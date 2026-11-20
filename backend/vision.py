"""Actual YOLO detections with measured boxes; preserved legacy classification stays separate."""
import hashlib
import threading
import time
import os
import numpy as np
import cv2
from .config import MODEL_FILES, MIN_SCORE, MIN_MARGIN, DETECTION_MIN_SCORE

FIVE={'Bacterial_Spot','Early_Blight','Healthy','Late_Blight','Yellow_Leaf_Curl_Virus'}
TEN=FIVE|{'Leaf_Mold','Septoria_Leaf_Spot','Spider_Mites','Target_Spot','Tomato_Mosaic_Virus'}

def canonical(name):
    s=str(name).lower().replace('_',' ').strip()
    pairs=[('septoria','Septoria Leaf Spot'),('early blight','Early Blight'),('late blight','Late Blight'),
           ('bacterial spot','Bacterial Spot'),('mosaic','Tomato Mosaic Virus'),('yellow leaf curl','Yellow Leaf Curl Virus'),
           ('yellow virus','Tomato Yellow Virus'),('mold','Leaf Mold'),('spider','Spider Mites'),('target spot','Target Spot')]
    for word,label in pairs:
        if word in s:return label
    if s in ('tomato leaf','healthy','tomato healthy','tomato leaf healthy'):return 'Healthy'
    return str(name).replace('_',' ')

DETECTOR_CLASSES={'Early Blight','Late Blight','Bacterial Spot','Septoria Leaf Spot','Healthy',
                  'Tomato Mosaic Virus','Tomato Yellow Virus','Leaf Mold','Spider Mites'}

def assess_quality(frame):
    small=cv2.resize(frame,(256,256),interpolation=cv2.INTER_AREA)
    gray=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY);hsv=cv2.cvtColor(small,cv2.COLOR_BGR2HSV)
    mean,std=float(gray.mean()),float(gray.std());blur=float(cv2.Laplacian(gray,cv2.CV_64F).var());clipped=float((gray>248).mean())
    foliage=float(((hsv[:,:,0]>=15)&(hsv[:,:,0]<=95)&(hsv[:,:,1]>=38)&(hsv[:,:,2]>=30)).mean())
    q={'brightness':round(mean,1),'contrast':round(std,1),'sharpness':round(blur,1),'foliage_fraction':round(foliage,3),
       'glare_fraction':round(clipped,3),'method':'unvalidated quality heuristic; not a leaf detector'}
    if mean<25:return 'LOW_QUALITY','Frame is too dark or the lens is covered.',q
    if mean>242 or clipped>.7:return 'LOW_QUALITY','Overexposed frame; reduce glare.',q
    if std<9:return 'LOW_QUALITY','Blank or nearly uniform frame; position a tomato leaf.',q
    if blur<12:return 'LOW_QUALITY','Blurred image; hold the leaf and camera still.',q
    return None,'Input quality is usable; crop identity and disease are not confirmed.',q

class Vision:
    def __init__(self):
        self.lock=threading.Lock();self.model=None;self.classifier=None;self.selected='hybrid';self.error='Model not loaded';self.meta={}
        self.reload(os.getenv('DEFAULT_MODEL', 'hybrid' if MODEL_FILES['detector9'].exists() else 'original'))

    def reload(self,choice):
        if choice not in (*MODEL_FILES, 'hybrid'):raise ValueError('Unknown model selection')
        if not self.lock.acquire(False):raise RuntimeError('Model busy; retry shortly')
        try:
            path=MODEL_FILES['detector9' if choice=='hybrid' else choice]
            if not path.is_file():raise ValueError('Model file is not installed')
            from ultralytics import YOLO
            import torch
            torch.set_num_threads(max(1,min(4,os.cpu_count() or 1)))
            model=YOLO(str(path));names=list(model.names.values())
            expected='detect' if choice in ('detector9','hybrid') else 'classify'
            if model.task!=expected:raise ValueError('Weight task does not match registered profile')
            if choice in ('detector9','hybrid') and {canonical(n) for n in names}!=DETECTOR_CLASSES:raise ValueError('Unexpected detector classes; refusing guessed label IDs')
            if choice not in ('detector9','hybrid') and set(names)!=(FIVE if choice=='original' else TEN):raise ValueError('Unexpected classifier classes')
            requested=os.getenv('INFERENCE_DEVICE','auto')
            device=(0 if torch.cuda.is_available() else 'cpu') if requested=='auto' else requested
            classifier=YOLO(str(MODEL_FILES['original'])) if choice=='hybrid' else None
            if classifier is not None and (classifier.task!='classify' or set(classifier.names.values())!=FIVE):raise ValueError('Preserved classifier taxonomy differs')
            self.model,self.classifier,self.selected,self.device=model,classifier,choice,device
            self.meta={'id':choice,'filename':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'classes':[canonical(n) for n in names],
                       'raw_classes':names,'task':model.task,'device':str(device),'input_size':640 if model.task=='detect' else 224,
                       'provenance':'NarimanOsman2025 / CC BY 4.0 secondary detector' if choice in ('detector9','hybrid') else 'Preserved user-trained classification model'}
            if classifier is not None:
                self.meta.update(task='two-stage', classes=[canonical(n) for n in classifier.names.values()],
                    classifier_sha256=hashlib.sha256(MODEL_FILES['original'].read_bytes()).hexdigest(),
                    classifier_file=MODEL_FILES['original'].name,
                    provenance='Actual 9-class YOLO detector boxes + preserved user 5-class YOLO classifier; experimental two-stage profile')
            self.error=None
        except Exception as exc:
            if self.model is None:self.error=f'{type(exc).__name__}: {str(exc)[:160]}'
            else:raise
        finally:self.lock.release()
        return self.state()

    def state(self):
        return {'ready':self.model is not None,'selected':self.selected,'model':dict(self.meta),'error':self.error,
                'available':(['hybrid'] if MODEL_FILES['detector9'].is_file() and MODEL_FILES['original'].is_file() else [])+[k for k,p in MODEL_FILES.items() if p.is_file()],
                'threshold':DETECTION_MIN_SCORE if self.meta.get('task') in ('detect','two-stage') else MIN_SCORE,
                'limitations':'Predicted tomato leaf-condition boxes, not lesion segmentation or confirmed diagnosis. Nutrient deficiency is not visually trained.'}

    def predict(self,frame,crop='tomato',leaf_confirmed=False,wait_s=0):
        started=time.perf_counter();status,reason,quality=assess_quality(frame)
        h,w=frame.shape[:2]
        base={'status':status,'label':None,'score':None,'quality':quality,'reason':reason,'model':dict(self.meta),'top_classes':[],
              'detections':[],'image_size':{'width':w,'height':h},'method':self.meta.get('task','none'),
              'warning':'Possible leaf condition. Model score is not diagnostic probability or disease severity.'}
        if crop!='tomato':base.update(status='UNSUPPORTED_CROP',reason=f'No trained {crop} model is installed.')
        elif status:pass
        elif self.model is None:base.update(status='MODEL_UNAVAILABLE',reason=self.error)
        elif not self.lock.acquire(timeout=max(0,min(5,wait_s))):base.update(status='BUSY',reason='Inference occupied; this frame was dropped.')
        else:
            try:
                detect=self.meta['task'] in ('detect','two-stage')
                options={'imgsz':640 if detect else 224,'device':self.device,'verbose':False}
                if detect:options.update(conf=DETECTION_MIN_SCORE,iou=.5,agnostic_nms=True,max_det=8)
                result=self.model.predict(frame,**options)[0]
                if detect:
                    for box in result.boxes:
                        cls=int(box.cls.item());score=float(box.conf.item());coords=box.xyxy[0].cpu().tolist()
                        x1,y1,x2,y2=[float(v) for v in coords]
                        x1,x2=max(0,min(w,x1)),max(0,min(w,x2));y1,y2=max(0,min(h,y1)),max(0,min(h,y2))
                        if x2<=x1 or y2<=y1:continue
                        detected=canonical(result.names[cls]);label=detected;class_score=score;disagrees=False;alternatives=[]
                        classification_input=None
                        if self.classifier is not None:
                            # A near-full-frame proposal uses the original image to avoid a harmful extra crop.
                            area=(x2-x1)*(y2-y1)/(w*h)
                            crop_frame=frame if area>=.80 else frame[int(y1):max(int(y1)+1,int(y2)),int(x1):max(int(x1)+1,int(x2))]
                            classification_input='full frame (proposal covers >=80%)' if area>=.80 else 'detected region'
                            classified=self.classifier.predict(crop_frame,imgsz=224,device=self.device,verbose=False)[0]
                            values=classified.probs.data.cpu().numpy();order=np.argsort(values)[::-1][:3]
                            alternatives=[{'label':canonical(classified.names[int(i)]),'score':round(float(values[i]),5)} for i in order]
                            class_score=alternatives[0]['score'];margin=class_score-alternatives[1]['score']
                            label=alternatives[0]['label'] if class_score>=MIN_SCORE and margin>=MIN_MARGIN else None
                            comparable='Yellow Leaf Curl Virus' if detected=='Tomato Yellow Virus' else detected
                            disagrees=bool(label and label!=comparable)
                        base['detections'].append({'id':len(base['detections'])+1,'class_id':cls,'label':label or 'Uncertain condition',
                            'raw_label':str(result.names[cls]),'score':round(class_score,5),'localization_score':round(score,5),
                            'detector_label':detected,'classifier_top_classes':alternatives,'classification_input':classification_input,
                            'review_required':bool(disagrees or not label),'models_disagree':disagrees,
                            'box':[round(x1/w,6),round(y1/h,6),round(x2/w,6),round(y2/h,6)],
                            'box_format':'normalized_xyxy','meaning':'Actual detector proposal; condition classified separately in two-stage mode. Not lesion segmentation.'})
                    base['detections'].sort(key=lambda x:-x['score'])
                    if not base['detections']:base.update(status='NO_DETECTION',reason='No supported tomato condition detected above threshold. Try a closer, well-lit single leaf; absence of boxes does not mean healthy.')
                    else:
                        best=base['detections'][0]
                        base.update(status=('LOW_CONFIDENCE' if best['label']=='Uncertain condition' else 'REVIEW' if best['review_required'] else 'OK'),
                            label=None if best['label']=='Uncertain condition' else best['label'],score=best['score'],
                            reason=f"{len(base['detections'])} YOLO region(s). "+('Models disagree; compare symptoms before accepting the class.' if best['models_disagree'] else 'Possible condition; inspect the leaf and seek confirmation.'))
                        seen=set()
                        for d in base['detections']:
                            if d['label']!='Uncertain condition' and d['label'] not in seen:base['top_classes'].append({'label':d['label'],'score':d['score']});seen.add(d['label'])
                else:
                    values=result.probs.data.cpu().numpy();indices=np.argsort(values)[::-1][:3]
                    top=[{'label':canonical(result.names[int(i)]),'score':round(float(values[i]),5)} for i in indices]
                    score,margin=top[0]['score'],top[0]['score']-top[1]['score'];base.update(score=score,top_classes=top,margin=round(margin,5))
                    if score<MIN_SCORE or margin<MIN_MARGIN:base.update(status='LOW_CONFIDENCE',reason='Ambiguous whole-image class match; no diagnosis inferred.')
                    else:base.update(status='OK',label=top[0]['label'],reason='Legacy whole-image classification; this profile cannot generate detection boxes.')
            except Exception as exc:base.update(status='INFERENCE_ERROR',reason=f'{type(exc).__name__}: local model inference failed. Open Settings for diagnostics.')
            finally:self.lock.release()
        base['latency_ms']=round((time.perf_counter()-started)*1000,1)
        return base

    @staticmethod
    def annotate(frame,prediction):
        image=frame.copy();h,w=image.shape[:2]
        for d in prediction.get('detections',[]):
            a,b,c,e=d['box'];x1,y1,x2,y2=int(a*w),int(b*h),int(c*w),int(e*h)
            cv2.rectangle(image,(x1,y1),(x2,y2),(74,230,100),max(2,round(w/700)))
            text=f"{d['label']} {d['score']:.2f}";scale=max(.42,min(.8,w/1400));(tw,th),_=cv2.getTextSize(text,cv2.FONT_HERSHEY_SIMPLEX,scale,1)
            tx=max(0,min(x1,w-tw-8));ty=max(th+9,y1)
            cv2.rectangle(image,(tx,ty-th-7),(min(w,tx+tw+7),ty+3),(74,230,100),-1)
            cv2.putText(image,text,(tx+3,ty-2),cv2.FONT_HERSHEY_SIMPLEX,scale,(8,30,12),1,cv2.LINE_AA)
        return image

vision=Vision()
