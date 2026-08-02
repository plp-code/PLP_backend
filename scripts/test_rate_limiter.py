import pytest
import os
import sys
from datetime import time


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from fastapi.testclient import TestClient
from src.python.app.main import app  

client = TestClient(app)

def test_login_rate_limit_exceeded():
    url = "/api/v1/auth/login"
    payload = {"email": "test@example.com", "password": "password123"}

    for _ in range(5):
        response = client.post(url, json=payload)
        assert response.status_code != 429

    blocked_response = client.post(url, json=payload)
    assert blocked_response.status_code == 429
    assert blocked_response.json() == {"detail": "Too many requests. Please try again later."}
    assert "retry-after" in blocked_response.headers


def test_docs_exempt_from_rate_limit():
    for _ in range(10):
        response = client.get("/docs")
        assert response.status_code == 200