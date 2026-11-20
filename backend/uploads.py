import io
import uuid
import warnings
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError
import cv2
import numpy as np
from fastapi import HTTPException
from .config import DATA, MAX_IMAGE, MAX_DOCUMENT, STORAGE_BUDGET
from . import storage

Image.MAX_IMAGE_PIXELS = 16_000_000

def room_for(size):
    used = sum(p.stat().st_size for folder in ('evidence', 'uploads', 'recordings') for p in (DATA / folder).iterdir() if p.is_file())
    if used + size > STORAGE_BUDGET: raise HTTPException(507, 'Storage limit reached. Back up and remove old artifacts before retrying.')

async def read_limited(file, maximum):
    data = await file.read(maximum + 1)
    if len(data) > maximum: raise HTTPException(413, f'File exceeds {maximum // (1024*1024)} MB limit')
    if not data: raise HTTPException(400, 'Empty attachment')
    return data

def decode_image(data):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as im:
                if im.format not in ('JPEG', 'PNG', 'WEBP'): raise ValueError('Use JPEG, PNG or WEBP')
                if im.width * im.height > 16_000_000 or min(im.size) < 64: raise ValueError('Image must be at least 64px and at most 16 megapixels')
                im = ImageOps.exif_transpose(im).convert('RGB')
                im.thumbnail((1920, 1920))
                out = io.BytesIO(); im.save(out, format='JPEG', quality=92)
                return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR), out.getvalue()
    except Exception:
        raise HTTPException(415, 'Invalid image. Use a readable JPG/PNG/WEBP (64px–16MP).')

async def store_attachment(file):
    name = Path((file.filename or 'attachment').replace('\\', '/')).name[:160]
    ext = Path(name).suffix.lower()
    aid = uuid.uuid4().hex
    text = ''
    if ext in ('.jpg', '.jpeg', '.png', '.webp'):
        raw = await read_limited(file, MAX_IMAGE)
        _, data = decode_image(raw)
        mime, stored = 'image/jpeg', aid + '.jpg'
    elif ext in ('.txt', '.csv', '.pdf'):
        data = await read_limited(file, MAX_DOCUMENT)
        if ext == '.pdf':
            try:
                import fitz
                with fitz.open(stream=data, filetype='pdf') as doc:
                    if doc.needs_pass: raise ValueError('Encrypted PDF')
                    text = '\n'.join(f'[Page {i+1}] {doc[i].get_text()}' for i in range(min(20, len(doc))))[:20000]
                mime = 'application/pdf'
            except Exception: raise HTTPException(415, 'Unreadable or encrypted PDF; use TXT instead.')
        else:
            try:
                text = data.decode('utf-8-sig')
                if '\x00' in text: raise ValueError()
                text = text[:20000]
            except (UnicodeDecodeError, ValueError): raise HTTPException(415, 'Use UTF-8 text or CSV, not binary data.')
            mime = 'text/plain' if ext == '.txt' else 'text/csv'
        stored = aid + ext
    else: raise HTTPException(415, 'Supported attachments: JPG, PNG, WEBP, PDF, TXT, CSV')
    room_for(len(data))
    (DATA / 'uploads' / stored).write_bytes(data)
    a = {'id': aid, 'name': name, 'mime': mime, 'size': len(data)}
    storage.save_attachment(a, stored, text)
    return storage.public_attachment(dict(a, text_content=text))
