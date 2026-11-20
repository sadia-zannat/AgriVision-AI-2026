/* AgriVision AI. No frontend framework, CDN, telemetry or browser-side secrets. */
'use strict';
const $ = id => document.getElementById(id);
const Core = window.AgriCore;
const state = {
  tab: 'camera', language: localStorage.getItem('agri.language') || 'bn', view: 'monitor', device: null,
  events: [], pending: [], evidence: null, conversation: crypto.randomUUID().replaceAll('-', ''),
  currentPrediction: null, pendingPhotoInference: false, inferenceToken: 0, inFlight: null, inferenceTimer: null, stable: new Core.Stabilizer(3),
  recorder: null, recordingStart: 0, recordTimer: null, recordStop: null, recordingDraft: null,
  mediaURLs: {}, capturing: false, lastEvent: null, status: null, sending: false, lastInference: 0, telemetryTimer: null
};
const camera = new window.CameraController($('cameraVideo'), navigator.mediaDevices, () => {
  invalidate(); showCameraEmpty(); controls(); notice('Camera disconnected. Reconnect and select the named USB device.', true);
});
function el(tag, cls, text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined) n.textContent = text; return n; }
function icon(id) { const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); const u = document.createElementNS(s.namespaceURI, 'use'); u.setAttribute('href', '#i-' + id); s.append(u); return s; }
function show(node, visible) { node.classList.toggle('hidden', !visible); }
function txt(bn, en) { return state.language === 'bn' ? bn : en; }
let toastTimer;
function toast(message) { $('toast').textContent = message; show($('toast'), true); clearTimeout(toastTimer); toastTimer = setTimeout(() => show($('toast'), false), 5500); }
function notice(message, error = false) { $('cameraNotice').textContent = message; $('cameraNotice').classList.toggle('error', error); }
async function api(url, options = {}, timeout = 20000) {
  const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), timeout);
  const headers = {'X-AgriVision-Request': '1', ...(options.headers || {})};
  try {
    const res = await fetch(url, {...options, headers, signal: controller.signal});
    if (!res.ok) {
      const raw = await res.text(); let message = raw.slice(0, 180);
      try { const j = JSON.parse(raw); message = typeof j.detail === 'string' ? j.detail : 'The request could not be validated.'; } catch { /* plain HTTP error */ }
      throw Object.assign(new Error(message || `HTTP ${res.status}`), {status: res.status});
    }
    return await res.json();
  } catch (err) { if (err.name === 'AbortError') throw new Error('Request timed out. Your unsent attachments are still here.'); throw err; }
  finally { clearTimeout(timer); }
}
function postJSON(url, body, timeout) { return api(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)}, timeout); }
function language(lang) {
  state.language = lang; localStorage.setItem('agri.language', lang); document.documentElement.lang = lang;
  document.querySelectorAll('[data-en][data-bn]').forEach(n => { n.textContent = n.dataset[lang]; });
  $('langBn').classList.toggle('active', lang === 'bn'); $('langEn').classList.toggle('active', lang === 'en');
  $('langBn').setAttribute('aria-pressed', String(lang === 'bn')); $('langEn').setAttribute('aria-pressed', String(lang === 'en'));
  feedTitle();
  $('question').placeholder = txt('পাতার সমস্যা বা আপনার প্রশ্ন লিখুন…', 'Describe the leaf or ask your question…');
}
function view(name) {
  state.view = name; document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.view === name));
  document.querySelectorAll('.view').forEach(n => show(n, n.id === 'view-' + name));
  $('mainContent').classList.toggle('chat-focus', name === 'chat');
  if (name === 'history') { renderHistory(); loadRecordings(); }
  if (name === 'reports') renderReports();
  if (name === 'settings') refreshStatus();
  requestAnimationFrame(updateROI);
}
function feedTitle() { const n=$('feedTitle').querySelector('span');n.dataset.en=state.tab==='image'?'Photo screening':state.tab==='video'?'Recorded Video':'Live Camera Feed';n.dataset.bn=state.tab==='image'?'ছবির স্ক্রিনিং':state.tab==='video'?'রেকর্ড করা ভিডিও':'লাইভ ক্যামেরা';n.textContent=n.dataset[state.language]; }
function source() { return state.tab === 'video' ? 'RECORDED VIDEO' : state.tab === 'image' ? 'UPLOADED IMAGE' : $('sourceDeclaration').value; }
function media() { return state.tab === 'video' ? $('recordedVideo') : state.tab === 'image' ? $('photoPreview') : $('cameraVideo'); }
function frameReady() {
  if (state.tab === 'camera') return Boolean(camera.stream && !camera.paused && $('cameraVideo').videoWidth);
  if (state.tab === 'video') return $('recordedVideo').readyState >= 2;
  return $('photoPreview').complete && Boolean($('photoPreview').naturalWidth);
}
function controls() {
  const live = Boolean(camera.stream); const cam = state.tab === 'camera';
  $('startCamera').disabled = !cam || !$('cameraSelect').value || live;
  $('pauseCamera').disabled = !cam || !live;
  $('pauseCamera').replaceChildren(document.createTextNode(camera.paused ? '▶ ' : 'Ⅱ '), el('span', '', camera.paused ? txt('আবার চালু','Resume') : txt('বিরতি','Pause')));
  $('stopCamera').disabled = !cam || !live;
  $('captureFrame').disabled = !frameReady() || state.capturing;
  $('explainCapture').disabled = !frameReady() || state.capturing;
  $('recordCamera').disabled = !cam || !live || camera.paused || Boolean(state.recordingDraft);
  $('recordCamera').classList.toggle('primary', Boolean(state.recorder));
  $('recordCamera').replaceChildren(el('span','rec-dot'), document.createTextNode(state.recorder ? txt('রেকর্ড থামান','Stop recording') : txt('রেকর্ড','Record')));
  $('cameraSelect').disabled = Boolean(state.recorder);
}
function statusBadge(node, text, type = 'neutral') { node.textContent = text; node.className = 'badge ' + type; }
function clearPrediction(reason = 'No current frame is being analyzed.', badge = 'WAITING') {
  state.currentPrediction=null;drawDetections(null);$('detectionList').replaceChildren();state.stable.reset(); statusBadge($('predictionStatus'), badge); $('predictionLabel').textContent = txt('নতুন frame-এর অপেক্ষায়','Waiting for a current frame');
  $('predictionReason').textContent = reason; $('predictionScore').textContent = '—'; $('predictionLatency').textContent = '—';
  $('qualityInfo').textContent = 'No current model evidence'; $('stableCount').textContent = 'No current evidence';
}
function invalidate(reason, badge) {
  state.inferenceToken++; clearTimeout(state.inferenceTimer); state.inferenceTimer = null; state.lastInference = 0;
  $('inferenceRate').textContent = 'Inference — /s'; clearPrediction(reason, badge);
}
function showCameraEmpty() { show($('cameraVideo'), false); show($('feedEmpty'), true); statusBadge($('feedState'), 'STOPPED'); $('deviceProof').textContent = 'No active camera'; }
async function cameras(grant = false) {
  try {
    const devices = await camera.enumerate(grant); const current = $('cameraSelect').value || localStorage.getItem('agri.camera');
    $('cameraSelect').replaceChildren(new Option(txt('নাম দেখে ক্যামেরা বাছুন…','Choose a named camera…'), ''));
    devices.forEach((d, i) => $('cameraSelect').add(new Option(d.label || `Camera ${i+1} — enable permission to reveal name`, d.deviceId)));
    if (devices.some(d => d.deviceId === current)) $('cameraSelect').value = current;
    if (camera.activeId && !devices.some(d => d.deviceId === camera.activeId)) { await stopCamera(); notice('Selected camera was removed.', true); }
    if (!devices.length) notice('No camera found. Check the USB connection and Windows camera permissions.', true);
    else notice(txt('তালিকায় USB camera-এর নাম বেছে Start চাপুন।','Choose your actual USB camera by name, then press Start.'));
    controls();
  } catch (err) { notice(Core.cameraError(err), true); }
}
async function startCamera() {
  if (!$('cameraSelect').value) return;
  $('startCamera').disabled = true; notice('Opening the exact selected device…');
  forgetCurrentEvidence(); invalidate('Camera is starting.');
  try {
    const info = await camera.start($('cameraSelect').value); if (!info) return;
    state.device = info; localStorage.setItem('agri.camera', $('cameraSelect').value);
    show($('cameraVideo'), true); show($('feedEmpty'), false); statusBadge($('feedState'), 'LIVE', '');
    $('deviceProof').textContent = `Selected: ${info.label} · ${info.settings.width || '?'} × ${info.settings.height || '?'} · device …${info.deviceId.slice(-8)}`;
    notice('Selected device ID verified. Show a close tomato leaf; screening starts automatically.');
    controls(); updateROI(); scheduleInference(0);
  } catch (err) { camera.stop(); showCameraEmpty(); notice(Core.cameraError(err), true); controls(); }
}
async function stopCamera() {
  if (state.recorder) await stopRecording();
  invalidate('Camera stopped. Old predictions were cleared.','STOPPED'); camera.stop(); state.device = null; showCameraEmpty(); controls();
}
async function pauseCamera() {
  if (state.recorder) await stopRecording();
  if (camera.paused) { await camera.resume(); statusBadge($('feedState'), 'LIVE', ''); scheduleInference(0); }
  else { camera.pause(); invalidate('Preview paused; this is not a fresh prediction.','PAUSED'); statusBadge($('feedState'),'PAUSED','amber'); }
  controls();
}
async function switchTab(tab) {
  await stopCamera(); $('recordedVideo').pause(); state.tab = tab; feedTitle();
  forgetCurrentEvidence();
  document.querySelectorAll('[data-source-tab]').forEach(b => { const active = b.dataset.sourceTab === tab; b.classList.toggle('active',active); b.setAttribute('aria-selected',String(active)); });
  show($('cameraOptions'), tab === 'camera'); show($('videoOptions'), tab === 'video'); show($('imageOptions'), tab === 'image');
  show($('recordedVideo'), tab === 'video' && Boolean($('recordedVideo').src)); show($('photoPreview'), tab === 'image' && Boolean($('photoPreview').src));
  show($('feedEmpty'), !frameReady()); $('sourceNote').textContent = tab === 'video' ? 'RECORDED · no live aerial connection' : tab === 'image' ? 'UPLOADED IMAGE' : 'Browser camera';
  $('deviceProof').textContent = tab === 'camera' ? 'No active camera' : tab === 'video' ? 'Local recorded media — not a live drone' : 'User-supplied image — crop identity unverified';
  statusBadge($('feedState'), tab === 'video' ? 'RECORDED' : tab === 'image' ? 'PHOTO' : 'STOPPED');
  invalidate(); controls(); updateROI(); refreshTelemetry();
  notice(tab==='camera'?'Choose the exact named camera, then Start.':tab==='video'?'Recorded playback only. Use close-up tomato leaves; wide aerial views are outside scope.':'Open a clear tomato leaf photo. Detection runs automatically; no confirmation checkbox is required.');
}
function updateROI() {
  drawDetections(state.currentPrediction);
  const m = media(); const w = m.videoWidth || m.naturalWidth; const h = m.videoHeight || m.naturalHeight; const box = $('feedContainer');
  if (!$('roiToggle').checked || !w || !h) { show($('roiGuide'),false); return; }
  const scale = Math.min(box.clientWidth/w,box.clientHeight/h); const side = Math.min(w,h)*.65*scale;
  const guide = $('roiGuide'); guide.style.width = side+'px'; guide.style.height = side+'px'; guide.style.left = (box.clientWidth-side)/2+'px'; guide.style.top = (box.clientHeight-side)/2+'px'; show(guide,true);
}
async function frameBlob() {
  if (!frameReady()) throw new Error('No readable current frame. Start the camera, play the video or choose a photo.');
  const m=media(); const width=m.videoWidth || m.naturalWidth; const height=m.videoHeight || m.naturalHeight;
  const scale=Math.min(1,1280/Math.max(width,height)); const c=document.createElement('canvas'); c.width=Math.round(width*scale); c.height=Math.round(height*scale);
  c.getContext('2d',{alpha:false}).drawImage(m,0,0,c.width,c.height);
  const blob=await new Promise(resolve=>c.toBlob(resolve,'image/jpeg',.9)); if (!blob) throw new Error('Frame encoding failed'); return blob;
}
async function frameForm() {
  const data=new FormData(); data.append('file',await frameBlob(),'frame.jpg'); data.append('crop','tomato'); data.append('roi',String($('roiToggle').checked)); return data;
}
function canInfer() { return !document.hidden && !state.capturing && !state.sending && $('liveInference').checked && frameReady() && (state.tab !== 'video' || !$('recordedVideo').paused); }
function scheduleInference(delay = Number($('sampleRate').value)) {
  clearTimeout(state.inferenceTimer); if (state.tab==='image') return; if (canInfer()) state.inferenceTimer=setTimeout(infer,delay);
}
async function infer(force = false) {
  if (!frameReady() || (!force && !canInfer())) return;
  if (state.inFlight) { if(state.tab==='image') state.pendingPhotoInference=true; else scheduleInference(120); return; }
  const token=state.inferenceToken; const marker={}; state.inFlight=marker;
  try {
    const data=await frameForm(); data.append('frame_id',String(token));
    const res=await api('/api/predict',{method:'POST',body:data},30000);
    if (token !== state.inferenceToken) return;
    const now=performance.now(); if (state.lastInference) $('inferenceRate').textContent=`Inference ${(1000/(now-state.lastInference)).toFixed(1)} /s`; state.lastInference=now;
    renderPrediction(res.prediction, state.tab === 'image');
  } catch (err) { if (token===state.inferenceToken) { clearPrediction(err.message,'UNAVAILABLE'); notice(err.message,true); } }
  finally { if (state.inFlight===marker) state.inFlight=null; if(state.tab==='image' && state.pendingPhotoInference){state.pendingPhotoInference=false;setTimeout(()=>infer(true),0);}else if(canInfer()) scheduleInference(); }
}
function renderPrediction(p, single = false) {
  state.currentPrediction=p;drawDetections(p);$('explainCapture').disabled=!frameReady()||state.capturing;
  const stable=state.stable.push(p); const good=['OK','REVIEW'].includes(p.status) && Boolean(p.label); const ready=single || stable.ready;
  statusBadge($('predictionStatus'),good ? (ready ? (p.status==='REVIEW'?'CHECK MODELS':'REVIEW') : 'STABILIZING') : p.status,good && ready ? '' : 'amber');
  $('predictionLabel').textContent=good ? (ready ? `Possible ${p.label}` : 'Checking consecutive frames…') : txt('সিদ্ধান্ত দেওয়া হয়নি','Screening abstained');
  $('predictionReason').textContent=p.reason || '';
  $('predictionScore').textContent=p.score == null ? '—' : `${(p.score*100).toFixed(1)}%`;
  $('predictionLatency').textContent=p.latency_ms == null ? '—' : p.latency_ms+' ms';
  $('stableCount').textContent=good ? (single ? 'Single-image result' : `${Math.min(stable.count,3)}/3 consistent frames`) : 'No disease label retained';
  const list=$('detectionList');list.replaceChildren();(p.detections||[]).forEach(d=>{const item=el('div','detected-leaf');item.append(el('strong','',`#${d.id} ${d.label} · ${(d.score*100).toFixed(1)}%`));if(d.models_disagree)item.append(el('small','',`Check: detector suggested ${d.detector_label}; preserved classifier suggests ${d.label}.`));list.append(item);});
  const q=p.quality; $('qualityInfo').textContent=q ? `Quality heuristic · brightness ${q.brightness} · sharpness ${q.sharpness} · foliage ${(q.foliage_fraction*100).toFixed(0)}%` : 'Quality unavailable';
}
async function captureFrame() {
  if(state.capturing)return;
  $('captureFrame').disabled=true;$('explainCapture').disabled=true;state.capturing=true; invalidate('Capturing a fresh frame…');
  try {
    if (state.inFlight) await new Promise(resolve=>{ const check=()=>state.inFlight ? setTimeout(check,40) : resolve(); check(); });
    const data=await frameForm(); data.append('source',source()); data.append('device_label',state.device?.label || (state.tab==='video' ? $('videoName').textContent : 'Uploaded image'));
    data.append('device_id',state.device?.deviceId || ''); data.append('media_time_s',String(state.tab==='video' ? $('recordedVideo').currentTime : 0)); data.append('captured_at',new Date().toISOString());
    const event=await api('/api/capture',{method:'POST',body:data}); state.lastEvent=event;
    renderPrediction(event.prediction,true); await loadEvents();
    toast(txt(`Evidence #${event.id} সংরক্ষিত। Discuss capture দিয়ে চ্যাটে যুক্ত করুন।`,`Evidence #${event.id} saved. Use Discuss capture to attach it to chat.`));
  } catch (err) { notice(err.message,true); toast(err.message); }
  finally { state.capturing=false; controls(); scheduleInference(); }
}
async function loadPhoto(file) {
  if (!file) return; if (file.size>10*1024*1024) return toast('Photo limit is 10 MB.');
  invalidate(); if (state.mediaURLs.image) URL.revokeObjectURL(state.mediaURLs.image); state.mediaURLs.image=URL.createObjectURL(file);
  $('photoPreview').onload=()=>{controls();updateROI();infer(true);};
  $('photoPreview').src=state.mediaURLs.image; $('photoName').textContent=file.name; forgetCurrentEvidence();
  show($('photoPreview'),true); show($('feedEmpty'),false); statusBadge($('feedState'),'PHOTO');
  notice('Photo selected. Local YOLO detection is running. Use Ask Doctor to discuss this exact image.');
  $('photoPreview').onerror=()=>{ notice('Unreadable photo. Use JPG/PNG/WEBP.',true); show($('photoPreview'),false); show($('feedEmpty'),true); };
}
function loadVideo(file) {
  if (!file) return; invalidate(); if (state.mediaURLs.video) URL.revokeObjectURL(state.mediaURLs.video); state.mediaURLs.video=URL.createObjectURL(file);
  $('recordedVideo').src=state.mediaURLs.video; $('videoName').textContent=file.name; forgetCurrentEvidence();
  show($('recordedVideo'),true); show($('feedEmpty'),false); statusBadge($('feedState'),'RECORDED','amber');
  notice('Recorded footage is local playback. Confirm a close-up tomato leaf before screening; aerial wide shots are outside model scope.');
}
async function startRecording() {
  if (state.recorder) return stopRecording();
  if (!camera.stream || state.recordingDraft) return;
  if (!window.MediaRecorder) return toast('Recording unavailable. Use a recent Chrome or Edge.');
  const mime=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm','video/mp4'].find(t=>MediaRecorder.isTypeSupported(t));
  if (!mime) return toast('This browser has no supported recording format.');
  const chunks=[]; let total=0; const rec=new MediaRecorder(camera.stream,{mimeType:mime,videoBitsPerSecond:2500000});
  const origin={source:source(),device_label:state.device?.label || 'Camera'};
  rec.ondataavailable=e=>{ if(e.data.size) { chunks.push(e.data); total+=e.data.size; if(total>110*1024*1024 && rec.state!=='inactive') rec.stop(); } };
  const done=new Promise(resolve=>{rec.onstop=async()=>{
    clearInterval(state.recordTimer); state.recorder=null; show($('recordingIndicator'),false);
    const blob=new Blob(chunks,{type:mime}); const draft={blob,url:URL.createObjectURL(blob),...origin,duration:(performance.now()-state.recordingStart)/1000,mime};
    state.recordingDraft=draft; renderRecordingDraft('Recording captured. Saving…'); controls();
    resolve(); saveRecordingDraft();
  };});
  rec.onerror=()=>{toast('Recording interrupted. Recover available footage using the download link.'); if(rec.state!=='inactive')rec.stop();};
  state.recordStop=done; state.recorder=rec; state.recordingStart=performance.now(); rec.start(1000);
  show($('recordingIndicator'),true); $('recordTime').textContent='00:00';
  state.recordTimer=setInterval(()=>{const seconds=Math.floor((performance.now()-state.recordingStart)/1000); $('recordTime').textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0'); if(seconds>=(state.status?.max_record_seconds || 120) && rec.state!=='inactive')rec.stop();},500);
  controls();
}
async function stopRecording() { const rec=state.recorder; if(!rec) return; if(rec.state!=='inactive')rec.stop(); await state.recordStop; }
function renderRecordingDraft(message) {
  let box=$('recordingRecovery'); if(!box){box=el('div','record-recovery');box.id='recordingRecovery';$('cameraOptions').before(box);}
  box.replaceChildren(el('div','',message)); const d=state.recordingDraft; if(!d)return;
  const link=el('a','',`Download ${Core.size(d.blob.size)}`);link.href=d.url;link.download='agrivision_recording'+(d.mime.includes('mp4')?'.mp4':'.webm');box.append(link);
  const retry=el('button','small','Retry save');retry.onclick=saveRecordingDraft; const discard=el('button','small','I saved it · dismiss');discard.onclick=()=>{URL.revokeObjectURL(d.url);state.recordingDraft=null;box.remove();controls();};box.append(retry,discard);
}
async function saveRecordingDraft() {
  const d=state.recordingDraft; if(!d || d.saving)return; d.saving=true;
  try {
    const data=new FormData();data.append('file',d.blob,'camera'+(d.mime.includes('mp4')?'.mp4':'.webm'));data.append('source',d.source);data.append('device_label',d.device_label);data.append('duration_s',String(d.duration));
    await api('/api/recordings',{method:'POST',body:data},60000); URL.revokeObjectURL(d.url);state.recordingDraft=null;$('recordingRecovery')?.remove();toast('Recording saved. Open History for playback and download.');loadRecordings();
  } catch(err) { renderRecordingDraft('Server save failed: '+err.message+' Your recording is still available below.'); }
  finally { d.saving=false;controls(); }
}
function eventDate(e) { return new Date(e.created_at).toLocaleString(state.language==='bn'?'bn-BD':'en-GB',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}); }
function shortClass(p) { return ['OK','REVIEW'].includes(p.status) && p.label ? p.label : p.status.replaceAll('_',' '); }
async function loadEvents() { state.events=await api('/api/events');renderEvents(); if(state.view==='history')renderHistory(); if(state.view==='reports')renderReports(); }
function renderEvents() {
  $('recentEvents').replaceChildren(); show($('recentEmpty'),state.events.length===0);
  state.events.slice(0,4).forEach(e=>{const row=el('tr');row.tabIndex=0;row.setAttribute('aria-label','Open evidence '+e.id);const p=e.prediction;
    [eventDate(e),e.source,shortClass(p),p.score==null?'—':(p.score*100).toFixed(1)+'%'].forEach(t=>row.append(el('td','',t)));
    const td=el('td');td.append(el('span','badge '+(p.status==='OK'?'':'amber'),['OK','REVIEW'].includes(p.status)?'REVIEW':'ABSTAIN'));row.append(td);row.onclick=()=>openEvent(e);row.onkeydown=k=>{if(k.key==='Enter')openEvent(e);};$('recentEvents').append(row);});
}
function renderHistory() {
  $('historyCount').textContent=String(state.events.length); const grid=$('historyGrid');grid.replaceChildren();
  if(!state.events.length){grid.append(el('p','muted','No captures yet. Capture a real frame in Monitor.'));return;}
  state.events.forEach(e=>{const card=el('button','event-card');const image=el('img');image.src=e.annotated_url||e.image_url;image.alt='Saved evidence #'+e.id;image.loading='lazy';const body=el('div');body.append(el('strong','',shortClass(e.prediction)),el('small','',eventDate(e)),el('small','',e.source),el('span','badge neutral',e.telemetry.mode));card.append(image,body);card.onclick=()=>openEvent(e);grid.append(card);});
}
function openEvent(e) {
  const detail=$('evidenceDetail');detail.replaceChildren();const image=el('img');image.src=e.annotated_url||e.image_url;image.alt='Original captured frame #'+e.id;detail.append(image,el('h3','',`#${e.id} · ${shortClass(e.prediction)}`),el('p','',`${e.source} · ${e.device_label || 'No device recorded'} · ${new Date(e.created_at).toLocaleString()}`),el('p','',e.prediction.reason || ''));
  const use=el('button','primary','Attach this evidence to Plant Doctor');use.onclick=()=>{attachEvidence(e);$('evidenceDialog').close();};
  const download=el('a','button','Download original');download.href=e.image_url;download.download=`agrivision_evidence_${e.id}.jpg`; const row=el('div','button-row');row.append(use,download);if(e.annotated_url){const a=el('a','button','Download with boxes');a.href=e.annotated_url;a.download=`agrivision_annotated_${e.id}.jpg`;row.append(a);}detail.append(row);
  const disclosure=el('details');disclosure.append(el('summary','','Model, quality and telemetry provenance'),el('pre','',JSON.stringify(e,null,2)));detail.append(disclosure);$('evidenceDialog').showModal();
}
function attachEvidence(e) {
  clearPending();state.evidence=e;const box=$('pendingEvidence');box.replaceChildren();const image=el('img');image.src=e.annotated_url||e.image_url;image.alt='Attached saved evidence';const remove=el('button','','×');remove.setAttribute('aria-label','Remove saved evidence');remove.onclick=()=>{state.evidence=null;show(box,false);};box.append(image,el('span','',`Saved #${e.id} · ${e.source} · ${shortClass(e.prediction)}`),remove);show(box,true);$('question').focus();toast('This saved event will be used only for your next message.');
}
async function loadRecordings() {
  try {const list=await api('/api/recordings');const box=$('recordingList');box.replaceChildren();if(!list.length)box.append(el('p','table-empty','No camera recordings saved.'));
    list.forEach(r=>{const item=el('div','record-item');item.append(el('strong','',new Date(r.created_at).toLocaleString()+' · '+Core.size(r.size_bytes)));const v=el('video');v.controls=true;v.preload='none';v.src=r.url;const a=el('a','','Download recording');a.href=r.url;a.download=r.filename;item.append(v,a,el('small','',r.source+' · '+r.device_label));box.append(item);});
  }catch(err){toast(err.message);}
}
function renderReports() {
  const total=state.events.length;const review=state.events.filter(e=>['OK','REVIEW'].includes(e.prediction.status)).length;const stats=$('reportStats');stats.replaceChildren();
  [[total,'Saved captures'],[review,'Class matches to review'],[total-review,'Abstained / unavailable']].forEach(([n,label])=>{const box=el('div','report-stat');box.append(el('strong','',String(n)),el('small','',label));stats.append(box);});
  const counts={};state.events.forEach(e=>{counts[e.prediction.status]=(counts[e.prediction.status]||0)+1;});const box=$('reportDistribution');box.replaceChildren();Object.entries(counts).forEach(([key,value])=>{const row=el('div','distribution-row');row.append(el('span','',key),el('b','',String(value)));box.append(row);});if(!total)box.append(el('p','muted','No evidence to summarize.'));
}
async function addAttachment(file) {
  if(!file)return; const image=file.type.startsWith('image/') || /\.(jpe?g|png|webp)$/i.test(file.name);
  if(file.size>(image?10:8)*1024*1024)return toast(image?'Image limit is 10 MB.':'Document limit is 8 MB.');
  if(state.pending.length>=4)return toast('Up to four attachments per question.');
  if(image && state.pending.some(a=>a.image))return toast('Use one leaf photo per question for clear provenance.');
  state.evidence=null;show($('pendingEvidence'),false);

  const a={localId:crypto.randomUUID(),file,image,url:image?URL.createObjectURL(file):null,uploaded:null};state.pending.push(a);renderPending();
}
function clearPending() { state.pending.forEach(a=>{if(a.url)URL.revokeObjectURL(a.url);});state.pending=[];renderPending(); }
function renderPending() {
  const box=$('attachmentPreviews');box.replaceChildren();show($('chatCropConfirmation'),state.pending.some(a=>a.image));state.pending.forEach(a=>{const chip=el('div','attachment-chip');chip.dataset.testid='attachment-preview';if(a.image){const im=el('img');im.src=a.url;im.alt='Attachment preview: '+a.file.name;chip.append(im);}else chip.append(el('div','file-icon',a.file.name.split('.').pop().toUpperCase()));const label=el('span','',a.file.name);label.append(el('small','',Core.size(a.file.size)+(a.uploaded?' · ready':'')));const remove=el('button','','×');remove.type='button';remove.disabled=state.sending;remove.setAttribute('aria-label','Remove '+a.file.name);remove.onclick=()=>{if(a.url)URL.revokeObjectURL(a.url);state.pending=state.pending.filter(x=>x!==a);renderPending();};chip.append(label,remove);box.append(chip);});
}
/* Safe Markdown subset: text nodes + bold/code. No raw HTML or automatic links. */
function markdown(text, parent) {
  String(text).split(/\n\s*\n/).forEach(part=>{const p=el('p'); const tokens=part.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);tokens.forEach(t=>{if(t.startsWith('**')&&t.endsWith('**'))p.append(el('strong','',t.slice(2,-2)));else if(t.startsWith('`')&&t.endsWith('`'))p.append(el('code','',t.slice(1,-1)));else p.append(document.createTextNode(t));});parent.append(p);});
}
function renderMessage(role, payload) {
  $('chatWelcome')?.remove(); const row=el('div','message '+role);const avatar=el('div','message-avatar');
  if(role==='assistant'){const img=el('img');img.src='/assets/plant-doctor-bot.svg';img.alt='';avatar.append(img);}else avatar.textContent='You';
  const content=el('div','message-content'); const body=el('div','message-body');
  if(role==='user'){
    if(payload.event){const im=el('img','event-chat-image');im.src=payload.event.image_url;im.alt='Saved evidence #'+payload.event.id;content.append(im,el('small','',`Saved event #${payload.event.id} · ${new Date(payload.event.created_at).toLocaleString()}`));}
    (payload.attachments||[]).forEach(a=>{const box=el('div','message-attachment');if(a.mime.startsWith('image/')){const im=el('img');im.src=a.url;im.alt='Submitted photo: '+a.name;box.append(im);}else{const link=el('a','',a.name+' · '+Core.size(a.size));link.href=a.url;link.download=a.name;box.append(link);if(a.preview){const d=el('details');d.append(el('summary','','Document preview'),el('pre','doc-preview',a.preview));box.append(d);}}content.append(box);});
    markdown(payload.question||'',body);
  }else{
    markdown(payload.answer||'',body);content.append(body);
    if(payload.annotated_url){const im=el('img','annotated-chat-image');im.src=payload.annotated_url;im.alt='Actual local YOLO boxes for the submitted photo';content.prepend(im);}
    if(payload.evidence_context?.follow_up)content.prepend(el('small','evidence-context','Follow-up: same previously submitted evidence · '+(payload.evidence_context.name||('capture #'+payload.evidence_context.event_id))));
    const mode=payload.provider==='offline'?'LOCAL YOLO + GUIDE':payload.provider.toUpperCase();const info=el('div','message-info',`${mode} · ${payload.image_understanding?'image transmitted to vision provider':(payload.local_vision?'local YOLO processed the submitted evidence':'guide / text context')}${payload.prediction?' · YOLO: '+payload.prediction.status:''}`);content.append(info);
    if(payload.sources?.length || payload.attempts?.length || payload.prediction){const details=el('details','source-disclosure');details.dataset.testid='sources';details.append(el('summary','',`View sources & evidence${payload.sources?.length?' ('+payload.sources.length+')':''}`));
      (payload.sources||[]).forEach((s,i)=>{const d=el('div','source-item');const link=el('a','',`[${i+1}] ${s.title}`);if(/^https:\/\//.test(s.url)){link.href=s.url;link.target='_blank';link.rel='noopener noreferrer';}d.append(link,el('small','',s.pages?'Pages '+s.pages.join(', '):(s.section||'Verified source')),el('p','',s.paraphrase||''));if(s.local){const local=el('a','','Open supplied guide PDF');local.href=s.local;local.target='_blank';d.append(local);}details.append(d);});
      if(payload.prediction)details.append(el('pre','doc-preview',JSON.stringify(payload.prediction,null,2)));
      if(payload.attempts?.length)details.append(el('small','',payload.attempts.map(a=>`${a.provider}: ${a.status}`).join(' → ')));content.append(details);
    }
    $('chatMode').textContent=payload.provider==='offline'?txt('স্থানীয় YOLO + offline guide','Local YOLO + offline guide'):payload.provider+' · '+payload.mode;
  }
  if(role==='user')content.append(body);row.append(avatar,content);$('messages').append(row);$('messages').scrollTop=$('messages').scrollHeight;
}
async function sendChat(event) {
  event.preventDefault();if(state.sending)return;
  const question=$('question').value.trim();if(!question&&!state.pending.length&&!state.evidence)return;
  state.sending=true;if(state.tab!=='image')invalidate('Plant Doctor is answering; live screening resumes afterward.','CHAT');$('sendChat').disabled=true;show($('composeError'),false);renderPending();
  const thinking=el('div','thinking',txt('প্রমাণ যাচাই করে উত্তর প্রস্তুত হচ্ছে…','Reviewing the evidence…'));thinking.id='thinking';$('messages').append(thinking);$('messages').scrollTop=$('messages').scrollHeight;
  try {
    for(const a of state.pending){if(!a.uploaded){const data=new FormData();data.append('file',a.file);a.uploaded=await api('/api/attachments',{method:'POST',body:data});}}
    const response=await postJSON('/api/chat',{question,language:state.language,crop:'tomato',conversation_id:state.conversation,attachment_ids:state.pending.map(a=>a.uploaded.id),event_id:state.evidence?.id || null,provider:$('chatProvider').value},100000);
    thinking.remove();renderMessage('user',response.user_message);renderMessage('assistant',response.assistant_message);
    $('question').value='';clearPending();state.evidence=null;show($('pendingEvidence'),false);refreshConversations();refreshStatus();
  }catch(err){thinking.remove();$('composeError').textContent=err.message;show($('composeError'),true);}
  finally{state.sending=false;$('sendChat').disabled=false;renderPending();scheduleInference(0);}
}
async function refreshConversations() {
  try {const items=await api('/api/conversations');$('conversationSelect').replaceChildren(new Option(txt('সংরক্ষিত চ্যাট…','Open saved conversation…'),''));items.forEach(c=>$('conversationSelect').add(new Option(c.title,c.id)));if(items.some(c=>c.id===state.conversation))$('conversationSelect').value=state.conversation;}catch{/* current conversation continues */}
}
async function openConversation(cid) {
  if(!cid||state.sending)return;try{const messages=await api('/api/conversations/'+cid);state.conversation=cid;$('messages').replaceChildren();messages.forEach(m=>renderMessage(m.role,m));clearPending();state.evidence=null;show($('pendingEvidence'),false);}catch(err){toast(err.message);}
}
function newChat() { if(state.sending)return;state.conversation=crypto.randomUUID().replaceAll('-','');$('messages').replaceChildren();state.evidence=null;show($('pendingEvidence'),false);clearPending();$('question').value='';renderMessage('assistant',{answer:txt('নতুন চ্যাট। ছবি বা নির্দিষ্ট প্রশ্ন পাঠান।','New conversation. Send a photo or a specific question.'),provider:'offline',sources:[]});$('conversationSelect').value=''; }
async function refreshTelemetry() {
  try {const time=state.tab==='video'?$('recordedVideo').currentTime:0;const g=await api(`/api/telemetry?source=${encodeURIComponent(source())}&time_s=${time||0}`);
    statusBadge($('gpsMode'),g.mode,g.mode==='SIMULATED'?'amber':g.mode==='UNAVAILABLE'?'neutral':'');$('gpsCoordinates').textContent=g.latitude==null?'No verified location':`${g.latitude.toFixed(5)}°, ${g.longitude.toFixed(5)}°`;
    $('gpsOrigin').textContent=g.origin||g.reason||'A coordinate is never inferred from a leaf photo.';$('fieldMode').textContent=g.mode;$('fieldDetails').textContent=(g.latitude==null?'No current coordinates. ':`Latitude ${g.latitude}, longitude ${g.longitude}. `)+(g.origin||g.reason||'')+' '+g.note;
    document.querySelector('.telemetry-card').classList.toggle('simulated',g.mode==='SIMULATED');
  }catch{/* server indicator reports connection state */}
}
async function gpsMode(mode){try{await postJSON('/api/telemetry/mode',{mode});refreshTelemetry();}catch(err){toast(err.message);}}
function browserLocation(){if(!navigator.geolocation)return toast('Geolocation is unavailable.');navigator.geolocation.getCurrentPosition(async p=>{try{await postJSON('/api/telemetry/live',{latitude:p.coords.latitude,longitude:p.coords.longitude,accuracy_m:p.coords.accuracy,timestamp_utc:new Date(p.timestamp).toISOString(),origin:'Browser device geolocation'});refreshTelemetry();toast('Device location received; expires after 30 seconds. This is not a leaf coordinate.');}catch(err){toast(err.message);}},async()=>{await gpsMode('UNAVAILABLE');toast('Device location failed or permission was denied. Location is now UNAVAILABLE.');},{timeout:10000,maximumAge:0});}
async function refreshStatus() {
  try {
    const s=await api('/api/status');state.status=s;$('serverDot').classList.remove('off');$('serverStatus').textContent=s.vision.ready?'YOLO ready':'YOLO unavailable';$('classCount').textContent=String(s.vision.model.classes?.length || 0);
    const old=$('modelSelect').value;$('modelSelect').replaceChildren();s.vision.available.forEach(id=>$('modelSelect').add(new Option(({hybrid:'Leaf boxes + your 5-class model',detector9:'Secondary detector · 9 labels · review',original:'Your original classifier · 5 classes',expanded:'Optional expanded classifier · 10 classes'})[id]||id,id)));if(document.activeElement!==$('modelSelect'))$('modelSelect').value=s.vision.selected;else $('modelSelect').value=old;
    $('modelInfo').textContent=JSON.stringify(s.vision,null,2);$('providerSettings').replaceChildren();Object.entries(s.providers).forEach(([key,p])=>{const row=el('div','provider-row');row.append(el('span','',`${key.toUpperCase()} · ${p.model} · ${p.configured?'configured':'not configured'} · ${p.state}`));const button=el('button','small','Test connection');button.disabled=!p.configured;button.onclick=async()=>{button.disabled=true;button.textContent='Testing…';try{const r=await postJSON('/api/providers/test/'+key,{},30000);toast(key.toUpperCase()+': '+r.state);refreshStatus();}catch(err){toast(err.message);}finally{button.disabled=false;button.textContent='Test connection';}};row.append(button);$('providerSettings').append(row);});
    $('resourceInfo').textContent=`Process RAM ${s.resources.process_rss_mb} MB · host CPU ${s.resources.host_cpu_percent}% · process threads ${s.resources.process_threads}. These are host measurements.`;
    if(!s.vision.ready)notice('Model unavailable. Open Settings to inspect the runtime. Your trained file is preserved.',true);
  }catch(err){$('serverDot').classList.add('off');$('serverStatus').textContent='Server disconnected';invalidate('Local API disconnected. Retry after restarting the server.','UNAVAILABLE');}
}
// Explicit event wiring keeps the app compatible with a strict script CSP.
$('enableCameras').onclick=()=>cameras(true);$('refreshCameras').onclick=()=>cameras(!camera.stream);$('startCamera').onclick=startCamera;$('pauseCamera').onclick=pauseCamera;$('stopCamera').onclick=stopCamera;
$('cameraSelect').onchange=async()=>{await stopCamera();controls();notice('Selected '+$('cameraSelect').selectedOptions[0].text+'. Press Start to verify this exact device.');};
$('captureFrame').onclick=captureFrame;$('recordCamera').onclick=startRecording;$('fullscreenFeed').onclick=()=>{if(document.fullscreenElement)document.exitFullscreen();else $('feedContainer').requestFullscreen?.().catch(()=>toast('Fullscreen is unavailable.'));};
$('explainCapture').onclick=async()=>{if(!frameReady())return;if(!state.lastEvent || state.tab!=='image')await captureFrame();if(state.lastEvent)attachEvidence(state.lastEvent);};
$('analyzePhoto').onclick=()=>{invalidate('Analyzing this photo…');infer(true);};
for(const id of ['liveInference','roiToggle','sampleRate'])$(id).onchange=()=>{forgetCurrentEvidence();invalidate('Screening settings changed; awaiting a new frame.');updateROI();if(state.tab==='image'&&frameReady())infer(true);else scheduleInference(0);};
$('sourceDeclaration').onchange=()=>{forgetCurrentEvidence();invalidate('Source declaration changed.');scheduleInference(0);};
document.querySelectorAll('[data-source-tab]').forEach(b=>b.onclick=()=>switchTab(b.dataset.sourceTab));
document.querySelectorAll('.nav-item').forEach(b=>b.onclick=()=>view(b.dataset.view));document.querySelectorAll('[data-open-view]').forEach(b=>b.onclick=()=>view(b.dataset.openView));
$('photoInput').onchange=e=>{loadPhoto(e.target.files[0]);e.target.value='';};$('videoInput').onchange=e=>{loadVideo(e.target.files[0]);e.target.value='';};
$('recordedVideo').onloadeddata=()=>{controls();updateROI();};$('recordedVideo').onplay=()=>{invalidate();scheduleInference(0);};$('recordedVideo').onpause=()=>{invalidate('Recorded playback paused. Capture to analyze this exact still frame.','PAUSED');controls();};$('recordedVideo').onended=()=>{invalidate('End of recorded video.','ENDED');controls();};$('recordedVideo').onseeking=()=>invalidate('Video position changed.');$('recordedVideo').onseeked=()=>{controls();scheduleInference(0);refreshTelemetry();};$('recordedVideo').onerror=()=>{notice('This video codec cannot be played. Use H.264 MP4 or WebM in Chrome/Edge.',true);invalidate();controls();};
$('cameraVideo').onloadedmetadata=()=>{controls();updateROI();};window.addEventListener('resize',updateROI);document.addEventListener('fullscreenchange',updateROI);
navigator.mediaDevices?.addEventListener('devicechange',()=>cameras(false));
$('langBn').onclick=()=>language('bn');$('langEn').onclick=()=>language('en');$('chatForm').onsubmit=sendChat;
$('question').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.isComposing){e.preventDefault();$('chatForm').requestSubmit();}};
$('chatImageInput').onchange=e=>{addAttachment(e.target.files[0]);e.target.value='';};$('chatDocInput').onchange=e=>{addAttachment(e.target.files[0]);e.target.value='';};$('newChat').onclick=newChat;$('conversationSelect').onchange=e=>openConversation(e.target.value);
document.querySelectorAll('[data-prompt-en]').forEach(b=>b.onclick=()=>{$('question').value=b.dataset[state.language==='bn'?'promptBn':'promptEn'];$('question').focus();});
$('closeEvidence').onclick=()=>$('evidenceDialog').close();$('evidenceDialog').onclick=e=>{if(e.target===$('evidenceDialog'))$('evidenceDialog').close();};$('refreshRecordings').onclick=loadRecordings;
$('gpsOff').onclick=()=>gpsMode('UNAVAILABLE');$('gpsSim').onclick=()=>gpsMode('SIMULATED');$('gpsBrowser').onclick=browserLocation;
$('gpsFile').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{const data=new FormData();data.append('file',file);await api('/api/telemetry/csv',{method:'POST',body:data});refreshTelemetry();toast('Recorded CSV loaded; coordinates apply to recorded video only.');}catch(err){toast(err.message);}e.target.value='';};
$('selectModel').onclick=async()=>{try{await postJSON('/api/model/select',{choice:$('modelSelect').value},60000);forgetCurrentEvidence();invalidate('Model changed. Awaiting new evidence.');refreshStatus();if(state.tab==='image')infer(true);else scheduleInference(0);}catch(err){toast(err.message);}};
window.addEventListener('beforeunload',e=>{if(state.recorder||state.recordingDraft||state.sending){e.preventDefault();e.returnValue='';}});
window.addEventListener('pagehide',()=>{camera.stop();$('recordedVideo').pause();});
document.addEventListener('visibilitychange',()=>{if(document.hidden){if(state.tab!=='image')invalidate('Tab hidden; inference suspended.');}else if(state.tab==='image'&&frameReady()&&!state.currentPrediction)infer();else scheduleInference(0);});
language(state.language);refreshStatus();loadEvents().catch(err=>toast(err.message));refreshConversations();refreshTelemetry();
setInterval(refreshStatus,15000);state.telemetryTimer=setInterval(refreshTelemetry,4000);

function forgetCurrentEvidence(){state.lastEvent=null;$('explainCapture').disabled=true;state.evidence=null;show($('pendingEvidence'),false);}
function drawDetections(p){
  const svg=$('detectionOverlay');svg.replaceChildren();
  const m=media();const w=m.videoWidth||m.naturalWidth;const h=m.videoHeight||m.naturalHeight;const box=$('feedContainer');
  if(!p?.detections?.length||!w||!h||!box.clientWidth||!box.clientHeight){show(svg,false);return;}
  const scale=Math.min(box.clientWidth/w,box.clientHeight/h);const width=w*scale,height=h*scale;
  svg.style.left=(box.clientWidth-width)/2+'px';svg.style.top=(box.clientHeight-height)/2+'px';svg.style.width=width+'px';svg.style.height=height+'px';svg.setAttribute('viewBox',`0 0 ${w} ${h}`);show(svg,true);
  const ns='http://www.w3.org/2000/svg';const font=12/scale;
  for(const d of p.detections){
    const [a,b,c,e]=d.box;const x=a*w,y=b*h,rw=(c-a)*w,rh=(e-b)*h;
    const r=document.createElementNS(ns,'rect');r.setAttribute('x',x);r.setAttribute('y',y);r.setAttribute('width',rw);r.setAttribute('height',rh);r.setAttribute('class','leaf-box');r.setAttribute('vector-effect','non-scaling-stroke');svg.append(r);
    const label=`${d.label} ${(d.score*100).toFixed(1)}%${d.review_required?' · check':''}`;const tw=Math.min(w,label.length*font*.57+font);const tx=Math.max(0,Math.min(x,w-tw)),ty=Math.max(font*1.5,y);
    const bg=document.createElementNS(ns,'rect');bg.setAttribute('x',tx);bg.setAttribute('y',ty-font*1.5);bg.setAttribute('width',tw);bg.setAttribute('height',font*1.5);bg.setAttribute('class','leaf-label-bg');svg.append(bg);
    const t=document.createElementNS(ns,'text');t.setAttribute('x',tx+font*.25);t.setAttribute('y',ty-font*.35);t.setAttribute('font-size',font);t.setAttribute('class','leaf-label');t.textContent=label;svg.append(t);
  }
}
async function loadKnowledge(){try{const k=await api('/api/knowledge');$('knowledgeInfo').textContent=`${k.count} curated guides. Visual classes depend on the selected model. Magnesium and untrained conditions are information only.`;k.entries.forEach(d=>$('knowledgeSelect').add(new Option(d.label,d.label)));}catch(err){$('knowledgeInfo').textContent=err.message;}}
$('askKnowledge').onclick=()=>{const name=$('knowledgeSelect').value;if(!name)return;view('chat');$('question').value=txt(name+' এর কারণ, লক্ষণ, করণীয় ও প্রতিরোধ বলুন।','Explain causes, symptoms, care and prevention for '+name+'.');$('question').focus();};
loadKnowledge();
