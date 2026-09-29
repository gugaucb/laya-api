import pytest
from fastapi.testclient import TestClient
from laya_api.server import create_app
from laya_api.engine import MockEngine

@pytest.fixture
def client():
    mock_engine = MockEngine(
        model_name="laya-base",
        backend="mock",
        labels=["low_risk", "high_risk", "invalid"],
        default_label="low_risk",
        default_confidence=0.985
    )
    app = create_app(engine=mock_engine, max_context=10)
    return TestClient(app)

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model"] == "laya-base"
    assert data["backend"] == "mock"

def test_native_decide_endpoint_success(client):
    payload = {
        "input": "Short transaction text",
        "on_overflow": "error"
    }
    response = client.post("/v1/decide", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "low_risk"
    assert data["confidence"] == 0.985
    assert "probabilities" in data
    assert data["probabilities"]["low_risk"] == 0.985
    assert "latency_ms" in data
    assert data["backend"] == "mock"
    assert response.headers["X-Laya-Backend"] == "mock"
    assert "X-Laya-Latency-Ms" in response.headers

def test_native_decide_context_overflow_error(client):
    payload = {
        "input": "word " * 20,
        "on_overflow": "error"
    }
    response = client.post("/v1/decide", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "context_length_exceeded"
    assert data["error"]["type"] == "invalid_request_error"
    assert data["error"]["details"]["max_context_length"] == 10

def test_native_decide_context_overflow_with_truncation(client):
    payload = {
        "input": "word " * 20,
        "on_overflow": "truncate_tail"
    }
    response = client.post("/v1/decide", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "low_risk"
    assert data["tokens"] == 10
