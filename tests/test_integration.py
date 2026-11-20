"""Integrated release regressions. Real models run on CPU unless explicitly mocked."""
import io,json,hashlib,uuid
from datetime import datetime,timezone,timedelta
import numpy as np,pytest
from PIL import Image
from backend.vision import vision
from backend import providers,chat as chatmod,storage,knowledge
from backend.config import MODEL_FILES
from backend.telemetry import telemetry
ORIGINAL='d3e816f6d02cd74f3d4b0fd6d756b8bcd93a7efefd9c41920f30a02af3bf3007'
DETECTOR='ccc05ab88bb550567fb7a7a07c564d37e344e7e69e094da54481ea47c0f134b3'
def png(frame):
 b=io.BytesIO();Image.fromarray(frame).save(b,format='PNG');return b.getvalue()
def predict(c,h,raw,**data):return c.post('/api/predict',headers=h,files={'file':('frame.jpg',raw)},data=data)
def upload(c,h,raw,name='leaf.jpg'):return c.post('/api/attachments',headers=h,files={'file':(name,raw)}).json()
def ask(c,h,**body):return c.post('/api/chat',headers=h,json=dict(language='en',provider='offline',**body)).json()['assistant_message']

def test_integrity_default_and_health(client):
 assert client.get('/api/health').json()['version']=='2.0.0'
 assert vision.selected=='hybrid' and vision.model.task=='detect' and vision.classifier.task=='classify'
 assert hashlib.sha256(MODEL_FILES['original'].read_bytes()).hexdigest()==ORIGINAL
 assert hashlib.sha256(MODEL_FILES['detector9'].read_bytes()).hexdigest()==DETECTOR
 assert len(vision.meta['classes'])==5 and len(vision.meta['raw_classes'])==9

@pytest.mark.parametrize('frame',[np.zeros((224,224,3),np.uint8),np.full((224,224,3),255,np.uint8),np.full((224,224,3),120,np.uint8)])
def test_bad_image_never_retains_label_or_box(client,headers,frame):
 p=predict(client,headers,png(frame)).json()['prediction']
 assert p['status']=='LOW_QUALITY' and p['label'] is None and p['score'] is None and not p['detections']

def test_real_prediction_without_confirmation_checkbox(client,headers,leaf):
 p=predict(client,headers,leaf,leaf_confirmed='false').json()['prediction']
 assert p['status']=='REVIEW' and p['label']=='Early Blight' and p['score']>.9
 assert p['model']['classifier_sha256']==ORIGINAL
 d=p['detections'][0];x,y,r,b=d['box']
 assert 0<=x<r<=1 and 0<=y<b<=1 and d['models_disagree']
 assert d['detector_label']=='Tomato Yellow Virus'  # Known secondary model error stays visible.
 assert p['image_size']=={'width':286,'height':259}

def test_no_detection_is_not_healthy(client,headers,leaf,monkeypatch):
 class M:
  def predict(self,*a,**k):return [type('Result',(),{'boxes':[]})()]
 monkeypatch.setattr(vision,'model',M());p=predict(client,headers,leaf).json()['prediction']
 assert p['status']=='NO_DETECTION' and p['label'] is None and not p['detections']

def test_roi_boxes_map_back_to_full_frame(client,headers,leaf,monkeypatch):
 def synthetic(frame,*a):return {'status':'OK','label':'Early Blight','score':.8,'detections':[{'box':[0,0,1,1]}]}
 monkeypatch.setattr(vision,'predict',synthetic);p=predict(client,headers,leaf,roi='true').json()['prediction'];r=p['region']
 assert p['detections'][0]['box']==pytest.approx([r['x']/286,r['y']/259,(r['x']+r['width'])/286,(r['y']+r['height'])/259],abs=1e-6)
 assert p['image_size']=={'width':286,'height':259}

def test_untrained_crop_is_explicit(client,headers,leaf):
 p=predict(client,headers,leaf,crop='rice').json()['prediction'];assert p['status']=='UNSUPPORTED_CROP' and not p['detections']
 a=upload(client,headers,leaf);p=ask(client,headers,question='This is a rice leaf',attachment_ids=[a['id']]);assert 'No trained' in p['answer']

def test_missing_model_and_backpressure(client,headers,leaf,monkeypatch):
 with monkeypatch.context() as patch:
  patch.setattr(vision,'model',None);assert predict(client,headers,leaf).json()['prediction']['status']=='MODEL_UNAVAILABLE'
 vision.lock.acquire()
 try:assert predict(client,headers,leaf).json()['prediction']['status']=='BUSY'
 finally:vision.lock.release()

def test_profiles_have_distinct_outputs(client,headers,leaf):
 try:
  assert client.post('/api/model/select',headers=headers,json={'choice':'original'}).status_code==200
  p=predict(client,headers,leaf).json()['prediction'];assert p['label']=='Early Blight' and p['model']['sha256']==ORIGINAL and p['detections']==[]
  assert client.post('/api/model/select',headers=headers,json={'choice':'detector9'}).status_code==200
  p=predict(client,headers,leaf).json()['prediction'];assert p['label']=='Tomato Yellow Virus' and len(p['model']['classes'])==9 and p['detections']
 finally:vision.reload('hybrid')

def test_raw_and_annotated_capture_persist_separately(client,headers,leaf):
 telemetry.reset();e=client.post('/api/capture',headers=headers,files={'file':('leaf.jpg',leaf)},data={'source':'USB CAMERA','device_label':'QA MOCK USB, not hardware'}).json()
 assert e['prediction']['label']=='Early Blight' and e['telemetry']['mode']=='UNAVAILABLE'
 raw=client.get(e['image_url']).content;annotated=client.get(e['annotated_url']).content
 assert raw!=annotated and Image.open(io.BytesIO(raw)).size==Image.open(io.BytesIO(annotated)).size
 assert hashlib.sha256(raw).hexdigest()==e['prediction']['input_sha256']
 assert client.get('/api/events/'+str(e['id'])).json()['prediction']==e['prediction']
 csv=client.get('/api/export/events.csv').text;assert 'detections_normalized_xyxy_json' in csv and ORIGINAL in csv
 dark=client.post('/api/capture',headers=headers,files={'file':('dark.png',png(np.zeros((224,224,3),np.uint8)))}).json()
 assert dark['prediction']['label'] is None and dark['annotated_url'] is None

def test_photo_offline_and_followup_context(client,headers,leaf):
 a=upload(client,headers,leaf);cid=uuid.uuid4().hex
 first=ask(client,headers,question='Is this leaf okay?',conversation_id=cid,attachment_ids=[a['id']])
 assert first['provider']=='offline' and first['local_vision'] and not first['image_understanding']
 assert first['prediction']['label']=='Early Blight' and 'Cause:' in first['answer'] and 'Symptoms:' in first['answer'] and first['annotated_url']
 follow=ask(client,headers,question='What causes it?',conversation_id=cid)
 assert follow['evidence_context']['follow_up'] and follow['prediction']==first['prediction'] and 'Alternaria' in follow['answer'] and 'Symptoms:' not in follow['answer']
 other=ask(client,headers,question='What causes Septoria?',conversation_id=cid);assert other['prediction'] is None and 'Septoria' in other['answer']
 greeting=ask(client,headers,question='hi',conversation_id=cid);assert greeting['prediction'] is None and not greeting['sources'] and 'Hello' in greeting['answer']
 new=ask(client,headers,question='What causes it?',conversation_id=uuid.uuid4().hex);assert new['prediction'] is None

def test_new_photo_replaces_old_disease_context(client,headers,leaf):
 cid=uuid.uuid4().hex;a=upload(client,headers,leaf);ask(client,headers,question='Explain',conversation_id=cid,attachment_ids=[a['id']])
 dark=upload(client,headers,png(np.zeros((224,224,3),np.uint8)),'dark.png')
 r=ask(client,headers,question='Explain this photo',conversation_id=cid,attachment_ids=[dark['id']])
 assert r['prediction']['status']=='LOW_QUALITY' and 'Early Blight' not in r['answer'] and not r['sources']

@pytest.mark.parametrize('lang,needle',[('en','Care:'),('bn','করণীয়:')])
def test_bilingual_guide(client,headers,lang,needle):
 r=client.post('/api/chat',headers=headers,json={'question':'Early Blight protikar','language':lang,'provider':'offline'}).json()['assistant_message']
 assert needle in r['answer'] and r['sources'][0]['id']=='early' and r['prediction'] is None

@pytest.mark.parametrize('d',knowledge.CORPUS,ids=lambda d:d['id'])
def test_each_curated_condition_has_answers_and_sources(d):
 docs=knowledge.retrieve(d['label']);assert docs and docs[0]['id']==d['id']
 assert set(d['en_fields'])==set(d['bn_fields'])=={'cause','symptoms','action','prevention'}
 assert d['source']['url'].startswith('https://')
 for lang in ('en','bn'):
  text=knowledge.offline(d['label'],lang,'tomato',None,docs,False,'');assert d['label'] in text and '[1]' in text

def test_knowledge_does_not_claim_visual_training(client):
 c=client.get('/api/knowledge').json();assert c['count']>=25
 for label in ('Magnesium Deficiency','Target Spot'):
  assert not next(d for d in c['entries'] if d['label']==label)['visually_trained']

def test_pdf_and_text_previews(client,headers):
 import fitz
 d=fitz.open();p=d.new_page();p.insert_text((30,50),'Observation: lower leaves show spots.');raw=d.tobytes();d.close()
 a=upload(client,headers,raw,'notes.pdf');r=ask(client,headers,question='Summarize this document',attachment_ids=[a['id']])
 assert 'lower leaves' in a['preview'] and r['prediction'] is None and 'does not verify' in r['answer']
 assert 'পাতায়' in upload(client,headers,'পাতায় দাগ আছে'.encode(),'notes.txt')['preview']

@pytest.mark.parametrize('name,data',[('payload.jpg',b'<script>alert(1)</script>'),('binary.txt',b'abc\x00def'),('fake.pdf',b'not a PDF'),('run.exe',b'MZfoo')])
def test_bad_upload_types(client,headers,name,data):assert client.post('/api/attachments',headers=headers,files={'file':(name,data)}).status_code==415

def test_limits_and_ambiguous_evidence(client,headers):
 assert client.post('/api/attachments',headers=headers,files={'file':('large.jpg',b'x'*(10*1024*1024+1))}).status_code==413
 assert client.post('/api/chat',headers=headers,json={'event_id':999999}).status_code==404
 assert client.post('/api/chat',headers=headers,json={'question':'hi','event_id':1,'attachment_ids':['a'*32]}).status_code==422

def test_provider_wire_contracts_no_model_list_gate(monkeypatch):
 import httpx
 real_client=httpx.Client;seen=[];providers.CAPS.clear()
 def handle(req):
  seen.append((str(req.url),json.loads(req.content) if req.content else None))
  if req.url.path.endswith('chat/completions'):return httpx.Response(200,json={'choices':[{'message':{'content':'Grounded reply [1]'},'finish_reason':'stop'}]})
  if req.url.path.endswith(':generateContent'):return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':'Grounded reply [1]'}]}}]})
  if req.url.path=='/api/show':return httpx.Response(200,json={'capabilities':['completion']})
  if req.url.path=='/api/chat':return httpx.Response(200,json={'message':{'content':'Grounded text-only reply [1]'}})
  raise AssertionError(req.url.path)
 monkeypatch.setattr(providers.httpx,'Client',lambda **kw:real_client(transport=httpx.MockTransport(handle),**kw))
 for name in ('meta','gemini','groq','ollama'):
  out,image,_=providers.generate(name,'system','prompt',b'fake_jpeg_bytes');assert out and image==(name!='ollama')
 assert not any(u.endswith('/models') for u,_ in seen)
 meta=next(b for u,b in seen if u.startswith(providers.META_BASE));assert 'max_completion_tokens' in meta and 'image_url' in json.dumps(meta)
 assert 'inline_data' in json.dumps(next(b for u,b in seen if ':generateContent' in u))
 assert 'images' not in next(b for u,b in seen if u.endswith('/api/chat'))['messages'][-1]

@pytest.mark.parametrize('code,reason',[(400,'format'),(401,'credentials'),(403,'access'),(404,'unavailable'),(429,'quota'),(500,'service')])
def test_safe_api_errors(code,reason):
 import httpx
 with pytest.raises(RuntimeError,match=reason):providers.check_response(httpx.Response(code,json={'error':'SECRET DO NOT ECHO'}))

def test_fallback_and_explicit_offline(monkeypatch):
 monkeypatch.setenv('MODEL_API_KEY','unit-test-not-real');monkeypatch.setenv('GEMINI_API_KEY','unit-test-not-real');monkeypatch.setenv('CHAT_PROVIDER_ORDER','meta,gemini,offline')
 providers.SKIP_UNTIL.clear();calls=[]
 def fake(name,*a,**kw):
  calls.append(name)
  if name=='meta':raise RuntimeError('quota/rate limit (HTTP 429)')
  return 'Water near the roots. [1]',False,'mock'
 monkeypatch.setattr(providers,'generate',fake);r=chatmod.answer('How should I water tomatoes?','tomato','en')
 assert calls==['meta','gemini'] and r['provider']=='gemini' and r['attempts'][0]['status'].startswith('quota')
 calls.clear();r=chatmod.answer('Early Blight care','tomato','en',provider='offline');assert not calls and r['provider']=='offline'
 providers.SKIP_UNTIL.clear();monkeypatch.setattr(providers,'generate',lambda *a,**k:('A grounded response without numeric brackets.',False,'mock'))
 assert chatmod.answer('Early Blight care','tomato','en')['provider']=='meta'

def test_connection_test_sanitizes_and_reads_local_env(client,headers,monkeypatch,tmp_path):
 monkeypatch.setattr(providers,'ROOT',tmp_path);(tmp_path/'.env').write_text('MODEL_API_KEY=local-placeholder\nMETA_MODEL=muse-spark-1.3\n')
 assert providers.configured()['meta'];monkeypatch.setattr(providers,'generate',lambda *a,**k:('Connection OK',False,'mock'))
 r=client.post('/api/providers/test/meta',headers=headers,json={}).json();assert r['ok']
 assert 'local-placeholder' not in json.dumps(r) and 'local-placeholder' not in client.get('/api/status').text
 (tmp_path/'.env').write_text('MODEL_API_KEY=\nMETA_API_KEY=\n');assert not providers.configured()['meta']

def test_gps_provenance_freshness_and_binding(client,headers):
 telemetry.reset();assert client.get('/api/telemetry').json()['mode']=='UNAVAILABLE'
 client.post('/api/telemetry/mode',headers=headers,json={'mode':'SIMULATED'});assert client.get('/api/telemetry').json()['mode']=='SIMULATED'
 raw=b'time_s,latitude,longitude\n0,23.8,90.3\n10,23.81,90.31\n'
 assert client.post('/api/telemetry/csv',headers=headers,files={'file':('track.csv',raw)}).status_code==200
 assert client.get('/api/telemetry',params={'source':'RECORDED VIDEO','time_s':10}).json()['mode']=='RECORDED TELEMETRY'
 assert client.get('/api/telemetry',params={'source':'USB CAMERA'}).json()['mode']=='UNAVAILABLE'
 old=(datetime.now(timezone.utc)-timedelta(minutes=5)).isoformat()
 client.post('/api/telemetry/live',headers=headers,json={'latitude':23,'longitude':90,'accuracy_m':30,'timestamp_utc':old,'origin':'Browser device geolocation'})
 assert client.get('/api/telemetry').json()['mode']=='UNAVAILABLE';telemetry.reset()

def test_security_and_missing_optional_weights(client,headers):
 assert client.post('/api/chat',json={'question':'hi'}).status_code==403
 assert client.post('/api/chat',headers=dict(headers,Origin='https://evil.example'),json={'question':'hi'}).status_code==403
 assert client.get('/api/health',headers={'Host':'evil.example'}).status_code==400
 assert client.post('/api/model/select',headers=headers,json={'choice':'expanded'}).status_code==409
 assert vision.selected=='hybrid' and client.get('/.env').status_code==404 and client.get('/models/tomato_best.pt').status_code==404
 assert 'script-src' in client.get('/').headers['Content-Security-Policy']
 assert client.post('/api/recordings',headers=headers,files={'file':('bad.webm',b'not video')}).status_code==415

def test_legacy_database_migration(tmp_path,monkeypatch):
 import sqlite3
 old=tmp_path/'legacy.db'
 with sqlite3.connect(old) as db:
  db.execute("CREATE TABLE events(id INTEGER PRIMARY KEY,created_at TEXT,source TEXT,predicted_label TEXT,score REAL,model_name TEXT,verdict TEXT,image_file TEXT,gps_mode TEXT,latitude REAL,longitude REAL,notes TEXT)")
  db.execute("INSERT INTO events VALUES(1,'2026-11-12T00:00:00Z','LEGACY','Early Blight',0.8,'tomato','REVIEW','old.jpg','UNAVAILABLE',NULL,NULL,'keep this')")
 monkeypatch.setattr(storage,'DB',old);storage.init();assert storage.event(1)['prediction']['label']=='Early Blight'
 with sqlite3.connect(old) as db:assert db.execute('SELECT notes FROM events WHERE id=1').fetchone()[0]=='keep this'

def test_uncertain_classifier_keeps_geometry_without_disease_label(client,headers,leaf,monkeypatch):
 import torch
 names=vision.classifier.names
 class Uncertain:
  def predict(self,*a,**k):return [type('Result',(),{'names':names,'probs':type('P',(),{'data':torch.tensor([.22,.21,.20,.19,.18])})()})()]
 monkeypatch.setattr(vision,'classifier',Uncertain())
 p=predict(client,headers,leaf).json()['prediction']
 assert p['status']=='LOW_CONFIDENCE' and p['label'] is None and p['detections'][0]['label']=='Uncertain condition'

def test_chat_photo_waits_for_short_live_inference_lock(client,headers,leaf):
 import threading
 a=upload(client,headers,leaf);vision.lock.acquire();release=threading.Timer(.15,vision.lock.release);release.start()
 try:
  r=ask(client,headers,question='Explain this leaf',attachment_ids=[a['id']]);assert r['prediction']['label']=='Early Blight' and r['prediction']['status']!='BUSY'
 finally:release.join()
