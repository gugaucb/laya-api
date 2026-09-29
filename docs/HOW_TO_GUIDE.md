# Laya API: Multi-Language Integration & Protocol HOW-TO Guide

This guide provides practical, educational, and production-ready examples for integrating **Laya API** across **Python**, **PHP / Laravel**, **Rust**, and **Java**.

---

## 🧭 1. Choosing the Optimal Protocol

Laya is a single-pass decision model with ~7–14ms inference time. Choosing the right protocol ensures your network overhead does not become the bottleneck:

| Protocol | Best For | Typical Latency Overhead | Supported SDKs / Libraries |
| :--- | :--- | :--- | :--- |
| **Unix Domain Socket (UDS)** | Agents running on the same host (IPC) | **< 0.3 ms** | Python `httpx`, PHP `curl`, Rust `tokio`, Java 16+ `UnixDomainSocketAddress` |
| **WebSocket (`/v1/stream/decide`)** | Continuous high-frequency loops (Trading, Live Guardrails) | **< 0.5 ms** (zero handshake per request) | Python `websockets`, Rust `tokio-tungstenite`, Java `WebSocket`, PHP Ratchet |
| **HTTP/2 Keep-Alive (`/v1/decide`)** | High-throughput distributed microservices | **~ 1.0 ms** | Python `httpx`, Go `net/http`, Rust `reqwest`, Java `HttpClient` |
| **OpenAI Format (`/v1/chat/completions`)** | Drop-in replacement for existing OpenAI agents | **~ 1.2 ms** | Official OpenAI SDKs (Python, JS/TS, Go, Rust, Java, PHP) |
| **Anthropic Format (`/v1/messages`)** | Drop-in replacement for Anthropic agents | **~ 1.2 ms** | Official Anthropic SDKs (Python, TypeScript, Go) |

---

## 🐍 2. Python Integration

### A. Using OpenAI Python SDK
```python
from openai import OpenAI

# Initialize client pointing to local Laya API
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="laya-base",
    messages=[
        {"role": "system", "content": "You are a customer support classifier."},
        {"role": "user", "content": "Refund request for order #8849: damaged item on arrival."}
    ],
    logprobs=True,
    top_logprobs=3,
    stream=False
)

# Parsed decision payload
print("Message Content:", response.choices[0].message.content)
```

### B. Using Anthropic Python SDK
```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://localhost:8000",
    api_key="not-needed"
)

message = client.messages.create(
    model="laya-base",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Check if transaction amount $4,500 exceeds velocity limit."}
    ]
)

print("Decision:", message.content[0].text)
```

### C. Ultra-Fast Unix Domain Socket (Co-located Agents)
```python
import httpx

# Connect directly to Unix Domain Socket (bypasses TCP/IP stack)
transport = httpx.HTTPTransport(uds="/tmp/laya.sock")
with httpx.Client(transport=transport, base_url="http://localhost") as client:
    resp = client.post("/v1/decide", json={
        "input": "User authentication attempt from unfamiliar IP address",
        "on_overflow": "error"
    })
    data = resp.json()
    print(f"Decision: {data['label']} (Confidence: {data['confidence']:.2%}) in {data['latency_ms']}ms")
```

### D. Continuous WebSocket Loop (Trading Bots & Streaming Pipelines)
```python
import asyncio
import json
import websockets

async def decision_stream():
    uri = "ws://localhost:8000/v1/stream/decide"
    async with websockets.connect(uri) as ws:
        for i in range(5):
            payload = {
                "id": f"event-{i}",
                "input": f"Market tick event: BTC/USDT price volatility spike #{i}",
                "on_overflow": "truncate_head"
            }
            await ws.send(json.dumps(payload))
            response = await ws.recv()
            print("Received decision:", response)

asyncio.run(decision_stream())
```

---

## 🐘 3. PHP / Laravel Integration

### A. Using Laravel HTTP Client (`Http` Facade)
```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use RuntimeException;

class LayaDecisionService
{
    protected string $baseUrl;

    public function __construct()
    {
        $this->baseUrl = config('services.laya.base_url', 'http://localhost:8000');
    }

    /**
     * Evaluate a decision using the high-performance native endpoint.
     */
    public function decide(string $text, string $onOverflow = 'error'): array
    {
        $response = Http::baseUrl($this->baseUrl)
            ->timeout(2.0)
            ->post('/v1/decide', [
                'input' => $text,
                'on_overflow' => $onOverflow
            ]);

        if ($response->failed()) {
            throw new RuntimeException("Laya API error: " . $response->body());
        }

        return $response->json();
    }

    /**
     * Evaluate using the OpenAI Chat Completion compatible endpoint.
     */
    public function chatEvaluate(string $prompt): array
    {
        $response = Http::baseUrl($this->baseUrl . '/v1')
            ->post('/chat/completions', [
                'model' => 'laya-base',
                'messages' => [
                    ['role' => 'user', 'content' => $prompt]
                ]
            ]);

        return $response->json();
    }
}
```

### B. High-Performance Unix Domain Socket with Native PHP cURL
```php
<?php

function evaluateViaUDS(string $socketPath, string $input): array
{
    $ch = curl_init('http://localhost/v1/decide');
    $payload = json_encode([
        'input' => $input,
        'on_overflow' => 'truncate_head'
    ]);

    curl_setopt($ch, CURLOPT_UNIX_SOCKET_PATH, $socketPath);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json'
    ]);

    $result = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode !== 200) {
        throw new Exception("Request failed with HTTP {$httpCode}: {$result}");
    }

    return json_decode($result, true);
}

// Example execution
$decision = evaluateViaUDS('/tmp/laya.sock', 'Order verification payload');
print_r($decision);
```

---

## 🦀 4. Rust Integration

### A. Using `reqwest` with HTTP/2 Keep-Alive
Add to `Cargo.toml`:
```toml
[dependencies]
reqwest = { version = "0.12", features = ["json", "http2"] }
tokio = { version = "1.0", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
```

```rust
use reqwest::Client;
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
struct DecideRequest<'a> {
    input: &'a str,
    on_overflow: &'a str,
}

#[derive(Deserialize, Debug)]
struct DecideResponse {
    label: String,
    confidence: f64,
    latency_ms: f64,
    backend: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = Client::builder()
        .http2_prior_knowledge()
        .build()?;

    let req = DecideRequest {
        input: "High frequency trading algorithmic risk guardrail check",
        on_overflow: "error",
    };

    let res: DecideResponse = client
        .post("http://localhost:8000/v1/decide")
        .json(&req)
        .send()
        .await?
        .json()
        .await?;

    println!("Decision: {} ({:.2}%) in {:.2}ms [{}]", 
        res.label, res.confidence * 100.0, res.latency_ms, res.backend);

    Ok(())
}
```

### B. High-Speed WebSocket Stream with `tokio-tungstenite`
Add to `Cargo.toml`:
```toml
[dependencies]
tokio-tungstenite = "0.21"
futures-util = "0.3"
```

```rust
use futures_util::{SinkExt, StreamExt};
use serde_json::json;
use tokio_tungstenite::connect_async;
use tungstenite::protocol::Message;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let url = "ws://localhost:8000/v1/stream/decide";
    let (ws_stream, _) = connect_async(url).await?;
    let (mut write, mut read) = ws_stream.split();

    for i in 0..3 {
        let msg = json!({
            "id": format!("order-{}", i),
            "input": format!("Validate transaction #{}", i),
            "on_overflow": "truncate_head"
        });

        write.send(Message::Text(msg.to_string())).await?;

        if let Some(Ok(Message::Text(text))) = read.next().await {
            println!("Received decision: {}", text);
        }
    }

    Ok(())
}
```

---

## ☕ 5. Java Integration

### A. Using Standard `java.net.http.HttpClient` (Java 16+)
```java
package com.example.laya;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public class LayaHttpClientExample {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newBuilder()
                .version(HttpClient.Version.HTTP_2)
                .connectTimeout(Duration.ofSeconds(2))
                .build();

        String jsonPayload = """
            {
                "input": "Risk assessment for wire transfer amount $10,000",
                "on_overflow": "error"
            }
            """;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:8000/v1/decide"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Status Code: " + response.statusCode());
        System.out.println("Response Body: " + response.body());
        System.out.println("Latency Header (ms): " + response.headers().firstValue("X-Laya-Latency-Ms").orElse("N/A"));
    }
}
```

### B. Unix Domain Socket Support in Java (Java 16+)
```java
package com.example.laya;

import java.net.UnixDomainSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;

public class LayaUDSJavaExample {
    public static void main(String[] args) throws Exception {
        Path socketPath = Path.of("/tmp/laya.sock");
        UnixDomainSocketAddress socketAddress = UnixDomainSocketAddress.of(socketPath);

        try (SocketChannel channel = SocketChannel.open(socketAddress)) {
            String payload = "{\"input\": \"High frequency trade evaluation\", \"on_overflow\": \"error\"}";
            String httpRequest = "POST /v1/decide HTTP/1.1\r\n" +
                    "Host: localhost\r\n" +
                    "Content-Type: application/json\r\n" +
                    "Content-Length: " + payload.getBytes(StandardCharsets.UTF_8).length + "\r\n\r\n" +
                    payload;

            channel.write(ByteBuffer.wrap(httpRequest.getBytes(StandardCharsets.UTF_8)));

            ByteBuffer buffer = ByteBuffer.allocate(4096);
            channel.read(buffer);
            buffer.flip();

            String response = StandardCharsets.UTF_8.decode(buffer).toString();
            System.out.println("UDS Response:\n" + response);
        }
    }
}
```

---

## 🛡️ 6. Context Window & Overflow Best Practices

Laya checkpoints feature strict token limits (e.g., 512 or 1024 tokens). Always specify `on_overflow` based on your application requirements:

- `on_overflow: "error"` (**Default & Recommended for Audit/Compliance**):
  - Returns `HTTP 400 Bad Request` if payload exceeds limits. Guarantees no data is silently omitted.
- `on_overflow: "truncate_head"` (**Recommended for Conversational & Real-Time Feeds**):
  - Preserves the most recent data (the tail) and drops older context.
## 🧩 7. Multi-Question Structured Evaluations

Laya can evaluate multiple decision dimensions simultaneously in a single forward pass by providing a `questions` schema dictionary containing question types (`choice`, `score`, `noul`, `guardrail`).

### Python Multi-Question Example
```python
import httpx

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

resp = httpx.post("http://localhost:8000/v1/decide", json=payload)
data = resp.json()

print("Department:", data["results"]["department"]["decision"])  # -> billing
print("Urgency:", data["results"]["urgency"]["decision"])        # -> soon (level 1)
print("Refund Requested:", data["results"]["refund"]["decision"]) # -> True
```

### PHP / Laravel Multi-Question Example
```php
<?php

use Illuminate\Support\Facades\Http;

$payload = [
    'input' => 'I was billed twice. Please refund the duplicate today.',
    'questions' => [
        'department' => [
            'type' => 'choice',
            'instructions' => 'Which team should handle this request?',
            'criteria' => [
                'billing' => 'invoices, payments, refunds',
                'technical' => 'bugs and outages',
                'sales' => 'new purchases'
            ]
        ],
        'urgency' => [
            'type' => 'score',
            'instructions' => 'How urgent is this request?',
            'criteria' => ['not urgent', 'soon', 'critical']
        ],
        'refund' => [
            'type' => 'noul',
            'instructions' => 'Does the customer ask for money back?'
        ]
    ]
];

$response = Http::baseUrl('http://localhost:8000')->post('/v1/decide', $payload);
$results = $response->json('results');

echo "Department: " . $results['department']['decision'] . "\n";
echo "Urgency: " . $results['urgency']['decision'] . "\n";
echo "Refund: " . ($results['refund']['decision'] ? 'YES' : 'NO') . "\n";
```

### Rust Multi-Question Example
```rust
use reqwest::Client;
use serde_json::json;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = Client::new();

    let payload = json!({
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
    });

    let res: serde_json::Value = client
        .post("http://localhost:8000/v1/decide")
        .json(&payload)
        .send()
        .await?
        .json()
        .await?;

    println!("Results:\n{}", serde_json::to_string_pretty(&res["results"])?);
    Ok(())
}
```

### Java Multi-Question Example
```java
package com.example.laya;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class LayaMultiQuestionExample {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();

        String payload = """
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
                }
            }
            """;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:8000/v1/decide"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("Structured Results:\n" + response.body());
    }
}
```
