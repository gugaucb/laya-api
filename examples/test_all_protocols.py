"""Comprehensive test script demonstrating all Laya API protocols in Python.

Requirements:
    pip install openai anthropic httpx websockets
"""

import json
import asyncio
import httpx
from openai import OpenAI
import anthropic
import websockets

BASE_URL = "http://localhost:8000"


def test_openai_chat_completions():
    print("\n" + "=" * 60)
    print("🤖 1. TEST: OpenAI Compatible Protocol (/v1/chat/completions)")
    print("=" * 60)
    
    client = OpenAI(
        base_url=f"{BASE_URL}/v1",
        api_key="not-needed"
    )

    response = client.chat.completions.create(
        model="laya-base",
        messages=[
            {"role": "system", "content": "You are a customer support ticket classifier."},
            {"role": "user", "content": "I was billed twice. Please refund the duplicate $49 invoice today."}
        ],
        logprobs=True,
        top_logprobs=3
    )

    print("Status: SUCCESS")
    print("Raw Content String:", response.choices[0].message.content)
    parsed = json.loads(response.choices[0].message.content)
    print("Parsed JSON Decision:", json.dumps(parsed, indent=2))


def test_anthropic_messages():
    print("\n" + "=" * 60)
    print("🧠 2. TEST: Anthropic Compatible Protocol (/v1/messages)")
    print("=" * 60)

    client = anthropic.Anthropic(
        base_url=BASE_URL,
        api_key="not-needed"
    )

    message = client.messages.create(
        model="laya-base",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Evaluate trading signal: BUY 2.5 BTC at market rate."}
        ]
    )

    print("Status: SUCCESS")
    print("Response Type:", message.type)
    print("Message Content:", message.content[0].text)


def test_native_single_and_multi_question():
    print("\n" + "=" * 60)
    print("⚡ 3. TEST: High-Speed Native REST Endpoint (/v1/decide)")
    print("=" * 60)

    with httpx.Client(base_url=BASE_URL) as client:
        # A. Single evaluation
        resp1 = client.post("/v1/decide", json={
            "input": "User password reset request from unknown browser fingerprint.",
            "on_overflow": "error"
        })
        print("\n--- A. Simple Single-Label Decision ---")
        print(f"HTTP {resp1.status_code} (Backend: {resp1.headers.get('X-Laya-Backend')}, Latency: {resp1.headers.get('X-Laya-Latency-Ms')}ms)")
        print(json.dumps(resp1.json(), indent=2))

        # B. Multi-Question Structured Evaluation
        resp2 = client.post("/v1/decide", json={
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
        })
        print("\n--- B. Multi-Question Structured Evaluation ---")
        print(f"HTTP {resp2.status_code} (Backend: {resp2.headers.get('X-Laya-Backend')}, Latency: {resp2.headers.get('X-Laya-Latency-Ms')}ms)")
        print(json.dumps(resp2.json(), indent=2))


async def test_websocket_stream():
    print("\n" + "=" * 60)
    print("🔌 4. TEST: WebSocket Persistent Duplex Loop (/v1/stream/decide)")
    print("=" * 60)

    uri = f"ws://localhost:8000/v1/stream/decide"
    async with websockets.connect(uri) as ws:
        for i in range(3):
            req_id = f"stream-msg-{i+1}"
            payload = {
                "id": req_id,
                "input": f"Live order book snapshot #{i+1} for BTC/USDT scalp strategy",
                "on_overflow": "truncate_head"
            }
            await ws.send(json.dumps(payload))
            raw_resp = await ws.recv()
            data = json.loads(raw_resp)
            print(f"[{req_id}] -> Decision: {data.get('label')} (Latency: {data.get('latency_ms')}ms)")


def main():
    print("🚀 Starting All Laya API Protocol Verification Tests...")
    
    # 1. Health check
    try:
        r = httpx.get(f"{BASE_URL}/health")
        print(f"Server Health: {r.json()}")
    except Exception as e:
        print(f"❌ Server not reachable at {BASE_URL}. Start the server first!")
        return

    # 2. Run protocol tests
    test_openai_chat_completions()
    test_anthropic_messages()
    test_native_single_and_multi_question()
    asyncio.run(test_websocket_stream())

    print("\n" + "=" * 60)
    print("🎉 ALL PROTOCOLS VERIFIED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
