"""SQLite persistence with additive migration; legacy user rows are preserved."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from .config import DB

def utc(): return datetime.now(timezone.utc).isoformat()

@contextmanager
def connect():
    db = sqlite3.connect(DB, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, source TEXT NOT NULL,
            predicted_label TEXT, score REAL, model_name TEXT, verdict TEXT NOT NULL,
            image_file TEXT NOT NULL, gps_mode TEXT NOT NULL DEFAULT 'UNAVAILABLE',
            latitude REAL, longitude REAL, notes TEXT NOT NULL DEFAULT '', payload TEXT NOT NULL DEFAULT '{}');
        CREATE TABLE IF NOT EXISTS attachments (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL,
            stored TEXT NOT NULL, text_content TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY, created_at TEXT NOT NULL, title TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT NOT NULL,
            role TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS recordings_v2 (
            id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL);
        ''')
        columns = {r['name'] for r in db.execute('PRAGMA table_info(events)')}
        if 'payload' not in columns: db.execute("ALTER TABLE events ADD COLUMN payload TEXT NOT NULL DEFAULT '{}'")

def save_event(event):
    pred = event['prediction']; gps = event['telemetry']
    with connect() as db:
        cur = db.execute('''INSERT INTO events
        (created_at,source,predicted_label,score,model_name,verdict,image_file,gps_mode,latitude,longitude,notes,payload)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''',
        (event['created_at'], event['source'], pred.get('label'), pred.get('score'), pred.get('model', {}).get('filename'),
         pred['status'], event['image_file'], gps['mode'], gps.get('latitude'), gps.get('longitude'), '', json.dumps(event, ensure_ascii=False)))
        event['id'] = cur.lastrowid
    return event

def decode_event(row):
    r = dict(row); payload = json.loads(r.get('payload') or '{}')
    if payload: return dict(payload, id=r['id'])
    return {'id': r['id'], 'created_at': r['created_at'], 'source': r['source'], 'image_file': r['image_file'],
            'image_url': '/api/evidence/' + r['image_file'], 'device_label': 'legacy / not recorded',
            'prediction': {'status': r['verdict'], 'label': r['predicted_label'], 'score': r['score'],
                           'reason': 'Imported legacy event: quality/provenance were not recorded.', 'model': {'filename': r['model_name']}},
            'telemetry': {'mode': r['gps_mode'], 'latitude': r['latitude'], 'longitude': r['longitude']}, 'legacy': True}

def events(limit=100):
    with connect() as db: return [decode_event(r) for r in db.execute('SELECT * FROM events ORDER BY id DESC LIMIT ?', (max(1, min(limit, 500)),))]

def event(event_id):
    with connect() as db: r = db.execute('SELECT * FROM events WHERE id=?', (event_id,)).fetchone()
    return decode_event(r) if r else None

def save_attachment(a, stored, text):
    with connect() as db:
        db.execute('INSERT INTO attachments VALUES(?,?,?,?,?,?,?)', (a['id'], a['name'], a['mime'], a['size'], stored, text, utc()))

def attachment(aid):
    with connect() as db: r = db.execute('SELECT * FROM attachments WHERE id=?', (aid,)).fetchone()
    return dict(r) if r else None

def public_attachment(a):
    return {k: a[k] for k in ('id', 'name', 'mime', 'size')} | {'url': '/api/attachments/' + a['id'], 'preview': a.get('text_content', '')[:2400]}

def new_conversation(cid, title):
    with connect() as db: db.execute('INSERT OR IGNORE INTO conversations VALUES(?,?,?)', (cid, utc(), title[:70]))

def save_messages(cid, user, assistant):
    with connect() as db:
        db.executemany('INSERT INTO messages(conversation_id,role,payload,created_at) VALUES(?,?,?,?)',
                       [(cid, role, json.dumps(p, ensure_ascii=False), utc()) for role, p in [('user', user), ('assistant', assistant)]])

def messages(cid):
    with connect() as db:
        return [dict(json.loads(r['payload']), role=r['role'], created_at=r['created_at']) for r in
                reversed(db.execute('SELECT * FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT 300', (cid,)).fetchall())]

def conversations():
    with connect() as db: return [dict(r) for r in db.execute('SELECT * FROM conversations ORDER BY created_at DESC LIMIT 60')]

def save_recording(rec):
    with connect() as db: db.execute('INSERT INTO recordings_v2 VALUES(?,?,?)', (rec['id'], json.dumps(rec), utc()))

def recordings():
    with connect() as db: return [json.loads(r['payload']) for r in db.execute('SELECT * FROM recordings_v2 ORDER BY created_at DESC LIMIT 60')]
