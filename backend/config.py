from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)
DATA = Path(os.getenv('APP_DATA_DIR', str(ROOT / 'artifacts'))).resolve()
for folder in ('evidence', 'uploads', 'recordings', 'logs'):
    (DATA / folder).mkdir(parents=True, exist_ok=True)
DB = DATA / 'agrivision.db'
MAX_IMAGE = 10 * 1024 * 1024
MAX_DOCUMENT = 8 * 1024 * 1024
MAX_RECORDING = 120 * 1024 * 1024
STORAGE_BUDGET = int(os.getenv('STORAGE_BUDGET_MB', '1024')) * 1024 * 1024
MAX_RECORD_SECONDS = min(600, max(10, int(os.getenv('MAX_RECORD_SECONDS', '120'))))
ALLOWED_HOSTS = [v.strip() for v in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1],testserver').split(',') if v.strip()]
MODEL_FILES = {'detector9': ROOT / 'models/tomato_detector_9class.pt', 'original': ROOT / 'models/tomato_best.pt', 'expanded': ROOT / 'models/tomato_10class_best.pt'}
MIN_SCORE = min(.99, max(.5, float(os.getenv('MIN_MODEL_SCORE', '.75'))))
MIN_MARGIN = min(.5, max(0, float(os.getenv('MIN_SCORE_MARGIN', '.15'))))

DETECTION_MIN_SCORE = min(.95, max(.1, float(os.getenv('DETECTION_MIN_SCORE', '.40'))))
