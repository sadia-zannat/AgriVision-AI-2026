"""Optional data export + exact/perceptual group split. Never touches original datasets/weights."""
import argparse
import hashlib
import json
import os
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ['Bacterial_Spot','Early_Blight','Healthy','Late_Blight','Leaf_Mold','Septoria_Leaf_Spot',
           'Spider_Mites','Target_Spot','Tomato_Mosaic_Virus','Yellow_Leaf_Curl_Virus']
ALIASES = {
 'bacterialspot':'Bacterial_Spot','earlyblight':'Early_Blight','healthy':'Healthy','lateblight':'Late_Blight',
 'leafmold':'Leaf_Mold','septorialeafspot':'Septoria_Leaf_Spot','spidermitestwospottedspidermite':'Spider_Mites',
 'spidermites':'Spider_Mites','targetspot':'Target_Spot','tomatomosaicvirus':'Tomato_Mosaic_Virus',
 'mosaicvirus':'Tomato_Mosaic_Virus','tomatoyellowleafcurlvirus':'Yellow_Leaf_Curl_Virus','yellowleafcurlvirus':'Yellow_Leaf_Curl_Virus'}

def resolve_label(value):
    name = ''.join(c.lower() for c in value if c.isalpha())
    if name.startswith('tomato') and name not in ALIASES: name = name[6:]
    if name not in ALIASES: raise ValueError('Unknown dataset label: ' + value)
    return ALIASES[name]

def fingerprints(path):
    with Image.open(path) as original:
        im = ImageOps.exif_transpose(original).convert('RGB')
        exact = hashlib.sha256(str(im.size).encode() + im.tobytes()).hexdigest()
        import numpy as np
        tiny = np.array(im.convert('L').resize((9,8), Image.Resampling.LANCZOS))
        bits = (tiny[:,1:] > tiny[:,:-1]).flatten()
        dh = 0
        for bit in bits: dh = (dh << 1) | int(bit)
        return exact, dh

class BKTree:
    def __init__(self): self.root = None
    def add(self, value, index):
        if self.root is None: self.root = [value,[index],{}]; return
        node=self.root
        while True:
            distance=(node[0]^value).bit_count()
            if distance==0: node[1].append(index);return
            if distance not in node[2]:node[2][distance]=[value,[index],{}];return
            node=node[2][distance]
    def within(self, value, maximum):
        if self.root is None:return []
        result=[];stack=[self.root]
        while stack:
            node=stack.pop();d=(node[0]^value).bit_count()
            if d<=maximum:result.extend(node[1])
            stack.extend(child for distance,child in node[2].items() if d-maximum<=distance<=d+maximum)
        return result

def prepare(raw, out, seed=2026, distance=4):
    if out.exists():raise ValueError('Output already exists. Use a NEW --output directory; no data is overwritten.')
    rows=[]; skipped=[]
    for path in sorted(raw.rglob('*')):
        if path.suffix.lower() not in {'.jpg','.jpeg','.png','.webp'}:continue
        try:
            label=resolve_label(path.parent.name);exact,dh=fingerprints(path)
            rows.append({'path':str(path.resolve()),'class':label,'pixel_sha256':exact,'dhash':dh,'file_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        except Exception as exc: skipped.append({'file':str(path),'error':str(exc)})
    if not rows:raise ValueError('No valid labelled images. --raw must contain ten named class folders.')
    parents=list(range(len(rows)))
    def find(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    def union(a,b):parents[find(a)]=find(b)
    tree=BKTree();exact_seen={}
    for i,row in enumerate(rows):
        key=row['pixel_sha256']
        if key in exact_seen:union(i,exact_seen[key])
        else:exact_seen[key]=i
        for j in tree.within(row['dhash'],distance):union(i,j)
        tree.add(row['dhash'],i)
    groups=defaultdict(list)
    for i,row in enumerate(rows):groups[find(i)].append(row)
    byclass=defaultdict(list);conflicts=[]
    for group in groups.values():
        if len({r['class'] for r in group})!=1:conflicts.extend(group);continue
        byclass[group[0]['class']].append(group)
    if set(byclass)!=set(CLASSES):raise ValueError('Not all ten verified classes remain after conflict filtering: '+str(sorted(byclass)))
    if any(len(g)<10 for g in byclass.values()):raise ValueError('Need at least ten distinct image groups per class for a meaningful split.')
    out.mkdir(parents=True);rng=random.Random(seed);manifest=[]
    for label in sorted(byclass):
        groups_for_class=byclass[label];rng.shuffle(groups_for_class)
        n=len(groups_for_class);nt=max(1,round(n*.1));nv=max(1,round(n*.1))
        assignment=[('test',groups_for_class[:nt]),('val',groups_for_class[nt:nt+nv]),('train',groups_for_class[nt+nv:])]
        for split,part in assignment:
            seen=set()
            for group in part:
                group_id=hashlib.sha256(''.join(sorted(r['pixel_sha256'] for r in group)).encode()).hexdigest()[:16]
                for row in group:
                    if row['pixel_sha256'] in seen:continue
                    seen.add(row['pixel_sha256']);target=out/split/label/(row['file_sha256'][:24]+Path(row['path']).suffix.lower())
                    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(row['path'],target)
                    manifest.append(dict(row,split=split,group_id=group_id,destination=str(target.relative_to(out))))
    audit={'seed':seed,'near_duplicate_hamming_threshold':distance,'raw_count':len(rows),'exact_unique':len(exact_seen),
           'retained_count':len(manifest),'class_split_counts':dict(Counter(r['class']+'/'+r['split'] for r in manifest)),
           'skipped':skipped,'cross_class_conflicts_quarantined':len(conflicts),
           'limitations':'dHash catches some near duplicates, not all augmentations, plant identities or shared-source leakage. External field evaluation remains necessary.'}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (out/'audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    (out/'quarantined.json').write_text(json.dumps(conflicts,indent=2),encoding='utf-8')
    return audit

def export_hf(raw, offline=False, revision='main'):
    if raw.exists():raise ValueError('Raw export exists. Reuse it with --raw, or select a new export directory.')
    if offline:os.environ['HF_DATASETS_OFFLINE']='1';os.environ['HF_HUB_OFFLINE']='1'
    from datasets import load_dataset, ClassLabel
    ds=load_dataset('Project-AgML/tomato_leaf_disease',revision=revision,split='train',download_mode='reuse_dataset_if_exists')
    feature=ds.features.get('label')
    if not isinstance(feature,ClassLabel):raise ValueError('Expected a verified ClassLabel; refusing to guess class IDs')
    mapping={i:resolve_label(n) for i,n in enumerate(feature.names)}
    if set(mapping.values())!=set(CLASSES):raise ValueError('Dataset scope changed; inspect labels before training')
    raw.mkdir(parents=True)
    for i,row in enumerate(ds):
        folder=raw/mapping[int(row['label'])];folder.mkdir(exist_ok=True)
        row['image'].convert('RGB').save(folder/f'hf_{i:06d}.png')
    provenance={'dataset':'Project-AgML/tomato_leaf_disease','url':'https://huggingface.co/datasets/Project-AgML/tomato_leaf_disease',
                'requested_revision':revision,'hf_fingerprint':ds._fingerprint,'rows':len(ds),'labels':feature.names,
                'mirror_license':'cc0-1.0 per mirror card; independently check upstream redistribution terms',
                'primary_data_collected_by_this_team':False}
    (raw/'source.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=ROOT/'datasets/tomato_10class_raw');p.add_argument('--output',type=Path,default=ROOT/'datasets/tomato_10class')
    p.add_argument('--download-hf',action='store_true');p.add_argument('--offline',action='store_true');p.add_argument('--revision',default='main');p.add_argument('--seed',type=int,default=2026)
    a=p.parse_args()
    if a.download_hf:export_hf(a.raw,a.offline,a.revision)
    print(json.dumps(prepare(a.raw,a.output,a.seed),indent=2))
