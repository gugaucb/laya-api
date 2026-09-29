"""FastAPI application for Laya API."""

from typing import Optional, Literal, Dict, Any
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from laya_api.engine import BaseEngine, MockEngine, create_engine
from laya_api.validator import ContextValidator, ContextLengthExceededError
from laya_api.adapters.openai import (
    OpenAIChatRequest,
    format_openai_chat_response,
    stream_openai_chat_response
)
from laya_api.adapters.anthropic import (
    AnthropicMessagesRequest,
    format_anthropic_message_response,
    stream_anthropic_message_response
)


class DecideRequest(BaseModel):
    input: str
    model: Optional[str] = None
    questions: Optional[Dict[str, Any]] = None
    on_overflow: Literal["error", "truncate_head", "truncate_tail"] = "error"


class DecideResponse(BaseModel):
    label: Optional[str] = None
    confidence: Optional[float] = None
    probabilities: Optional[Dict[str, float]] = None
    results: Optional[Dict[str, Any]] = None
    tokens: int
    latency_ms: float
    backend: str
    model: str


def create_app(
    engine: Optional[BaseEngine] = None,
    max_context: int = 1024,
    model_name: str = "laya-base",
    backend: str = "auto"
) -> FastAPI:
    app = FastAPI(
        title="Laya API",
        description="Ultra-Fast OpenAI & Anthropic-Compatible Inference API for Laya Models",
        version="0.1.0"
    )

    if engine is None:
        engine = create_engine(model_name=model_name, backend=backend)

    validator = ContextValidator(max_tokens=max_context)

    # Attach to app state
    app.state.engine = engine
    app.state.validator = validator
    app.state.max_context = max_context

    @app.exception_handler(ContextLengthExceededError)
    async def context_overflow_handler(request: Request, exc: ContextLengthExceededError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "message": str(exc),
                    "type": "invalid_request_error",
                    "param": "input",
                    "code": "context_length_exceeded",
                    "details": {
                        "token_count": exc.token_count,
                        "max_context_length": exc.max_tokens
                    }
                }
            }
        )

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "model": app.state.engine.model_name,
            "backend": app.state.engine.backend_name
        }

    @app.post("/v1/decide", response_model=DecideResponse)
    async def decide(req: DecideRequest):
        tokens, count = validator.validate_and_tokenize(req.input, on_overflow=req.on_overflow)
        normalized_input = validator.decode(tokens)
        
        if req.questions:
            import time
            start = time.perf_counter()
            structured_results = engine.infer_structured(normalized_input, req.questions, token_count=count)
            latency_ms = round((time.perf_counter() - start) * 1000.0, 2)
            headers = {
                "X-Laya-Latency-Ms": str(latency_ms),
                "X-Laya-Backend": engine.backend_name,
                "X-Laya-Model": engine.model_name
            }
            return JSONResponse(
                status_code=200,
                headers=headers,
                content={
                    "results": structured_results,
                    "tokens": count,
                    "latency_ms": latency_ms,
                    "backend": engine.backend_name,
                    "model": engine.model_name
                }
            )

        result = engine.infer(normalized_input, token_count=count)
        
        headers = {
            "X-Laya-Latency-Ms": str(result.latency_ms),
            "X-Laya-Backend": result.backend,
            "X-Laya-Model": result.model
        }
        
        return JSONResponse(
            status_code=200,
            headers=headers,
            content={
                "label": result.label,
                "confidence": result.confidence,
                "probabilities": result.probabilities,
                "tokens": result.tokens,
                "latency_ms": result.latency_ms,
                "backend": result.backend,
                "model": result.model
            }
        )

    @app.post("/v1/chat/completions")
    async def chat_completions(req: OpenAIChatRequest):
        combined_text = "\n".join(f"{msg.role}: {msg.content}" for msg in req.messages)
        overflow_strategy = "error"
        questions = None
        if req.extra_body:
            if "on_overflow" in req.extra_body:
                overflow_strategy = req.extra_body["on_overflow"]
            if "questions" in req.extra_body:
                questions = req.extra_body["questions"]

        tokens, count = validator.validate_and_tokenize(combined_text, on_overflow=overflow_strategy)
        normalized_input = validator.decode(tokens)

        if questions:
            import time
            start = time.perf_counter()
            structured_results = engine.infer_structured(normalized_input, questions, token_count=count)
            latency_ms = round((time.perf_counter() - start) * 1000.0, 2)
            headers = {
                "X-Laya-Latency-Ms": str(latency_ms),
                "X-Laya-Backend": engine.backend_name,
                "X-Laya-Model": engine.model_name
            }
            import uuid, json
            resp_payload = {
                "id": f"chatcmpl-laya-{uuid.uuid4().hex[:12]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": engine.model_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(structured_results)
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": count,
                    "completion_tokens": 1,
                    "total_tokens": count + 1
                },
                "results": structured_results
            }
            return JSONResponse(status_code=200, headers=headers, content=resp_payload)

        result = engine.infer(normalized_input, token_count=count)

        headers = {
            "X-Laya-Latency-Ms": str(result.latency_ms),
            "X-Laya-Backend": result.backend,
            "X-Laya-Model": result.model
        }

        if req.stream:
            return StreamingResponse(
                stream_openai_chat_response(result),
                media_type="text/event-stream",
                headers=headers
            )

        resp_payload = format_openai_chat_response(
            result,
            logprobs=bool(req.logprobs),
            top_logprobs=req.top_logprobs
        )
        return JSONResponse(status_code=200, headers=headers, content=resp_payload)

    @app.post("/v1/messages")
    async def messages(req: AnthropicMessagesRequest):
        text_parts = []
        if req.system:
            if isinstance(req.system, str):
                text_parts.append(f"system: {req.system}")
            elif isinstance(req.system, list):
                for blk in req.system:
                    if isinstance(blk, dict) and "text" in blk:
                        text_parts.append(f"system: {blk['text']}")

        for msg in req.messages:
            if isinstance(msg.content, str):
                text_parts.append(f"{msg.role}: {msg.content}")
            elif isinstance(msg.content, list):
                for blk in msg.content:
                    if isinstance(blk, dict) and "text" in blk:
                        text_parts.append(f"{msg.role}: {blk['text']}")

        combined_text = "\n".join(text_parts)
        overflow_strategy = "error"
        if req.metadata and "on_overflow" in req.metadata:
            overflow_strategy = req.metadata["on_overflow"]

        tokens, count = validator.validate_and_tokenize(combined_text, on_overflow=overflow_strategy)
        normalized_input = validator.decode(tokens)

        result = engine.infer(normalized_input, token_count=count)

        headers = {
            "X-Laya-Latency-Ms": str(result.latency_ms),
            "X-Laya-Backend": result.backend,
            "X-Laya-Model": result.model
        }

        if req.stream:
            return StreamingResponse(
                stream_anthropic_message_response(result),
                media_type="text/event-stream",
                headers=headers
            )

        resp_payload = format_anthropic_message_response(result)
        return JSONResponse(status_code=200, headers=headers, content=resp_payload)

    @app.websocket("/v1/stream/decide")
    async def stream_decide_ws(websocket: WebSocket):
        await websocket.accept()
        try:
            while True:
                data_str = await websocket.receive_text()
                import json
                try:
                    payload = json.loads(data_str)
                    raw_input = payload.get("input", "")
                    req_id = payload.get("id", "")
                    questions = payload.get("questions", None)
                    overflow_strategy = payload.get("on_overflow", "error")

                    tokens, count = validator.validate_and_tokenize(raw_input, on_overflow=overflow_strategy)
                    normalized_input = validator.decode(tokens)

                    if questions:
                        import time
                        start = time.perf_counter()
                        structured_results = engine.infer_structured(normalized_input, questions, token_count=count)
                        latency_ms = round((time.perf_counter() - start) * 1000.0, 2)
                        response_data = {
                            "id": req_id,
                            "results": structured_results,
                            "latency_ms": latency_ms,
                            "tokens": count,
                            "backend": engine.backend_name,
                            "model": engine.model_name
                        }
                    else:
                        result = engine.infer(normalized_input, token_count=count)
                        response_data = {
                            "id": req_id,
                            "label": result.label,
                            "confidence": result.confidence,
                            "probabilities": result.probabilities,
                            "latency_ms": result.latency_ms,
                            "tokens": result.tokens,
                            "backend": result.backend,
                            "model": result.model
                        }
                    await websocket.send_text(json.dumps(response_data))
                except ContextLengthExceededError as err:
                    err_response = {
                        "id": payload.get("id", "") if "payload" in locals() else "",
                        "error": {
                            "message": str(err),
                            "type": "invalid_request_error",
                            "code": "context_length_exceeded"
                        }
                    }
                    await websocket.send_text(json.dumps(err_response))
                except Exception as ex:
                    err_response = {
                        "id": payload.get("id", "") if "payload" in locals() else "",
                        "error": {
                            "message": str(ex),
                            "type": "server_error"
                        }
                    }
                    await websocket.send_text(json.dumps(err_response))
        except WebSocketDisconnect:
            pass

    return app
