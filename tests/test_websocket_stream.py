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
        labels=["APPROVE", "REJECT"],
        default_label="APPROVE",
        default_confidence=0.98
    )
    app = create_app(engine=mock_engine, max_context=20)
    return TestClient(app)

def test_websocket_stream_decide(client):
    with client.websocket_connect("/v1/stream/decide") as ws:
        for i in range(3):
            req_id = f"loop-{i}"
            payload = {
                "id": req_id,
                "input": f"Order payload #{i}",
                "on_overflow": "error"
            }
            ws.send_text(json.dumps(payload))
            raw_response = ws.receive_text()
            data = json.loads(raw_response)
            
            assert data["id"] == req_id
            assert data["label"] == "APPROVE"
            assert data["confidence"] == 0.98
            assert "probabilities" in data
            assert "latency_ms" in data
