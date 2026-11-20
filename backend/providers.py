"""Bounded provider fallback, reloadable local configuration and safe diagnostics."""
import os,re,time,base64
import httpx
from dotenv import dotenv_values
from .config import ROOT
STATE={};CAPS={};SKIP_UNTIL={}
META_BASE='https://api.meta.ai/v1'
GEMINI_BASE='https://generativelanguage.googleapis.com/v1beta'
GROQ_BASE='https://api.groq.com/openai/v1'
DEFAULTS={'meta':'muse-spark-1.3','gemini':'gemini-2.5-flash-lite','groq':'qwen/qwen3.8-27b','ollama':'qwen3:4b'}
KEYS={'meta':'MODEL_API_KEY','gemini':'GEMINI_API_KEY','groq':'GROQ_API_KEY'}

def setting(key,default=''):
    # Read only the known local file; never accept credential or provider URLs from the browser.
    local=dotenv_values(ROOT/'.env') if (ROOT/'.env').is_file() else {}
    value=local.get(key) if key in local else os.getenv(key,default)
    return str(value or '').strip()

def credential(name):
    if name=='meta':return setting('MODEL_API_KEY') or setting('META_API_KEY')
    return setting(KEYS.get(name,''))

def model_name(name):
    model=setting({'meta':'META_MODEL','gemini':'GEMINI_MODEL','groq':'GROQ_MODEL','ollama':'OLLAMA_MODEL'}[name],DEFAULTS[name])
    if not re.fullmatch(r'[\w./:-]{1,150}',model):raise RuntimeError('invalid model name')
    return model

def configured():return {'meta':bool(credential('meta')),'gemini':bool(credential('gemini')),'groq':bool(credential('groq')),'ollama':setting('OLLAMA_ENABLED','false').lower()=='true'}

def status():return {k:{'configured':v,'state':STATE.get(k,'untested' if v else 'not configured'),'model':model_name(k)} for k,v in configured().items()}

def check_response(r):
    if r.status_code==429:raise RuntimeError('quota/rate limit (HTTP 429)')
    if r.status_code in (401,403):raise RuntimeError(f'credentials/access rejected (HTTP {r.status_code})')
    if r.status_code==404:raise RuntimeError('configured model or endpoint unavailable (HTTP 404)')
    if r.status_code==400:raise RuntimeError('provider rejected model or request format (HTTP 400)')
    if r.status_code>=400:raise RuntimeError(f'provider service unavailable (HTTP {r.status_code})')
    return r.json()

def safe_error(exc):
    message=str(exc)
    safe=['quota/rate limit','credentials/access rejected','configured model or endpoint unavailable','provider rejected model or request format','provider service unavailable','empty/invalid response','truncated response','blocked or truncated response','invalid model name','Ollama must use a loopback URL','unsupported dose']
    if any(message.startswith(s) for s in safe):return message[:120]
    if isinstance(exc,httpx.TimeoutException):return 'provider request timed out'
    if isinstance(exc,httpx.ConnectError):return 'provider connection failed'
    return 'invalid or unreachable provider response'

def capability(client,name,model):
    # Models-list access is not a prerequisite for a valid Chat Completions key.
    if name=='meta':return model.startswith(('muse-spark-','muse-wonder-'))
    if name=='gemini':return model.startswith('gemini-')
    if name=='groq':return model in {'qwen/qwen3.8-27b','meta-llama/llama-4-scout-17b-16e-instruct','meta-llama/llama-4-maverick-17b-128e-instruct','meta-models/muse-spark-open'}
    url=setting('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')
    if not re.fullmatch(r'http://(localhost|127\.0\.0\.1):\d{2,5}',url):raise RuntimeError('Ollama must use a loopback URL')
    key=(name,model)
    if key not in CAPS or time.monotonic()-CAPS[key][0]>300:
        data=check_response(client.post(url+'/api/show',json={'model':model}))
        CAPS[key]=(time.monotonic(),'vision' in data.get('capabilities',[]))
    return CAPS[key][1]

def generate(name,system,prompt,image=None,timeout=25):
    model=model_name(name)
    # One generation attempt. No hidden retries, paid web-search tools or raw error echoes.
    with httpx.Client(timeout=httpx.Timeout(timeout,connect=min(5,timeout)),follow_redirects=False,trust_env=False) as client:
        vision=capability(client,name,model)
        encoded=base64.b64encode(image).decode() if image and vision else None
        if image and not vision:prompt+='\nThe image was NOT transmitted to this text-only provider. Use only supplied local YOLO evidence.'
        if name in ('meta','groq'):
            content=[{'type':'text','text':prompt}]
            if encoded:content.append({'type':'image_url','image_url':{'url':'data:image/jpeg;base64,'+encoded}})
            body={'model':model,'messages':[{'role':'system','content':system},{'role':'user','content':content}],'max_completion_tokens':2500}
            if name=='meta':body['reasoning_effort']='minimal'
            data=check_response(client.post((META_BASE if name=='meta' else GROQ_BASE)+'/chat/completions',headers={'Authorization':'Bearer '+credential(name)},json=body))
            choice=data['choices'][0]
            if choice.get('finish_reason')=='length':raise RuntimeError('truncated response')
            output=choice['message']['content']
        elif name=='gemini':
            parts=[{'text':prompt}]
            if encoded:parts.append({'inline_data':{'mime_type':'image/jpeg','data':encoded}})
            data=check_response(client.post(GEMINI_BASE+'/models/'+model+':generateContent',headers={'x-goog-api-key':credential(name)},json={
                'system_instruction':{'parts':[{'text':system}]},'contents':[{'role':'user','parts':parts}],
                'generationConfig':{'temperature':.1,'maxOutputTokens':1800}}))
            candidate=data['candidates'][0]
            if candidate.get('finishReason') not in (None,'STOP'):raise RuntimeError('blocked or truncated response')
            output='\n'.join(p.get('text','') for p in candidate['content']['parts'] if not p.get('thought'))
        else:
            url=setting('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')
            user={'role':'user','content':prompt}
            if encoded:user['images']=[encoded]
            data=check_response(client.post(url+'/api/chat',json={'model':model,'stream':False,'think':False,'messages':[{'role':'system','content':system},user],'options':{'temperature':.1,'num_predict':650}}))
            output=data['message']['content']
        if not isinstance(output,str) or not 2<=len(output.strip())<=16000:raise RuntimeError('empty/invalid response')
        return output.strip(),bool(encoded),model

def test_provider(name):
    if name not in DEFAULTS:raise ValueError('Unknown provider')
    if not configured()[name]:return {'provider':name,'ok':False,'state':'not configured','model':model_name(name)}
    try:
        _,_,model=generate(name,'This is an API connection test.','Reply only: AgriVision connection OK.',timeout=20)
        STATE[name]='connection test succeeded';SKIP_UNTIL.pop(name,None)
        return {'provider':name,'ok':True,'state':STATE[name],'model':model,'note':'Text connection tested; image support and agronomic accuracy are separate.'}
    except Exception as exc:
        STATE[name]=safe_error(exc)
        return {'provider':name,'ok':False,'state':STATE[name],'model':model_name(name)}
