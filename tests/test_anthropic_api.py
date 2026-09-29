import json
import pytest
from fastapi.testclient import TestClient
from laya_api.server import create_app
from laya_api.engine import MockEngine

@pytest.fixture
def client():
    mock_engine = MockEngine(
        model_name="laya-base",
        backend="mock",
        labels=["phishing", "safe"],
        default_label="phishing",
        default_confidence=0.999
    )
    app = create_app(engine=mock_engine, max_context=15)
    return TestClient(app)

def test_anthropic_messages_sync(client):
    payload = {
        "model": "laya-base",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Is this email malicious?"}
        ],
        "stream": False
    }
    response = client.post("/v1/messages", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["type"] == "message"
    assert data["role"] == "assistant"
    assert data["stop_reason"] == "end_turn"
    assert len(data["content"]) == 1
    assert data["content"][0]["type"] == "text"
    
    content_obj = json.loads(data["content"][0]["text"])
    assert content_obj["label"] == "phishing"
    assert content_obj["confidence"] == 0.999
    
    assert "usage" in data
    assert data["usage"]["input_tokens"] > 0
    assert data["usage"]["output_tokens"] == 1

def test_anthropic_messages_stream(client):
    payload = {
        "model": "laya-base",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Quick test"}
        ],
        "stream": True
    }
    response = client.post("/v1/messages", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    lines = [line.strip() for line in response.text.split("\n") if line.strip()]
    events = [l for l in lines if l.startswith("event:")]
    assert "event: message_start" in events
    assert "event: message_stop" in events

def test_anthropic_messages_context_overflow(client):
    payload = {
        "model": "laya-base",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "word " * 30}
        ],
        "stream": False
    }
    response = client.post("/v1/messages", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "context_length_exceeded"
