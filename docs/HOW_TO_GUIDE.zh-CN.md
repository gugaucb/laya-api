# Laya API: 多语言集成与协议实战指南 (HOW-TO Guide)

本指南提供使用 **Python**、**PHP / Laravel**、**Rust** 和 **Java** 接入 **Laya API** 的全套实战代码与协议最佳实践。

---

## 🧭 1. 选择最适合的传输协议

Laya 是非自回归的“系统 1”决策模型，单次推理耗时仅约 **7–14ms**。合理选择通信协议可避免网络层握手成为性能瓶颈：

| 传输协议 | 适用场景 | 额外网络延迟 | 推荐客户端 / 库 |
| :--- | :--- | :--- | :--- |
| **Unix Domain Socket (UDS)** | 同台主机内的进程间通信 (IPC) | **< 0.3 ms** | Python `httpx`, PHP `curl`, Rust `tokio`, Java 16+ `UnixDomainSocketAddress` |
| **WebSocket (`/v1/stream/decide`)** | 高频循环长连接（量化交易策略、实时风控拦截） | **< 0.5 ms** (单次请求零握手) | Python `websockets`, Rust `tokio-tungstenite`, Java `WebSocket`, PHP Ratchet |
| **HTTP/2 Keep-Alive (`/v1/decide`)** | 分布式微服务高吞吐决策调用 | **~ 1.0 ms** | Python `httpx`, Go `net/http`, Rust `reqwest`, Java `HttpClient` |
| **OpenAI 兼容格式 (`/v1/chat/completions`)** | 现有基于 OpenAI 接口的 Agent 无缝平替 | **~ 1.2 ms** | OpenAI 官方 SDK (Python, JS/TS, Go, Rust, Java, PHP) |
| **Anthropic 兼容格式 (`/v1/messages`)** | 现有基于 Claude / Anthropic 接口的应用 | **~ 1.2 ms** | Anthropic 官方 SDK (Python, TypeScript, Go) |

---

## 🐍 2. Python 语言集成

### A. 使用 OpenAI 官方 Python SDK
```python
from openai import OpenAI

# 初始化客户端，指向本地 Laya API 服务
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="laya-base",
    messages=[
        {"role": "system", "content": "你是一个客服工单分类器。"},
        {"role": "user", "content": "申请退款：订单 #8849 运输破损。"}
    ],
    logprobs=True,
    top_logprobs=3,
    stream=False
)

# 获取决策 JSON 字符串
print("决策结果:", response.choices[0].message.content)
```

### B. 使用 Anthropic 官方 Python SDK
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
        {"role": "user", "content": "判断该笔 35,000 元转账是否超过风控频次限制。"}
    ]
)

print("判定输出:", message.content[0].text)
```

### C. 超低延迟 Unix Domain Socket (同机进程)
```python
import httpx

# 通过 Unix Domain Socket 直连（绕过 TCP/IP 协议栈开销）
transport = httpx.HTTPTransport(uds="/tmp/laya.sock")
with httpx.Client(transport=transport, base_url="http://localhost") as client:
    resp = client.post("/v1/decide", json={
        "input": "异地 IP 登录验证请求",
        "on_overflow": "error"
    })
    data = resp.json()
    print(f"结果: {data['label']} (置信度: {data['confidence']:.2%}) 耗时 {data['latency_ms']}ms")
```

### D. WebSocket 双向长连接循环 (高频量化与流处理)
```python
import asyncio
import json
import websockets

async def decision_stream():
    uri = "ws://localhost:8000/v1/stream/decide"
    async with websockets.connect(uri) as ws:
        for i in range(5):
            payload = {
                "id": f"evt-{i}",
                "input": f"行情 Tick 事件: BTC/USDT 剧烈波动信号 #{i}",
                "on_overflow": "truncate_head"
            }
            await ws.send(json.dumps(payload))
            response = await ws.recv()
            print("收到决策响应:", response)

asyncio.run(decision_stream())
```

---

## 🐘 3. PHP / Laravel 语言集成

### A. 使用 Laravel HTTP Client (`Http` Facade)
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
     * 使用高性能原生决策接口
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
            throw new RuntimeException("Laya API 请求失败: " . $response->body());
        }

        return $response->json();
    }

    /**
     * 使用 OpenAI Chat Completions 兼容接口
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

### B. 基于原生 PHP cURL 的 Unix Domain Socket 调用
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
        throw new Exception("请求失败 HTTP {$httpCode}: {$result}");
    }

    return json_decode($result, true);
}

// 执行示例
$decision = evaluateViaUDS('/tmp/laya.sock', '交易订单风控审核载荷');
print_r($decision);
```

---

## 🦀 4. Rust 语言集成

### A. 使用 `reqwest` 实现 HTTP/2 长连接复用
在 `Cargo.toml` 中添加：
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
        input: "高频交易套利策略执行前置风控判定",
        on_overflow: "error",
    };

    let res: DecideResponse = client
        .post("http://localhost:8000/v1/decide")
        .json(&req)
        .send()
        .await?
        .json()
        .await?;

    println!("决策结果: {} (置信度: {:.2}%) 耗时: {:.2}ms [引擎: {}]", 
        res.label, res.confidence * 100.0, res.latency_ms, res.backend);

    Ok(())
}
```

### B. 基于 `tokio-tungstenite` 的 WebSocket 流式通信
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
            "input": format!("实时风控数据包 #{}", i),
            "on_overflow": "truncate_head"
        });

        write.send(Message::Text(msg.to_string())).await?;

        if let Some(Ok(Message::Text(text))) = read.next().await {
            println!("收到决策响应: {}", text);
        }
    }

    Ok(())
}
```

---

## ☕ 5. Java 语言集成

### A. 使用标准 `HttpClient` (Java 16+)
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
                "input": "跨境支付大额交易风控审核评估",
                "on_overflow": "error"
            }
            """;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:8000/v1/decide"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("状态码: " + response.statusCode());
        System.out.println("响应数据: " + response.body());
        System.out.println("服务端耗时 (ms): " + response.headers().firstValue("X-Laya-Latency-Ms").orElse("N/A"));
    }
}
```

### B. Java 16+ 原生 Unix Domain Socket 支持
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
            String payload = "{\"input\": \"高频量化风控校验\", \"on_overflow\": \"error\"}";
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
            System.out.println("UDS 响应结果:\n" + response);
        }
    }
}
```

---

## 🛡️ 6. 上下文长度与溢出处理最佳实践

Laya 模型具有严格的 Token 上下文限制（如 512 或 1024 Token）。请根据业务场景明确指定 `on_overflow` 参数：

- `on_overflow: "error"`（**默认推荐，适用于合规与审计场景**）：
  - 超出长度限制时立即返回 `HTTP 400 Bad Request`，确保不会遗漏关键信息。
- `on_overflow: "truncate_head"`（**适用于实时长会话与时序流数据**）：
  - 保留最新鲜的尾部数据，丢弃较早的历史上下文。
## 🧩 7. 多维度结构化评估 (Multi-Question)

Laya 支持通过 `questions` 模式字典在单次前向推理中同时评估多个决策维度，支持包含 `choice`、`score`、`noul` 和 `guardrail` 等题型。

### Python 多问题评估实战
```python
import httpx

payload = {
    "input": "我被重复扣款了，请今天立即退还重复扣取的费用。",
    "questions": {
        "department": {
            "type": "choice",
            "instructions": "该请求应由哪个部门处理？",
            "criteria": {
                "billing": "账单、支付、扣款与退款",
                "technical": "系统故障、API 异常与 Bug",
                "sales": "新采购与企业版咨询"
            }
        },
        "urgency": {
            "type": "score",
            "instructions": "评估该请求的紧急程度",
            "criteria": ["不紧急", "尽快处理", "紧急严重"]
        },
        "refund": {
            "type": "noul",
            "instructions": "客户是否在申请退款？"
        }
    }
}

resp = httpx.post("http://localhost:8000/v1/decide", json=payload)
data = resp.json()

print("处理部门:", data["results"]["department"]["decision"]) # -> billing
print("紧急程度:", data["results"]["urgency"]["decision"])    # -> 尽快处理 (level 1)
print("是否退款:", data["results"]["refund"]["decision"])    # -> True
```

### PHP / Laravel 多问题评估实战
```php
<?php

use Illuminate\Support\Facades\Http;

$payload = [
    'input' => '我被重复扣款了，请今天立即退还重复扣取的费用。',
    'questions' => [
        'department' => [
            'type' => 'choice',
            'instructions' => '该请求应由哪个部门处理？',
            'criteria' => [
                'billing' => '账单、支付、扣款与退款',
                'technical' => '系统故障、API 异常与 Bug',
                'sales' => '新采购与企业版咨询'
            ]
        ],
        'urgency' => [
            'type' => 'score',
            'instructions' => '评估该请求的紧急程度',
            'criteria' => ['不紧急', '尽快处理', '紧急严重']
        ],
        'refund' => [
            'type' => 'noul',
            'instructions' => '客户是否在申请退款？'
        ]
    ]
];

$response = Http::baseUrl('http://localhost:8000')->post('/v1/decide', $payload);
$results = $response->json('results');

echo "处理部门: " . $results['department']['decision'] . "\n";
echo "紧急程度: " . $results['urgency']['decision'] . "\n";
echo "是否退款: " . ($results['refund']['decision'] ? '是' : '否') . "\n";
```

### Rust 多问题评估实战
```rust
use reqwest::Client;
use serde_json::json;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = Client::new();

    let payload = json!({
        "input": "我被重复扣款了，请今天立即退还重复扣取的费用。",
        "questions": {
            "department": {
                "type": "choice",
                "instructions": "该请求应由哪个部门处理？",
                "criteria": {
                    "billing": "账单、支付、扣款与退款",
                    "technical": "系统故障、API 异常与 Bug",
                    "sales": "新采购与企业版咨询"
                }
            },
            "urgency": {
                "type": "score",
                "instructions": "评估该请求的紧急程度",
                "criteria": ["不紧急", "尽快处理", "紧急严重"]
            },
            "refund": {
                "type": "noul",
                "instructions": "客户是否在申请退款？"
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

    println!("结构化判定结果:\n{}", serde_json::to_string_pretty(&res["results"])?);
    Ok(())
}
```

### Java 多问题评估实战
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
                "input": "我被重复扣款了，请今天立即退还重复扣取的费用。",
                "questions": {
                    "department": {
                        "type": "choice",
                        "instructions": "该请求应由哪个部门处理？",
                        "criteria": {
                            "billing": "账单、支付、扣款与退款",
                            "technical": "系统故障、API 异常与 Bug",
                            "sales": "新采购与企业版咨询"
                        }
                    },
                    "urgency": {
                        "type": "score",
                        "instructions": "评估该请求的紧急程度",
                        "criteria": ["不紧急", "尽快处理", "紧急严重"]
                    },
                    "refund": {
                        "type": "noul",
                        "instructions": "客户是否在申请退款？"
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
        System.out.println("结构化评估结果:\n" + response.body());
    }
}
```
