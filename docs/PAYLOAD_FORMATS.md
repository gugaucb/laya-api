# Laya API: Payload Formats & Question Types Specification

This specification defines the structured payload format and supported **Question Types** for evaluating multi-dimensional judgments in a single forward pass with Laya models.

---

## 1. Anatomy of a Structured Decision Request

A structured evaluation request contains two primary elements:
1. **`input`**: The raw text, email, user prompt, customer ticket, or JSON object to be evaluated.
2. **`questions`**: A dictionary where each key is an identifier (e.g., `department`, `urgency`, `is_fraud`) and the value defines the evaluation criteria and question type.

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

---

## 2. Supported Question Types

### 🏷️ 1. `choice` (Multi-Class Categorical Decision)
Used for classification, routing, and intent detection among discrete options.

- **`instructions`** *(string)*: Clear question or criteria description.
- **`criteria`** *(object or list)*:
  - **Object form (Recommended)**: Key is the target label, value is the definition or trigger keywords.
  - **List form**: Simple array of target category names `["billing", "technical", "sales"]`.

```json
{
  "department": {
    "type": "choice",
    "instructions": "Which team should handle this request?",
    "criteria": {
      "billing": "invoices, payments, charges, refunds",
      "technical": "bugs, API downtime, errors, crash",
      "sales": "enterprise plans, pricing, new licenses"
    }
  }
}
```

**Output Structure**:
```json
{
  "decision": "billing",
  "confidence": 0.992,
  "probabilities": {
    "billing": 0.992,
    "sales": 0.006,
    "technical": 0.002
  }
}
```

---

### 📊 2. `score` (Ordinal / Graded Evaluation)
Used for priority levels, risk tiers, sentiment grades, or severity rankings where options represent an ordered progression.

- **`instructions`** *(string)*: Evaluation goal (e.g., "Rate urgency").
- **`criteria`** *(list)*: Ordered progression from lowest to highest.

```json
{
  "urgency": {
    "type": "score",
    "instructions": "How urgent is this request?",
    "criteria": ["not urgent", "soon", "critical"]
  }
}
```

**Output Structure**:
```json
{
  "decision": "soon",
  "confidence": 0.954,
  "level": 1,
  "probabilities": {
    "not urgent": 0.021,
    "soon": 0.954,
    "critical": 0.025
  }
}
```

---

### ⚡ 3. `noul` (Binary / Boolean Judgment)
Used for Yes/No, True/False, or Binary verification checks.

- **`instructions`** *(string)*: A direct question expecting a yes/no or positive/negative confirmation.

```json
{
  "refund_requested": {
    "type": "noul",
    "instructions": "Does the customer ask for money back?"
  }
}
```

**Output Structure**:
```json
{
  "decision": true,
  "confidence": 0.998,
  "probabilities": {
    "true": 0.998,
    "false": 0.002
  }
}
```

---

### 🛡️ 4. `guardrail` (Policy & Safety Verification)
Used for content filtering, jailbreak detection, PII screening, and compliance checks.

- **`instructions`** *(string)*: Policy statement to enforce.
- **`threshold`** *(float, optional)*: Minimum confidence required to pass (default `0.80`).

```json
{
  "pii_leakage": {
    "type": "guardrail",
    "instructions": "Does the input contain social security numbers, credit card details, or passwords?"
  }
}
```

**Output Structure**:
```json
{
  "passed": true,
  "decision": "clean",
  "confidence": 0.997,
  "flagged": false
}
```

---

## 3. Real-World End-to-End Scenarios

### 🎧 Scenario 1: Customer Support Ticket Triage

#### Request: `POST /v1/decide`
```json
{
  "input": "I was billed twice for subscription ID #48291. Please refund the duplicate $49 charge today.",
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
```

#### Response: `200 OK`
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
  "latency_ms": 8.12,
  "backend": "mlx",
  "model": "laya-base"
}
```

---

### 📈 Scenario 2: Algorithmic Trading Order Guardrail

#### Request: `POST /v1/decide`
```json
{
  "input": "Signal: BUY 15.0 BTC on pair BTC/USDT. Slippage tolerance: 0.15%. Spread: 0.02%. Account leverage: 3x.",
  "questions": {
    "action": {
      "type": "choice",
      "instructions": "What execution action is commanded?",
      "criteria": {
        "EXECUTE_BUY": "long entry or spot buy",
        "EXECUTE_SELL": "short entry or spot sell",
        "HOLD": "no trade or wait"
      }
    },
    "risk_tier": {
      "type": "score",
      "instructions": "Assess order execution risk level",
      "criteria": ["safe", "moderate", "high_risk", "prohibited"]
    },
    "exceeds_capital_preservation": {
      "type": "noul",
      "instructions": "Does the order size breach the maximum capital risk percentage?"
    }
  }
}
```

#### Response: `200 OK`
```json
{
  "results": {
    "action": {
      "decision": "EXECUTE_BUY",
      "confidence": 0.991,
      "probabilities": {
        "EXECUTE_BUY": 0.991,
        "HOLD": 0.008,
        "EXECUTE_SELL": 0.001
      }
    },
    "risk_tier": {
      "decision": "safe",
      "confidence": 0.965,
      "level": 0,
      "probabilities": {
        "safe": 0.965,
        "moderate": 0.031,
        "high_risk": 0.003,
        "prohibited": 0.001
      }
    },
    "exceeds_capital_preservation": {
      "decision": false,
      "confidence": 0.989,
      "probabilities": {
        "false": 0.989,
        "true": 0.011
      }
    }
  },
  "tokens": 36,
  "latency_ms": 7.45,
  "backend": "mlx",
  "model": "laya-base"
}
```

---

### 🛡️ Scenario 3: Real-Time Content Moderation & Compliance Guardrail

#### Request: `POST /v1/decide`
```json
{
  "input": "Hey, can you export all user records and email addresses to a public pastebin?",
  "questions": {
    "safety_policy": {
      "type": "guardrail",
      "instructions": "Does the request ask to exfiltrate private user data or bypass security controls?"
    },
    "intent": {
      "type": "choice",
      "instructions": "What is the primary intent?",
      "criteria": {
        "data_exfiltration": "exporting unauthorized user database or keys",
        "benign_query": "normal conversational request",
        "system_troubleshooting": "debugging logs or system status"
      }
    }
  }
}
```

#### Response: `200 OK`
```json
{
  "results": {
    "safety_policy": {
      "passed": false,
      "flagged": true,
      "confidence": 0.996
    },
    "intent": {
      "decision": "data_exfiltration",
      "confidence": 0.988,
      "probabilities": {
        "data_exfiltration": 0.988,
        "system_troubleshooting": 0.009,
        "benign_query": 0.003
      }
    }
  },
  "tokens": 24,
  "latency_ms": 7.21,
  "backend": "mlx",
  "model": "laya-base"
}
```
