import os
import sys
import tempfile
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
_TEMP=tempfile.TemporaryDirectory(prefix='agrivision_test_')
os.environ['APP_DATA_DIR']=_TEMP.name
os.environ['CHAT_PROVIDER_ORDER']='offline'
os.environ['ALLOWED_HOSTS']='localhost,127.0.0.1,testserver'
from backend.app import app
from fastapi.testclient import TestClient

@pytest.fixture(scope='session')
def client():
    with TestClient(app) as c:yield c

@pytest.fixture
def headers():return {'x-agrivision-request':'1'}

@pytest.fixture
def leaf():return (ROOT/'tests/assets/QA_TEST_KSTATE_EARLY_BLIGHT_NOT_LIVE.jpg').read_bytes()
