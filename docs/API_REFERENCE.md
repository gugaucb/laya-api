# Laya API Reference

All responses and server error messages are returned in **English**.

---

## 1. OpenAI Compatibility (`/v1/chat/completions`)

### Endpoint
`POST /v1/chat/completions`

### Request Headers
- `Content-Type: application/json`
- `Authorization: Bearer <optional-api-key>`

### Request Body
```json
{
  "model": "laya-base",
  "messages": [
    {
      "role": "user",
      "content": "Evaluate trading risk for order #4928: amount 5000 USDT on pair BTC/USDT."
    }
  ],
  "stream": false,
  "logprobs": true,
  "top_logprobs": 5,
  "extra_body": {
    "on_overflow": "error"
  }
}
```

### Response (`200 OK`)
```json
{
  "id": "chatcmpl-laya-9f8a7b6c5d4e",
  "object": "chat.completion",
  "created": 1774892400,
  "model": "laya-base",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "{\"decision\": \"APPROVED\", \"confidence\": 0.9842, \"label\": \"low_risk\"}"
      },
      "logprobs": {
        "content": [
          {
            "token": "APPROVED",
            "logprob": -0.0159,
            "top_logprobs": [
              { "token": "APPROVED", "logprob": -0.0159 },
              { "token": "REJECTED", "logprob": -4.1420 },
              { "token": "MANUAL_REVIEW", "logprob": -5.8201 }
            ]
          }
        ]
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 28,
    "completion_tokens": 1,
    "total_tokens": 29
  },
  "decision_meta": {
    "predicted_label": "low_risk",
    "probability": 0.9842,
    "probabilities": {
      "low_risk": 0.9842,
      "high_risk": 0.0157,
      "invalid": 0.0001
    }
  }
}
```

### Response Headers
- `X-Laya-Latency-Ms: 8.42`
- `X-Laya-Backend: mlx`
- `X-Laya-Model: laya-base`

---

## 2. Anthropic Compatibility (`/v1/messages`)

### Endpoint
`POST /v1/messages`

### Request Headers
- `Content-Type: application/json`
- `x-api-key: <optional-api-key>`
- `anthropic-version: 2023-06-01`

### Request Body
```json
{
  "model": "laya-base",
  "max_tokens": 1024,
  "messages": [
    {
      "role": "user",
      "content": "Is this email phishing: 'Your account is suspended, click here to verify.'"
    }
  ],
  "stream": false
}
```

### Response (`200 OK`)
```json
{
  "id": "msg_laya_8e7d6c5b4a",
  "type": "message",
  "role": "assistant",
  "model": "laya-base",
  "content": [
    {
      "type": "text",
      "text": "{\"decision\": \"PHISHING\", \"confidence\": 0.9991, \"label\": \"malicious\"}"
    }
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 21,
    "output_tokens": 1
  }
}
```

---

## 3. High-Performance Native Endpoint (`/v1/decide`)

Designed for maximum throughput, supporting both single-label and multi-question structured evaluations (see [Payload Formats & Question Types Specification](PAYLOAD_FORMATS.md)).

### Endpoint
`POST /v1/decide`

### Multi-Question Structured Request Body
```json
{
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
  },
  "on_overflow": "error"
}
```

### Multi-Question Response (`200 OK`)
```json
{
  "results": {
    "department": {
      "decision": "billing",
      "confidence": 0.994,
      "probabilities": {
        "billing": 0.994,
        "sales": 0.004,
        "technical": 0.002
      }
    },
    "urgency": {
      "decision": "soon",
      "confidence": 0.928,
      "level": 1,
      "probabilities": {
        "not urgent": 0.032,
        "soon": 0.928,
        "critical": 0.040
      }
    },
    "refund": {
      "decision": true,
      "confidence": 0.999,
      "probabilities": {
        "true": 0.999,
        "false": 0.001
      }
    }
  },
  "tokens": 42,
  "latency_ms": 7.85,
  "backend": "mlx",
  "model": "laya-base"
}
```

### Simple Request Body (Legacy Single-Label)
```json
{
  "input": "User transaction details or text payload",
  "model": "laya-base",
  "on_overflow": "error"
}
```

### Response (`200 OK`)
```json
{
  "label": "approved",
  "confidence": 0.9945,
  "probabilities": {
    "approved": 0.9945,
    "flagged": 0.0055
  },
  "tokens": 18,
  "latency_ms": 7.15,
  "backend": "mlx"
}
```

---

## 4. Persistent WebSocket Stream (`/v1/stream/decide`)

Ideal for tight execution loops (e.g., trading bots, live content filters). Avoids repeated connection negotiation.

### Connection
`ws://localhost:8000/v1/stream/decide`

### Client Message (JSON)
```json
{
  "id": "req-101",
  "input": "Order book snapshot payload...",
  "on_overflow": "truncate_head"
}
```

### Server Message (JSON)
```json
{
  "id": "req-101",
  "label": "EXECUTE_BUY",
  "confidence": 0.978,
  "probabilities": {
    "EXECUTE_BUY": 0.978,
    "HOLD": 0.021,
    "EXECUTE_SELL": 0.001
  },
  "latency_ms": 6.82
}
```

---

## 5. Unix Domain Socket (UDS) Usage

When client and server run on the same physical machine, connect via Unix Domain Socket:

```bash
# Start server with UDS socket
laya-api serve --socket /tmp/laya.sock
```

### Python Client Example (`httpx`)
```python
import httpx

transport = httpx.HTTPTransport(uds="/tmp/laya.sock")
with httpx.Client(transport=transport, base_url="http://localhost") as client:
    resp = client.post("/v1/decide", json={"input": "test payload"})
    print(resp.json())
```

---

## 6. Error Responses

Errors follow standard HTTP status codes and OpenAI error JSON schema.

### Context Length Exceeded (`400 Bad Request`)
```json
{
  "error": {
    "message": "Input token count (1280) exceeds model context window limit (1024 tokens). Configure 'on_overflow' parameter to 'truncate_head' or 'truncate_tail' to allow automatic truncation.",
    "type": "invalid_request_error",
    "param": "messages",
    "code": "context_length_exceeded",
    "details": {
      "token_count": 1280,
      "max_context_length": 1024
    }
  }
}
```

### Model Not Found (`404 Not Found`)
```json
{
  "error": {
    "message": "Model 'unknown-model' is not loaded. Available models: ['laya-base'].",
    "type": "invalid_request_error",
    "param": "model",
    "code": "model_not_found"
  }
}
```
