import os
os.environ.setdefault("API_KEYS", "test-secret")
os.environ.setdefault("RATE_LIMIT_REQUESTS", "100")
os.environ.setdefault("RATE_LIMIT_WINDOW_SECONDS", "60")

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def auth_headers():
    return {"X-API-Key": "test-secret"}
