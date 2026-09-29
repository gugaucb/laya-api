"""Anthropic API schema adapter for Laya inference."""

import json
import time
import uuid
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

from laya_api.engine import DecisionResult


class AnthropicMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]


class AnthropicMessagesRequest(BaseModel):
    model: str = "laya-base"
    messages: List[AnthropicMessage]
    max_tokens: Optional[int] = 1024
    system: Optional[Union[str, List[Dict[str, Any]]]] = None
    stream: bool = False
    metadata: Optional[Dict[str, Any]] = None


def format_anthropic_message_response(result: DecisionResult) -> Dict[str, Any]:
    content_str = json.dumps({
        "label": result.label,
        "confidence": result.confidence,
        "probabilities": result.probabilities
    })

    return {
        "id": f"msg_laya_{uuid.uuid4().hex[:12]}",
        "type": "message",
        "role": "assistant",
        "model": result.model,
        "content": [
            {
                "type": "text",
                "text": content_str
            }
        ],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": result.tokens,
            "output_tokens": 1
        }
    }


def stream_anthropic_message_response(result: DecisionResult):
    msg_id = f"msg_laya_{uuid.uuid4().hex[:12]}"
    content_str = json.dumps({
        "label": result.label,
        "confidence": result.confidence,
        "probabilities": result.probabilities
    })

    # Event 1: message_start
    yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': msg_id, 'type': 'message', 'role': 'assistant', 'model': result.model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': result.tokens, 'output_tokens': 0}}})}\n\n"

    # Event 2: content_block_start
    yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"

    # Event 3: content_block_delta
    yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': content_str}})}\n\n"

    # Event 4: content_block_stop
    yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"

    # Event 5: message_delta
    yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': 'end_turn', 'stop_sequence': None}, 'usage': {'output_tokens': 1}})}\n\n"

    # Event 6: message_stop
    yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"
