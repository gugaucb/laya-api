import json
import pytest
from fastapi.testclient import TestClient
from laya_api.server import create_app
from laya_api.engine import MockEngine

@pytest.fixture
def client():
    mock_engine = MockEngine(
        model_name="laya-base",
        backend="mock"
    )
    app = create_app(engine=mock_engine, max_context=100)
    return TestClient(app)

def test_multi_question_structured_decide(client):
    payload = {
        "input": "I was billed twice. Please refund the duplicate today.",
        "questions": {
            "department": {
                "type": "choice",
                "instructions": "Which team should handle this request?",
                "criteria": {
                    "billing": "invoices, payments, refunds",
                    "technical": "bugs and outages",
                    "sales": "new purchases"
                }
            },
            "urgency": {
                "type": "score",
                "instructions": "How urgent is this request?",
                "criteria": ["not urgent", "soon", "critical"]
            },
            "refund": {
                "type": "noul",
                "instructions": "Does the customer ask for money back?"
            }
        }
    }
    response = client.post("/v1/decide", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "results" in data
    results = data["results"]
    assert "department" in results
    assert "urgency" in results
    assert "refund" in results
    
    # department evaluation
    assert results["department"]["decision"] in ["billing", "technical", "sales"]
    assert results["department"]["confidence"] > 0.0
    
    # urgency evaluation
    assert results["urgency"]["decision"] in ["not urgent", "soon", "critical"]
    assert "level" in results["urgency"]
    
    # refund evaluation
    assert isinstance(results["refund"]["decision"], bool)
    assert results["refund"]["confidence"] > 0.0

def test_multi_question_openai_chat_completions(client):
    payload = {
        "model": "laya-base",
        "messages": [
            {"role": "user", "content": "I was billed twice. Please refund the duplicate today."}
        ],
        "extra_body": {
            "questions": {
                "department": {
                    "type": "choice",
                    "criteria": {"billing": "refunds", "technical": "bugs"}
                },
                "refund": {
                    "type": "noul"
                }
            }
        }
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    data = response.json()
    content_obj = json.loads(data["choices"][0]["message"]["content"])
    assert "department" in content_obj
    assert "refund" in content_obj
