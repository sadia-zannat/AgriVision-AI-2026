"""Runs the real local server + Chromium. Camera is MOCKED; no physical USB claim."""
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
SHOTS=ROOT/'docs/screenshots'
LEAF=ROOT/'tests/assets/QA_TEST_KSTATE_EARLY_BLIGHT_NOT_LIVE.jpg'
CHECKS=[]
def passed(name):
    CHECKS.append({'check':name,'passed':True});print('PASS',name,flush=True)

def main():
    SHOTS.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='agri_browser_qa_') as temp:
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        base=f'http://127.0.0.1:{port}'
        env=dict(os.environ,APP_DATA_DIR=temp,CHAT_PROVIDER_ORDER='offline',ALLOWED_HOSTS='localhost,127.0.0.1',PYTHONUNBUFFERED='1')
        log=open(ROOT.parent/'browser-server.log','w')
        server=subprocess.Popen([sys.executable,'-m','uvicorn','backend.app:app','--host','127.0.0.1','--port',str(port),'--no-access-log'],cwd=ROOT,env=env,stdout=log,stderr=log)
        try:
            with httpx.Client(trust_env=False) as client:
                for _ in range(120):
                    try:
                        if client.get(base+'/api/health',timeout=1).status_code==200:break
                    except Exception:time.sleep(.25)
                else:raise RuntimeError('Local server did not start')
            with sync_playwright() as p:
                executable=os.getenv('CHROMIUM_PATH') or shutil.which('chromium') or shutil.which('chrome')
                args={'headless':True,'args':['--no-sandbox']}
                if executable:args['executable_path']=executable
                browser=p.chromium.launch(**args)
                ctx=browser.new_context(viewport={'width':1366,'height':768},locale='en-US')
                page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base);expect(page.locator('#serverStatus')).to_have_text('YOLO ready',timeout=20000)
                page.locator('#langEn').click();page.screenshot(path=str(SHOTS/'01_dashboard_1366.png'),full_page=True)
                passed('Real server starts, two-stage profile loads and dashboard renders at 1366×768')
                page.locator('[data-source-tab="image"]').click();page.locator('#photoInput').set_input_files(str(LEAF));page.locator('#chatProvider').select_option('offline')
                expect(page.locator('#predictionLabel')).to_have_text('Possible Early Blight',timeout=15000)
                expect(page.locator('#detectionOverlay .leaf-box')).to_have_count(1)
                expect(page.locator('#detectionOverlay text')).to_contain_text('Early Blight')
                page.locator('#captureFrame').click();expect(page.locator('#explainCapture')).to_be_enabled(timeout=10000)
                page.locator('#explainCapture').click();page.locator('#langBn').click();page.locator('#question').fill('এই পাতাটি কি সুস্থ?');page.locator('#sendChat').click()
                expect(page.locator('.message.assistant')).to_have_count(1,timeout=20000)
                expect(page.locator('.message.user img')).to_be_visible();expect(page.locator('.source-disclosure')).to_have_count(1)
                assert not page.locator('.source-disclosure').evaluate('(n)=>n.open')
                assert 'Early Blight' in page.locator('.message.assistant').inner_text()
                page.locator('#toast').evaluate("n=>n.classList.add('hidden')");page.evaluate('()=>{window.scrollTo(0,0);document.getElementById("messages").scrollTop=0;}');page.screenshot(path=str(SHOTS/'02_photo_evidence_chat_1366.png'),full_page=True)
                assert page.locator('.annotated-chat-image').count()==1
                passed('Real YOLO detector box + preserved classifier → capture → Bengali offline guide, annotated chat image and sources')
                page.locator('#langEn').click();page.locator('#question').fill('What causes it?');page.locator('#sendChat').click()
                expect(page.locator('.message.user')).to_have_count(2,timeout=15000)
                expect(page.locator('.message.assistant').last).to_contain_text('Alternaria')
                expect(page.locator('.message.assistant').last.locator('.evidence-context')).to_be_visible()
                passed('Offline follow-up reuses explicitly submitted evidence and answers causes')

                page.locator('#newChat').click();page.locator('#langEn').click();page.locator('#question').fill('hi');page.locator('#sendChat').click()
                expect(page.locator('.message.user')).to_have_count(1,timeout=10000)
                assert 'Early Blight' not in page.locator('.message.assistant').last.inner_text()
                passed('Image-less greeting does not reuse a previous event')
                page.locator('#chatImageInput').set_input_files(str(LEAF));expect(page.locator('.attachment-chip img')).to_be_visible()
                page.locator('#question').fill('Is this leaf okay?')
                page.screenshot(path=str(SHOTS/'03_attachment_preview.png'),full_page=True)
                page.route('**/api/chat',lambda route:route.fulfill(status=503,content_type='application/json',body='{"detail":"QA simulated server failure"}'))
                page.locator('#sendChat').click();expect(page.locator('#composeError')).to_contain_text('QA simulated server failure',timeout=10000)
                expect(page.locator('.attachment-chip img')).to_be_visible();assert page.locator('#question').input_value()=='Is this leaf okay?'
                page.unroute('**/api/chat');page.locator('#sendChat').click();expect(page.locator('.message.user')).to_have_count(2,timeout=20000)
                assert page.locator('.message.user').last.locator('img').count()==1
                passed('Attachment preview, failed-send retention and successful image transmission/display')
                page.set_viewport_size({'width':1920,'height':1080});page.screenshot(path=str(SHOTS/'04_dashboard_1920.png'),full_page=True)
                for width,height in [(1366,768),(1920,1080),(390,844)]:
                    page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(150)
                    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1'),f'horizontal overflow at {width}'
                    if width>970:
                        page.evaluate('window.scrollTo(0,0)')
                        assert page.locator('#sendChat').bounding_box()['y']+page.locator('#sendChat').bounding_box()['height']<=height, 'composer clipped'
                        assert page.locator('#messages').bounding_box()['height']>120, 'conversation collapsed'

                page.locator('#toast').evaluate("n=>n.classList.add('hidden')");page.screenshot(path=str(SHOTS/'05_mobile_390.png'),full_page=True)
                passed('Responsive 1366 / 1920 / 390px layouts, visible desktop send button and scrollable message region')
                page.set_viewport_size({'width':1366,'height':768})
                page.locator('[data-source-tab="image"]').click();page.locator('#photoInput').set_input_files(str(LEAF));expect(page.locator('#predictionLabel')).to_have_text('Possible Early Blight',timeout=15000)
                page.locator('#explainCapture').click();expect(page.locator('#pendingEvidence')).to_be_visible(timeout=15000)
                import io
                from PIL import Image
                dark=io.BytesIO();Image.new('RGB',(300,300)).save(dark,format='PNG')
                page.locator('#photoInput').set_input_files({'name':'new_dark.png','mimeType':'image/png','buffer':dark.getvalue()})
                expect(page.locator('#predictionStatus')).to_have_text('LOW_QUALITY',timeout=15000)
                expect(page.locator('#pendingEvidence')).to_be_hidden();expect(page.locator('#detectionOverlay')).to_be_hidden()
                assert page.evaluate('state.lastEvent') is None
                passed('Opening a new photo clears old saved-event attachment and old boxes')
                page.locator('.nav-item[data-view="field"]').click();page.locator('#gpsSim').click();expect(page.locator('#fieldMode')).to_have_text('SIMULATED')
                page.evaluate("()=>{navigator.geolocation.getCurrentPosition=(ok,fail)=>fail({code:1});}")
                page.locator('#gpsBrowser').click();expect(page.locator('#fieldMode')).to_have_text('UNAVAILABLE')
                passed('Geolocation failure clears simulation and displays actual UNAVAILABLE state')

                ctx.close()
                # Full browser flow with real video tracks generated by a QA canvas, not physical hardware.
                mock=browser.new_context(viewport={'width':1366,'height':768})
                data=base64.b64encode(LEAF.read_bytes()).decode()
                mock.add_init_script('''
                window.__qaRequests=[];window.__qaStreams=[];window.__qaDark=false;
                const devices=new EventTarget();
                devices.enumerateDevices=async()=>[{kind:'videoinput',deviceId:'builtin-qa',label:'QA MOCK Integrated camera'},{kind:'videoinput',deviceId:'usb-qa',label:'QA MOCK External USB camera'}];
                devices.getUserMedia=async constraints=>{
                  const id=constraints.video.deviceId?.exact || 'builtin-qa';window.__qaRequests.push(id);
                  const c=document.createElement('canvas');c.width=572;c.height=518;const g=c.getContext('2d');const im=new Image();im.src='data:image/jpeg;base64,''' + data + '''';
                  const draw=()=>{g.fillStyle='#000';g.fillRect(0,0,572,518);if(!window.__qaDark&&im.complete)g.drawImage(im,0,0,572,518);};draw();const timer=setInterval(draw,40);
                  const stream=c.captureStream(24);const track=stream.getVideoTracks()[0];const original=track.getSettings.bind(track);track.getSettings=()=>({...original(),deviceId:id});
                  Object.defineProperty(track,'label',{value:id==='usb-qa'?'QA MOCK External USB camera':'QA MOCK Integrated camera'});
                  const stop=track.stop.bind(track);track.stop=()=>{clearInterval(timer);stop();};window.__qaStreams.push(stream);return stream;
                };
                Object.defineProperty(navigator,'mediaDevices',{value:devices});
                ''')
                page=mock.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base)
                page.locator('#enableCameras').click();expect(page.locator('#cameraSelect option')).to_have_count(3)
                assert page.evaluate('window.__qaStreams[0].getTracks()[0].readyState')=='ended'
                page.locator('#cameraSelect').select_option('usb-qa');page.locator('#startCamera').click();expect(page.locator('#deviceProof')).to_contain_text('QA MOCK External USB',timeout=15000)
                assert page.evaluate('window.__qaRequests.at(-1)')=='usb-qa'
                page.locator('#chatProvider').select_option('offline');expect(page.locator('#predictionStatus')).to_have_text('CHECK MODELS',timeout=15000)
                page.evaluate('window.__qaDark=true');expect(page.locator('#predictionStatus')).to_have_text('LOW_QUALITY',timeout=10000)
                assert 'Early Blight' not in page.locator('#predictionLabel').inner_text()
                page.evaluate('window.__qaDark=false');expect(page.locator('#predictionStatus')).to_have_text('CHECK MODELS',timeout=15000)
                passed('Mock permission probe releases default; exact USB selection; stable live inference clears old label on a dark frame')
                page.locator('#chatImageInput').set_input_files(str(LEAF));page.locator('#question').fill('Explain this photo');page.locator('#sendChat').click()
                expect(page.locator('.message.assistant')).to_have_count(1,timeout=20000)
                expect(page.locator('.message.assistant').last).to_contain_text('Early Blight')
                expect(page.locator('#predictionStatus')).to_have_text('CHECK MODELS',timeout=15000)
                passed('Chat photo during live camera succeeds locally; live inference resumes after answering')
                page.locator('#pauseCamera').click();expect(page.locator('#feedState')).to_have_text('PAUSED');assert page.locator('#captureFrame').is_disabled()
                page.locator('#pauseCamera').click();expect(page.locator('#feedState')).to_have_text('LIVE')
                page.locator('#recordCamera').click();expect(page.locator('#recordingIndicator')).to_be_visible();page.wait_for_timeout(2200);page.locator('#recordCamera').click()
                expect(page.locator('#recordingIndicator')).to_be_hidden(timeout=15000)
                page.wait_for_function('()=>state.recordingDraft===null && state.recorder===null',timeout=20000)
                with httpx.Client(trust_env=False) as client:
                    recs=client.get(base+'/api/recordings').json();assert recs
                    raw=client.get(base+recs[0]['url']).content;assert len(raw)>1000
                passed('Real MediaRecorder on mocked video track → validated WebM storage → playback/download route')
                page.locator('#stopCamera').click();expect(page.locator('#feedState')).to_have_text('STOPPED')
                assert page.evaluate('window.__qaStreams.at(-1).getTracks()[0].readyState')=='ended'
                page.locator('#cameraSelect').select_option('builtin-qa');page.locator('#startCamera').click();expect(page.locator('#deviceProof')).to_contain_text('Integrated camera')
                page.locator('#stopCamera').click();passed('Pause/resume, Stop track cleanup, second-device switch and restart')
                page.locator('[data-source-tab="video"]').click();page.locator('#videoInput').set_input_files({'name':'QA_MOCK_RECORDED_NOT_LIVE.webm','mimeType':'video/webm','buffer':raw})
                page.locator('#recordedVideo').evaluate('(v)=>v.play()');page.locator('#chatProvider').select_option('offline')
                expect(page.locator('#captureFrame')).to_be_enabled(timeout=10000);page.locator('#captureFrame').click();expect(page.locator('#explainCapture')).to_be_enabled(timeout=10000)
                with httpx.Client(trust_env=False) as client:assert client.get(base+'/api/events').json()[0]['source']=='RECORDED VIDEO'
                passed('Recorded-video playback/capture retains honest recorded origin')
                assert not errors,errors
                passed('No uncaught browser JavaScript errors')
                browser.close()
        finally:
            server.terminate()
            try:server.wait(timeout=8)
            except subprocess.TimeoutExpired:server.kill();server.wait()
            log.close()
    result={'executed_utc':datetime.now(timezone.utc).isoformat(),'environment':'Linux Chromium + real detector/classifier CPU YOLO; camera tracks MOCKED',
            'screenshots':'Real running application; leaf asset from supplied K-State L721 figure 2, not live field evidence',
            'checks':CHECKS,'physical_usb_tested':False,'cuda_tested':False,'cloud_provider_credentials_tested':False}
    (ROOT/'docs/qa-browser-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('ALL BROWSER CHECKS PASSED',flush=True)
if __name__=='__main__':main()
