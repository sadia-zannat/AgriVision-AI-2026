"""Read-only local diagnostics; never prints API keys."""
import sys
import hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.vision import vision
import torch
print('Python:',sys.version.split()[0]);print('PyTorch:',torch.__version__);print('CUDA available:',torch.cuda.is_available())
if torch.cuda.is_available():print('GPU:',torch.cuda.get_device_name(0))
print('Model:',vision.state())
original=Path(__file__).resolve().parents[1]/'models/tomato_best.pt'
print('Original SHA256:',hashlib.sha256(original.read_bytes()).hexdigest())
print('No camera is opened by this check. Use the browser device selector for physical verification.')

expected='d3e816f6d02cd74f3d4b0fd6d756b8bcd93a7efefd9c41920f30a02af3bf3007'
if not vision.state()['ready']:
    raise SystemExit('Model failed to load. Read the model error above; setup is incomplete.')
if hashlib.sha256(original.read_bytes()).hexdigest()!=expected:
    raise SystemExit('Preserved model hash differs. Keep a backup and restore the supplied original weights.')
