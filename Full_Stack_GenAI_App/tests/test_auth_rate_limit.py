from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.rate_limiter import RateLimiter


def test_ask_requires_api_key(client):
    response = client.post("/ask", json={"query": "hello", "mode": "rag", "top_k": 2})
    assert response.status_code == 401


def test_invalid_api_key_rejected(client):
    response = client.post("/ask", headers={"X-API-Key": "wrong"}, json={
        "query": "hello there, please search", "mode": "rag", "top_k": 2
    })
    assert response.status_code == 401


def test_rate_limiter_tracks_each_key_separately():
    limiter = RateLimiter(limit=1, window_seconds=60)
    allowed_a, _, _ = limiter.check("key-a")
    blocked_a, retry, count = limiter.check("key-a")
    allowed_b, _, _ = limiter.check("key-b")
    assert allowed_a is True
    assert blocked_a is False
    assert retry >= 1
    assert count == 1
    assert allowed_b is True
