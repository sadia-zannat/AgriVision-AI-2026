"""One local origin serves editable UI, inference, attachments and evidence APIs."""
import asyncio
import csv
import io
import json
import time
import uuid
import re
import os
import threading
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Literal
import cv2
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, field_validator
from .config import ROOT, DATA, MAX_IMAGE, MAX_RECORDING, MAX_RECORD_SECONDS, ALLOWED_HOSTS
from . import storage, providers, knowledge
from .vision import vision
from .uploads import read_limited, decode_image, store_attachment, room_for
from .telemetry import telemetry
from .chat import answer, CHAT_SLOT

FRAME_SLOT = threading.BoundedSemaphore(2)
START = time.monotonic()
SOURCE = Literal['USB CAMERA', 'BUILT-IN CAMERA', 'CAMERA (UNVERIFIED)', 'PHONE SCREEN VIA CAMERA', 'RECORDED VIDEO', 'UPLOADED IMAGE']

@asynccontextmanager
async def lifespan(app):
    storage.init()
    yield
    # No camera-owning backend processes; SQLite connections are context-managed.

app = FastAPI(title='AgriVision AI — Plant Doctor', version='2.0.0', lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

@app.middleware('http')
async def local_security(request: Request, call_next):
    try: length = int(request.headers.get('content-length', '0'))
    except ValueError: return Response('Invalid length', status_code=400)
    if length > MAX_RECORDING + 2*1024*1024: return Response('Request too large', status_code=413)
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if request.headers.get('x-agrivision-request') != '1': return Response('Missing local request header', status_code=403)
        origin = request.headers.get('origin')
        expected = f'{request.url.scheme}://{request.url.netloc}'
        if origin and origin != expected: return Response('Cross-origin request rejected', status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Permissions-Policy'] = 'camera=(self), microphone=(), geolocation=(self)'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; media-src 'self' blob:; connect-src 'self'; object-src 'none'; frame-src 'none'; base-uri 'none'; form-action 'self'"
    if request.url.path.startswith('/api/'): response.headers['Cache-Control'] = 'no-store'
    return response

@app.get('/api/health')
def health(): return {'ok': True, 'version': '2.0.0', 'model_ready': vision.model is not None, 'uptime_s': round(time.monotonic()-START, 1)}

@app.get('/api/status')
def status():
    import psutil
    process = psutil.Process()
    return {'app': 'AgriVision AI', 'vision': vision.state(), 'providers': providers.status(),
            'telemetry': telemetry.current(), 'max_record_seconds': MAX_RECORD_SECONDS,
            'resources': {'process_rss_mb': round(process.memory_info().rss/1024**2, 1),
                          'host_cpu_percent': psutil.cpu_percent(None), 'process_threads': process.num_threads(),
                          'gpu_measured': False}}

class ModelChoice(BaseModel):
    choice: Literal['hybrid', 'detector9', 'original', 'expanded']
@app.post('/api/model/select')
async def select_model(body: ModelChoice):
    try: return await asyncio.to_thread(vision.reload, body.choice)
    except (ValueError, RuntimeError) as exc: raise HTTPException(409, str(exc)[:160])

async def process_frame(file, crop, leaf_confirmed, roi):
    raw = await read_limited(file, MAX_IMAGE)
    frame, jpeg = await asyncio.to_thread(decode_image, raw)
    h, w = frame.shape[:2]
    region = {'x': 0, 'y': 0, 'width': w, 'height': h}
    if roi:
        # Center square, 65% of the shorter side. UI guide is aligned to object-fit: contain.
        side = int(min(h, w)*.65); x = (w-side)//2; y = (h-side)//2
        region = {'x': x, 'y': y, 'width': side, 'height': side}
        target = frame[y:y+side, x:x+side]
    else: target = frame
    result = await asyncio.to_thread(vision.predict, target, crop, leaf_confirmed)
    result['region'] = region
    # Convert crop-relative boxes to the full normalized photograph, once at the server boundary.
    for d in result.get('detections',[]):
        a,b,c,e=d['box']
        d['box']=[round((region['x']+a*region['width'])/w,6),round((region['y']+b*region['height'])/h,6),round((region['x']+c*region['width'])/w,6),round((region['y']+e*region['height'])/h,6)]
    result['image_size']={'width':w,'height':h}
    import hashlib
    result['input_sha256'] = hashlib.sha256(jpeg).hexdigest()
    return frame, jpeg, result

@app.post('/api/predict')
async def predict(file: UploadFile=File(...), crop: str=Form('tomato', max_length=40),
                  leaf_confirmed: bool=Form(False), roi: bool=Form(False), frame_id: str=Form('', max_length=80)):
    if not FRAME_SLOT.acquire(False): raise HTTPException(429, 'Frames dropped: server busy. Retry next interval.')
    try:
        _, _, result = await process_frame(file, crop, leaf_confirmed, roi)
        return {'prediction': result, 'frame_id': frame_id, 'processed_at': storage.utc()}
    finally: FRAME_SLOT.release()

def annotated_image(frame,prediction):
    if not prediction.get('detections'):return None
    rendered=vision.annotate(frame,prediction)
    ok,encoded=cv2.imencode('.jpg',rendered,[cv2.IMWRITE_JPEG_QUALITY,92])
    if not ok:return None
    data=encoded.tobytes();room_for(len(data));name=uuid.uuid4().hex+'.jpg'
    (DATA/'evidence'/name).write_bytes(data)
    return '/api/evidence/'+name

@app.get('/api/knowledge')
def knowledge_catalog():
    trained=set(vision.meta.get('classes',[]))
    return {'count':len(knowledge.CORPUS),'visual_classes':sorted(trained),'entries':[dict(id=d['id'],label=d['label'],en=d['en_fields'],bn=d['bn_fields'],source=d['source'],visually_trained=d['label'] in trained) for d in knowledge.CORPUS]}

@app.post('/api/providers/test/{name}')
async def provider_test(name: Literal['meta','gemini','groq','ollama']):
    return await asyncio.to_thread(providers.test_provider,name)

@app.post('/api/capture')
@app.post('/api/diagnose')
async def capture(file: UploadFile=File(...), source: SOURCE=Form('UPLOADED IMAGE'),
                  crop: str=Form('tomato', max_length=40), leaf_confirmed: bool=Form(False), roi: bool=Form(False),
                  device_label: str=Form('', max_length=180), device_id: str=Form('', max_length=240),
                  media_time_s: float=Form(0, ge=0, le=86400), captured_at: str=Form('', max_length=60)):
    if not FRAME_SLOT.acquire(False): raise HTTPException(429, 'Server busy; capture again shortly.')
    try:
        frame, jpeg, result = await process_frame(file, crop, leaf_confirmed, roi)
        if result['status'] == 'BUSY': raise HTTPException(409, 'Model busy; capture again shortly.')
        name = uuid.uuid4().hex + '.jpg'; room_for(len(jpeg))
        (DATA / 'evidence' / name).write_bytes(jpeg)
        gps = telemetry.current(source, media_time_s) if source != 'UPLOADED IMAGE' else {'mode': 'UNAVAILABLE', 'latitude': None, 'longitude': None, 'note': 'Uploaded photo has no verified geolocation.'}
        event = {'created_at': storage.utc(), 'client_captured_at': captured_at, 'source': source, 'crop': crop,
                 'crop_origin': 'user supplied', 'device_label': device_label or 'not supplied', 'device_id': device_id,
                 'media_time_s': media_time_s, 'prediction': result, 'telemetry': gps, 'image_file': name,
                 'image_url': '/api/evidence/' + name,'annotated_url':await asyncio.to_thread(annotated_image,frame,result)}
        return storage.save_event(event)
    finally: FRAME_SLOT.release()

@app.get('/api/events')
def events(limit: int=Query(100, ge=1, le=500)): return storage.events(limit)

@app.get('/api/events/{event_id}')
def event(event_id: int):
    e = storage.event(event_id)
    if e is None: raise HTTPException(404, 'Event not found')
    return e

@app.get('/api/evidence/{name}')
def evidence(name: str):
    if not re.fullmatch(r'[\w.-]+\.jpg', name) or Path(name).name != name: raise HTTPException(404)
    p = DATA / 'evidence' / name
    if not p.is_file(): raise HTTPException(404, 'Evidence image not found')
    return FileResponse(p, media_type='image/jpeg')

@app.get('/api/export/events.csv')
def export():
    stream = io.StringIO(); writer = csv.writer(stream)
    writer.writerow(['id','timestamp_utc','source','device_label','crop_user_supplied','class','score_not_severity','status','quality_reason','model_file','model_sha256','gps_mode','latitude','longitude','gps_origin','media_time_s','classifier_sha256','detections_normalized_xyxy_json'])
    def safe(v):
        s = '' if v is None else str(v)
        return "'"+s if s.startswith(('=','+','-','@','\t','\r')) else s
    for e in storage.events(500):
        p, g = e['prediction'], e['telemetry']; m = p.get('model',{})
        writer.writerow([safe(v) for v in [e['id'],e['created_at'],e['source'],e.get('device_label'),e.get('crop'),p.get('label'),p.get('score'),p['status'],p.get('reason'),m.get('filename'),m.get('sha256'),g['mode'],g.get('latitude'),g.get('longitude'),g.get('origin'),e.get('media_time_s'),m.get('classifier_sha256'),json.dumps(p.get('detections',[]),ensure_ascii=False)]])
    return Response('\ufeff'+stream.getvalue(), media_type='text/csv; charset=utf-8', headers={'Content-Disposition':'attachment; filename="agrivision_evidence.csv"'})

@app.post('/api/attachments')
async def upload(file: UploadFile=File(...)): return await store_attachment(file)

@app.get('/api/attachments/{aid}')
def get_attachment(aid: str):
    a = storage.attachment(aid)
    if not a: raise HTTPException(404, 'Attachment not found')
    p = DATA / 'uploads' / a['stored']
    if not p.is_file(): raise HTTPException(404)
    headers = {} if a['mime'].startswith('image/') else {'Content-Disposition': 'attachment; filename="document' + Path(a['stored']).suffix + '"'}
    return FileResponse(p, media_type=a['mime'], headers=headers)

class ChatBody(BaseModel):
    question: str=Field('', max_length=3000)
    language: Literal['bn','en']='bn'
    crop: str=Field('tomato', max_length=40)
    conversation_id: str=Field(default_factory=lambda: uuid.uuid4().hex, pattern=r'^[a-f0-9]{32}$')
    attachment_ids: list[str]=Field(default_factory=list, max_length=4)
    event_id: int | None=None
    leaf_confirmed: bool=False
    provider: Literal['auto','offline','meta','gemini','groq','ollama']='auto'
    @field_validator('attachment_ids')
    @classmethod
    def valid_ids(cls, values):
        if any(not re.fullmatch(r'[a-f0-9]{32}', v) for v in values): raise ValueError('Invalid attachment id')
        return values

@app.post('/api/chat')
async def chat(body: ChatBody):
    q = body.question.strip()
    if not q and not body.attachment_ids and not body.event_id: raise HTTPException(400, 'Type a question or attach evidence')
    if not CHAT_SLOT.acquire(False): raise HTTPException(429, 'Plant Doctor is busy; please send again shortly.')
    try:
        image = None; prediction = None; text = ''; attachments = []; e = None; annotated_url = None; evidence_context = None
        crop = body.crop.lower().strip()
        # Explicit crop words override a stale tomato selector. No visual crop guessing.
        for name, aliases in {'rice':['rice','ধান'], 'wheat':['wheat','গম'], 'potato':['potato','আলু'], 'maize':['maize','corn','ভুট্টা']}.items():
            if any(re.search(r'\b'+re.escape(w)+r'\b',q.lower()) if w.isascii() else w in q for w in aliases): crop = name; break
        if body.event_id and body.attachment_ids: raise HTTPException(422, 'Use a saved event OR new attachments so evidence stays unambiguous.')
        if body.event_id:
            e = storage.event(body.event_id)
            if not e: raise HTTPException(404, 'Saved event not found')
            p = DATA / 'evidence' / e['image_file']
            if not p.exists(): raise HTTPException(404, 'Saved evidence image missing')
            image, prediction = p.read_bytes(), e['prediction']
            annotated_url=e.get('annotated_url')
            evidence_context={'kind':'saved capture','event_id':e['id'],'created_at':e['created_at']}
            # An unsupported crop never inherits a supported tomato prediction.
            if crop != 'tomato': prediction = {'status': 'UNSUPPORTED_CROP', 'label': None, 'reason': 'Saved tomato evidence is not applicable to this crop.'}
        image_count = 0
        for aid in body.attachment_ids:
            a = storage.attachment(aid)
            if not a: raise HTTPException(404, 'Attachment expired or not found')
            attachments.append(storage.public_attachment(a))
            if a['mime'].startswith('image/'):
                image_count += 1
                if image_count > 1: raise HTTPException(422, 'Submit one leaf photo per question for clear model provenance.')
                image = (DATA / 'uploads' / a['stored']).read_bytes()
                frame, _ = decode_image(image)
                prediction = await asyncio.to_thread(vision.predict, frame, crop, body.leaf_confirmed, 5)
                annotated_url=await asyncio.to_thread(annotated_image,frame,prediction)
                evidence_context={'kind':'submitted photo','attachment_id':aid,'name':a['name']}
            else: text += '\n' + a['name'] + ':\n' + a['text_content']
        question = q or ('এই প্রমাণটি সতর্কভাবে ব্যাখ্যা করুন।' if body.language=='bn' else 'Cautiously explain this evidence.')
        history = storage.messages(body.conversation_id)
        # A question explicitly about the previous submitted result may reuse its evidence.
        # It never silently switches to a different monitor image or a different conversation.
        if prediction is None and not body.attachment_ids and not body.event_id and crop=='tomato' and history and knowledge.follow_up(question):
            last=history[-1]
            previous=last.get('prediction') if last.get('role')=='assistant' else None
            named=[d for d in knowledge.matched(question) if d['id']!='watering']
            previous_labels={previous.get('label')} if previous else set()
            previous_labels.update(d.get('label') for d in (previous or {}).get('detections',[]))
            if previous and (not named or any(d['label'] in previous_labels for d in named)):
                prediction=previous;annotated_url=last.get('annotated_url')
                evidence_context=dict(last.get('evidence_context') or {},follow_up=True)

        context = [{'role': m['role'], 'text': (m.get('question') or m.get('answer') or '')[:1800]} for m in history[-8:]]
        result = await asyncio.to_thread(answer, question, crop, body.language, prediction, image, text, context, body.provider)
        result.update(conversation_id=body.conversation_id, evidence_event_id=body.event_id, crop=crop,annotated_url=annotated_url,evidence_context=evidence_context)
        user = {'question': question, 'attachments': attachments,
                'event': {'id': e['id'], 'image_url': e['image_url'], 'created_at': e['created_at']} if e else None}
        storage.new_conversation(body.conversation_id, question)
        storage.save_messages(body.conversation_id, user, result)
        return {'user_message': user, 'assistant_message': result}
    finally: CHAT_SLOT.release()

@app.get('/api/conversations')
def conversations(): return storage.conversations()
@app.get('/api/conversations/{cid}')
def conversation(cid: str): return storage.messages(cid)

@app.get('/api/telemetry')
def gps(source: str='', time_s: float=Query(0, ge=0, le=86400)): return telemetry.current(source, time_s)
class GPSMode(BaseModel):
    mode: Literal['UNAVAILABLE','SIMULATED']
@app.post('/api/telemetry/mode')
def mode(body: GPSMode):
    if body.mode == 'SIMULATED': telemetry.simulate()
    else: telemetry.reset()
    return telemetry.current()
@app.post('/api/telemetry/csv')
async def gps_csv(file: UploadFile=File(...)):
    raw = await read_limited(file, 1024*1024)
    telemetry.load_csv(raw)
    return {'mode': 'RECORDED TELEMETRY', 'count': len(telemetry.points)}
class LivePoint(BaseModel):
    latitude: float=Field(ge=-90, le=90)
    longitude: float=Field(ge=-180, le=180)
    accuracy_m: float=Field(ge=0, le=100000)
    timestamp_utc: str
    origin: Literal['Browser device geolocation','External telemetry adapter']
    @field_validator('timestamp_utc')
    @classmethod
    def timestamp(cls,v):
        d=datetime.fromisoformat(v.replace('Z','+00:00'))
        if d.tzinfo is None: raise ValueError('Timestamp must include timezone')
        return v
@app.post('/api/telemetry/live')
def live(body: LivePoint):
    telemetry.set_live(body.model_dump()); return telemetry.current()

@app.post('/api/recordings')
async def recording(file: UploadFile=File(...), source: SOURCE=Form('CAMERA (UNVERIFIED)'),
                    device_label: str=Form('',max_length=180), duration_s: float=Form(0, ge=0, le=600)):
    rid=uuid.uuid4().hex
    prefix=await file.read(64)
    if prefix.startswith(b'\x1aE\xdf\xa3'): ext, mime='.webm','video/webm'
    elif len(prefix)>12 and prefix[4:8]==b'ftyp': ext,mime='.mp4','video/mp4'
    else: raise HTTPException(415, 'Recording must be valid WebM or MP4')
    name=rid+ext; path=DATA/'recordings'/name; total=len(prefix)
    room_for(MAX_RECORDING)
    try:
        with path.open('wb') as out:
            out.write(prefix)
            while chunk:=await file.read(1024*1024):
                total+=len(chunk)
                if total>MAX_RECORDING: raise HTTPException(413,'Recording exceeds 120 MB')
                out.write(chunk)
        cap=cv2.VideoCapture(str(path)); ok, frame=cap.read(); cap.release()
        if not ok: raise HTTPException(415,'Recording container is unreadable; keep your local download and try Chrome/Edge.')
        rec={'id':rid,'filename':name,'source':source,'device_label':device_label,'reported_duration_s':duration_s,
             'size_bytes':total,'created_at':storage.utc(),'mime':mime,'url':'/api/recordings/'+name,
             'width':int(frame.shape[1]),'height':int(frame.shape[0]), 'note':'Browser media recording; not proof of live aerial operation.'}
        storage.save_recording(rec); return rec
    except Exception:
        path.unlink(missing_ok=True); raise
@app.get('/api/recordings')
def recordings(): return storage.recordings()
@app.get('/api/recordings/{name}')
def playback(name: str):
    if not re.fullmatch(r'[a-f0-9]{32}\.(webm|mp4)',name): raise HTTPException(404)
    p=DATA/'recordings'/name
    if not p.exists(): raise HTTPException(404)
    return FileResponse(p,media_type='video/webm' if name.endswith('.webm') else 'video/mp4')

app.mount('/references', StaticFiles(directory=ROOT/'references'), name='references')
app.mount('/', StaticFiles(directory=ROOT/'frontend/static', html=True), name='dashboard')
