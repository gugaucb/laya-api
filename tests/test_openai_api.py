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
        labels=["low_risk", "high_risk"],
        default_label="low_risk",
        default_confidence=0.99
    )
    app = create_app(engine=mock_engine, max_context=15)
    return TestClient(app)

def test_openai_chat_completions_sync(client):
    payload = {
        "model": "laya-base",
        "messages": [
            {"role": "system", "content": "You are a risk evaluator."},
            {"role": "user", "content": "Evaluate transaction #1234"}
        ],
        "logprobs": True,
        "top_logprobs": 2,
        "stream": False
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["object"] == "chat.completion"
    assert data["model"] == "laya-base"
    assert len(data["choices"]) == 1
    
    choice = data["choices"][0]
    assert choice["finish_reason"] == "stop"
    assert choice["message"]["role"] == "assistant"
    
    # Message content contains serialized JSON decision
    content_obj = json.loads(choice["message"]["content"])
    assert content_obj["label"] == "low_risk"
    assert content_obj["confidence"] == 0.99
    
    # Usage metrics
    assert "usage" in data
    assert data["usage"]["prompt_tokens"] > 0
    assert data["usage"]["completion_tokens"] == 1
    
    # Custom decision metadata
    assert "decision_meta" in data
    assert data["decision_meta"]["predicted_label"] == "low_risk"
    
    # Headers
    assert "X-Laya-Latency-Ms" in response.headers
    assert response.headers["X-Laya-Backend"] == "mock"

def test_openai_chat_completions_stream(client):
    payload = {
        "model": "laya-base",
        "messages": [
            {"role": "user", "content": "Quick check"}
        ],
        "stream": True
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    
    lines = [line.strip() for line in response.text.split("\n") if line.strip()]
    data_lines = [l for l in lines if l.startswith("data:")]
    assert len(data_lines) >= 2
    assert data_lines[-1] == "data: [DONE]"
    
    # First chunk should have content
    first_chunk_json = json.loads(data_lines[0].replace("data: ", ""))
    assert first_chunk_json["object"] == "chat.completion.chunk"
    assert "content" in first_chunk_json["choices"][0]["delta"]

def test_openai_chat_completions_context_overflow(client):
    payload = {
        "model": "laya-base",
        "messages": [
            {"role": "user", "content": "word " * 30}
        ],
        "stream": False
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "context_length_exceeded"
