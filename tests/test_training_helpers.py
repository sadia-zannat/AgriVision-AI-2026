import sys
from pathlib import Path
import pytest
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_tomato_10class import resolve_label, BKTree, fingerprints, prepare

def test_strict_taxonomy_does_not_merge_speck_or_other_crop():
    assert resolve_label('Tomato___Tomato_Yellow_Leaf_Curl_Virus')=='Yellow_Leaf_Curl_Virus'
    assert resolve_label('Spider_mites Two-spotted_spider_mite')=='Spider_Mites'
    with pytest.raises(ValueError):resolve_label('Bacterial_speck')
    with pytest.raises(ValueError):resolve_label('Rice___healthy')

def test_reencoded_exact_pixels_and_near_duplicate_lookup(tmp_path):
    arr=np.random.default_rng(4).integers(0,255,(80,80,3),dtype=np.uint8)
    for name,compress in [('a.png',1),('b.png',9)]:Image.fromarray(arr).save(tmp_path/name,compress_level=compress)
    assert fingerprints(tmp_path/'a.png')[0]==fingerprints(tmp_path/'b.png')[0]
    tree=BKTree();tree.add(0b1111,1);tree.add(0b1101,2);tree.add(0xFFFFFFFFFFFFFFFF,3)
    assert sorted(tree.within(0b1111,1))==[1,2]

def test_preparation_refuses_overwrite(tmp_path):
    out=tmp_path/'existing';out.mkdir();sentinel=out/'keep.txt';sentinel.write_text('keep')
    with pytest.raises(ValueError,match='already exists'):prepare(tmp_path/'raw',out)
    assert sentinel.read_text()=='keep'


def test_preparation_group_split_with_synthetic_ten_class_fixture(tmp_path):
    from prepare_tomato_10class import CLASSES
    import json
    raw=tmp_path/'raw';rng=np.random.default_rng(99)
    for label in CLASSES:
        folder=raw/label;folder.mkdir(parents=True)
        for i in range(12):
            Image.fromarray(rng.integers(0,255,(64,64,3),dtype=np.uint8)).save(folder/f'{i}.png')
    duplicate=raw/CLASSES[0]/'duplicate.png'
    with Image.open(raw/CLASSES[0]/'0.png') as im:im.save(duplicate,compress_level=9)
    out=tmp_path/'split';audit=prepare(raw,out)
    rows=json.loads((out/'manifest.json').read_text());groups={}
    for row in rows:groups.setdefault(row['group_id'],set()).add(row['split'])
    assert all(len(splits)==1 for splits in groups.values())
    assert audit['raw_count']==121 and audit['retained_count']==120
    assert {r['split'] for r in rows}=={'train','val','test'}
