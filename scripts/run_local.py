"""Single owned server; delayed browser open; no orphaned subprocesses or LAN bind."""
import sys
import socket
import threading
import webbrowser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def open_when_ready():
    import time
    import urllib.request
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(100):
        try:
            with opener.open('http://127.0.0.1:8000/api/health',timeout=1) as r:
                if r.status==200:webbrowser.open('http://localhost:8000');return
        except Exception:time.sleep(.5)

if __name__=='__main__':
    import uvicorn
    try:
        with socket.socket() as check:check.bind(('127.0.0.1',8000))
    except OSError:
        raise SystemExit('Port 8000 is occupied. Close the older AgriVision terminal (Ctrl+C), then run again.')
    threading.Thread(target=open_when_ready,daemon=True).start()
    uvicorn.run('backend.app:app',host='127.0.0.1',port=8000,workers=1,proxy_headers=False,log_level='info',access_log=False)
