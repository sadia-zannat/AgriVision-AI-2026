"""Optional training and guarded final test. Original tomato_best.pt is never a destination."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,default=ROOT/'datasets/tomato_10class');p.add_argument('--epochs',type=int,default=30);p.add_argument('--batch',type=int,default=16);p.add_argument('--device',default='auto');p.add_argument('--final-evaluate',action='store_true');a=p.parse_args()
    from ultralytics import YOLO
    import torch
    from prepare_tomato_10class import CLASSES
    data=a.data.resolve();out=ROOT/'models/tomato_10class_best.pt'
    if not (data/'manifest.json').is_file():raise SystemExit('Run the audited preparation script first.')
    if {d.name for d in (data/'train').iterdir() if d.is_dir()}!=set(CLASSES):raise SystemExit('Ten-class audit failed')
    manifest=data/'manifest.json';manifest_hash=hashlib.sha256(manifest.read_bytes()).hexdigest()
    device=(0 if torch.cuda.is_available() else 'cpu') if a.device=='auto' else a.device
    if not a.final_evaluate:
        if out.exists():raise SystemExit('Expanded model already exists. Archive it yourself before a new training run; never overwrite the original.')
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        model=YOLO(str(ROOT/'models/tomato_best.pt'))
        model.train(data=str(data),epochs=a.epochs,batch=a.batch,imgsz=224,device=device,workers=0,seed=2026,
                    deterministic=True,project=str(ROOT/'runs'),name='tomato10_'+stamp,patience=7,plots=True)
        best=Path(model.trainer.best)
        if not best.is_file():raise SystemExit('No trained best weights created')
        shutil.copy2(best,out)
        (ROOT/'models/tomato_10class_provenance.json').write_text(json.dumps({'created_utc':stamp,'classes':CLASSES,'data_manifest_sha256':manifest_hash,
            'training_device':str(device),'seed':2026,'epochs_max':a.epochs,'source':'Project-AgML/tomato_leaf_disease or explicitly supplied --data',
            'initial_weights':'tomato_best.pt','best_weights_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'test_evaluated':False},indent=2),encoding='utf-8')
        print('Training complete. Inspect validation results. Run --final-evaluate ONCE only after all choices are frozen.')
        return
    if not out.exists():raise SystemExit('Train the expanded model first')
    marker=data/'FINAL_TEST_ALREADY_USED.json'
    if marker.exists():raise SystemExit('Final test already used. Do not tune on this test. Obtain a new independent evaluation dataset.')
    provenance=json.loads((ROOT/'models/tomato_10class_provenance.json').read_text())
    if provenance['data_manifest_sha256']!=manifest_hash:raise SystemExit('Manifest changed since training')
    # Exclusive sentinel before reading test. A failed run remains recorded for audit.
    with marker.open('x',encoding='utf-8') as f:json.dump({'started_utc':datetime.now(timezone.utc).isoformat(),'state':'started; test considered used'},f)
    model=YOLO(str(out));classes=model.names;matrix=[[0]*len(classes) for _ in classes];n=0
    lookup={name:int(i) for i,name in classes.items()}
    for folder in sorted((data/'test').iterdir()):
        if not folder.is_dir():continue
        true=lookup[folder.name]
        files=sorted(p for p in folder.iterdir() if p.suffix.lower() in {'.jpg','.jpeg','.png','.webp'})
        for result in model.predict(source=[str(p) for p in files],imgsz=224,device=device,stream=True,verbose=False):
            predicted=int(result.probs.top1);matrix[true][predicted]+=1;n+=1
    report={'test_count':n,'top1':sum(matrix[i][i] for i in range(len(classes)))/max(1,n),'classes':classes,'confusion_matrix':matrix,
            'per_class_recall':{classes[i]:matrix[i][i]/max(1,sum(matrix[i])) for i in range(len(classes))},'data_manifest_sha256':manifest_hash,
            'warning':'Same-source test only; not field accuracy. Do not tune after viewing this result.'}
    (data/'FINAL_TEST_REPORT.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(11,9));ax.imshow(matrix,cmap='Greens');ax.set_xticks(range(len(classes)),classes.values(),rotation=90);ax.set_yticks(range(len(classes)),classes.values());ax.set_xlabel('Predicted');ax.set_ylabel('True');fig.tight_layout();fig.savefig(data/'FINAL_TEST_CONFUSION_MATRIX.png',dpi=150);plt.close(fig)
    provenance['test_evaluated']=True;(ROOT/'models/tomato_10class_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
