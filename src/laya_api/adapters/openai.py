"""OpenAI API schema adapter for Laya inference."""

import json
import math
import time
import uuid
from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse, JSONResponse

from laya_api.engine import DecisionResult


class ChatMessage(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    model: str = "laya-base"
    messages: List[ChatMessage]
    stream: bool = False
    logprobs: Optional[bool] = False
    top_logprobs: Optional[int] = None
    extra_body: Optional[Dict[str, Any]] = None


def format_openai_chat_response(result: DecisionResult, logprobs: bool = False, top_logprobs: Optional[int] = None) -> Dict[str, Any]:
    content_str = json.dumps({
        "label": result.label,
        "confidence": result.confidence,
        "probabilities": result.probabilities
    })

    logprobs_payload = None
    if logprobs:
        top_items = []
        for label, prob in sorted(result.probabilities.items(), key=lambda x: x[1], reverse=True):
            logprob_val = round(math.log(max(prob, 1e-9)), 4)
            top_items.append({
                "token": label,
                "logprob": logprob_val
            })
        
        if top_logprobs and top_logprobs > 0:
            top_items = top_items[:top_logprobs]

        selected_logprob = round(math.log(max(result.confidence, 1e-9)), 4)
        logprobs_payload = {
            "content": [
                {
                    "token": result.label,
                    "logprob": selected_logprob,
                    "top_logprobs": top_items
                }
            ]
        }

    return {
        "id": f"chatcmpl-laya-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": result.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content_str
                },
                "logprobs": logprobs_payload,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": result.tokens,
            "completion_tokens": 1,
            "total_tokens": result.tokens + 1
        },
        "decision_meta": {
            "predicted_label": result.label,
            "probability": result.confidence,
            "probabilities": result.probabilities
        }
    }


def stream_openai_chat_response(result: DecisionResult):
    chat_id = f"chatcmpl-laya-{uuid.uuid4().hex[:12]}"
    created = int(time.time())
    content_str = json.dumps({
        "label": result.label,
        "confidence": result.confidence,
        "probabilities": result.probabilities
    })

    # Chunk 1: Role & initial delta
    chunk1 = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": result.model,
        "choices": [
            {
                "index": 0,
                "delta": {
                    "role": "assistant",
                    "content": content_str
                },
                "finish_reason": None
            }
        ]
    }
    yield f"data: {json.dumps(chunk1)}\n\n"

    # Chunk 2: Finish chunk
    chunk2 = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": result.model,
        "choices": [
            {
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }
        ]
    }
    yield f"data: {json.dumps(chunk2)}\n\n"
    yield "data: [DONE]\n\n"
