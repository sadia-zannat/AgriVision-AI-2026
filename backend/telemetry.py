"""Explicit origin, freshness and source binding. No automatic leaf geolocation."""
import csv
import io
import threading
from datetime import datetime, timezone
from fastapi import HTTPException

NOTE = 'Device/drone position is not the leaf/plot coordinate without geocalibration.'
class Telemetry:
    def __init__(self):
        self.lock = threading.Lock(); self.mode = 'UNAVAILABLE'; self.points = []; self.live = None
    def reset(self):
        with self.lock: self.mode = 'UNAVAILABLE'; self.points = []; self.live = None
    def simulate(self):
        with self.lock:
            self.mode = 'SIMULATED'; self.points = [dict(time_s=i*5, latitude=23.876+i*.00008, longitude=90.321+i*.00006) for i in range(6)]
    def load_csv(self, raw):
        try:
            rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
            if not rows or len(rows) > 10000: raise ValueError()
            points = []
            for row in rows:
                t, lat, lon = float(row['time_s']), float(row['latitude']), float(row['longitude'])
                if not 0 <= t <= 86400 or not -90 <= lat <= 90 or not -180 <= lon <= 180: raise ValueError()
                points.append(dict(time_s=t, latitude=lat, longitude=lon))
            points.sort(key=lambda p: p['time_s'])
        except Exception: raise HTTPException(422, 'CSV needs time_s,latitude,longitude with valid numeric values (max 10,000 points).')
        with self.lock: self.mode = 'RECORDED TELEMETRY'; self.points = points; self.live = None
    def set_live(self, point):
        with self.lock: self.mode = 'LIVE TELEMETRY'; self.live = point; self.points = []
    def current(self, source=None, t=0):
        with self.lock:
            empty = {'mode': 'UNAVAILABLE', 'latitude': None, 'longitude': None, 'note': NOTE}
            if self.mode == 'UNAVAILABLE': return empty
            if self.mode == 'SIMULATED':
                p = self.points[min(int(max(0,t)//5),len(self.points)-1)]
                return dict(p, mode='SIMULATED', origin='Explicit demonstration track', note=NOTE)
            if self.mode == 'RECORDED TELEMETRY':
                if source != 'RECORDED VIDEO': return dict(empty, reason='Recorded track is bound to recorded video only.')
                closest = min(self.points, key=lambda p: abs(p['time_s'] - t))
                if abs(closest['time_s'] - t) > 5: return dict(empty, reason='No recorded telemetry within 5 seconds of this video frame.')
                return dict(closest, mode=self.mode, origin='User-supplied CSV; accuracy not verified', note=NOTE)
            if self.live:
                age = (datetime.now(timezone.utc) - datetime.fromisoformat(self.live['timestamp_utc'].replace('Z','+00:00'))).total_seconds()
                if age > 30 or age < -5: return dict(empty, reason='Live telemetry stale or clock invalid.')
                if source in ('UPLOADED IMAGE','RECORDED VIDEO'): return dict(empty, reason='Live position is not attached to unrelated media.')
                return dict(self.live, mode='LIVE TELEMETRY', note=NOTE)
            return empty
telemetry = Telemetry()
