# Laya API: Guia Prático HOW-TO de Integração e Protocolos Multi-Linguagem

Este guia apresenta exemplos práticos, didáticos e prontos para produção para integração com a **Laya API** utilizando **Python**, **PHP / Laravel**, **Rust** e **Java**.

---

## 🧭 1. Escolhendo o Protocolo Ideal

O Laya é um motor de decisão não-autoregressivo ("System 1") com tempo de inferência de apenas ~7–14ms. Escolher o protocolo correto garante que o handshake de rede não se torne o gargalo da sua aplicação:

| Protocolo | Ideal Para | Sobrecarga de Latência | SDKs / Bibliotecas Suportadas |
| :--- | :--- | :--- | :--- |
| **Unix Domain Socket (UDS)** | Agentes e processos rodando na mesma máquina (IPC) | **< 0.3 ms** | Python `httpx`, PHP `curl`, Rust `tokio`, Java 16+ `UnixDomainSocketAddress` |
| **WebSocket (`/v1/stream/decide`)** | Loops de alta frequência contínuos (Trading, Guardrails em tempo real) | **< 0.5 ms** (zero handshake por request) | Python `websockets`, Rust `tokio-tungstenite`, Java `WebSocket`, PHP Ratchet |
| **HTTP/2 Keep-Alive (`/v1/decide`)** | Microsserviços distribuídos de alta vazão | **~ 1.0 ms** | Python `httpx`, Go `net/http`, Rust `reqwest`, Java `HttpClient` |
| **Padrão OpenAI (`/v1/chat/completions`)** | Substituição direta para agentes que já usam OpenAI | **~ 1.2 ms** | SDKs oficiais da OpenAI (Python, JS/TS, Go, Rust, Java, PHP) |
| **Padrão Anthropic (`/v1/messages`)** | Substituição direta para fluxos Claude / Anthropic | **~ 1.2 ms** | SDKs oficiais da Anthropic (Python, TypeScript, Go) |

---

## 🐍 2. Integração com Python

### A. Utilizando o SDK Oficial da OpenAI
```python
from openai import OpenAI

# Inicializa o cliente apontando para a Laya API local
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="laya-base",
    messages=[
        {"role": "system", "content": "Você é um classificador de suporte ao cliente."},
        {"role": "user", "content": "Solicitação de reembolso para o pedido #8849: item avariado no transporte."}
    ],
    logprobs=True,
    top_logprobs=3,
    stream=False
)

# Conteúdo da mensagem formatado em JSON
print("Decisão:", response.choices[0].message.content)
```

### B. Utilizando o SDK Oficial da Anthropic
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
        {"role": "user", "content": "Verifique se o valor da transação R$ 4.500 excede o limite de velocidade."}
    ]
)

print("Decisão:", message.content[0].text)
```

### C. Ultra-Baixa Latência com Unix Domain Socket (Mesma Máquina)
```python
import httpx

# Conexão direta via Unix Domain Socket (elimina pilha TCP/IP)
transport = httpx.HTTPTransport(uds="/tmp/laya.sock")
with httpx.Client(transport=transport, base_url="http://localhost") as client:
    resp = client.post("/v1/decide", json={
        "input": "Tentativa de autenticação a partir de IP incomum",
        "on_overflow": "error"
    })
    data = resp.json()
    print(f"Decisão: {data['label']} (Confiança: {data['confidence']:.2%}) em {data['latency_ms']}ms")
```

### D. Loop Contínuo via WebSocket (Robôs de Trading e Streaming)
```python
import asyncio
import json
import websockets

async def decision_stream():
    uri = "ws://localhost:8000/v1/stream/decide"
    async with websockets.connect(uri) as ws:
        for i in range(5):
            payload = {
                "id": f"evento-{i}",
                "input": f"Tick de mercado: volatilidade de preço BTC/USDT evento #{i}",
                "on_overflow": "truncate_head"
            }
            await ws.send(json.dumps(payload))
            response = await ws.recv()
            print("Resposta recebida:", response)

asyncio.run(decision_stream())
```

---

## 🐘 3. Integração com PHP / Laravel

### A. Utilizando o Laravel HTTP Client (`Http` Facade)
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
     * Avalia uma decisão utilizando o endpoint nativo de alta performance.
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
            throw new RuntimeException("Erro na Laya API: " . $response->body());
        }

        return $response->json();
    }

    /**
     * Avalia utilizando o endpoint compatível com OpenAI Chat Completions.
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

### B. Alta Performance com Unix Domain Socket via cURL Nativo
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
        throw new Exception("Falha na requisição HTTP {$httpCode}: {$result}");
    }

    return json_decode($result, true);
}

// Exemplo de execução
$decision = evaluateViaUDS('/tmp/laya.sock', 'Payload de validação de pedido');
print_r($decision);
```

---

## 🦀 4. Integração com Rust

### A. Utilizando `reqwest` com Pool HTTP/2
Adicione ao `Cargo.toml`:
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
        input: "Verificação de risco para robô de arbitragem de alta frequência",
        on_overflow: "error",
    };

    let res: DecideResponse = client
        .post("http://localhost:8000/v1/decide")
        .json(&req)
        .send()
        .await?
        .json()
        .await?;

    println!("Decisão: {} ({:.2}%) em {:.2}ms [{}]", 
        res.label, res.confidence * 100.0, res.latency_ms, res.backend);

    Ok(())
}
```

### B. Stream Contínuo em WebSocket com `tokio-tungstenite`
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
            "input": format!("Validar transação #{}", i),
            "on_overflow": "truncate_head"
        });

        write.send(Message::Text(msg.to_string())).await?;

        if let Some(Ok(Message::Text(text))) = read.next().await {
            println!("Decisão recebida: {}", text);
        }
    }

    Ok(())
}
```

---

## ☕ 5. Integração com Java

### A. Utilizando o `HttpClient` Padrão (Java 16+)
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
                "input": "Avaliação de risco para transferência de R$ 50.000",
                "on_overflow": "error"
            }
            """;

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:8000/v1/decide"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
        System.out.println("Payload: " + response.body());
        System.out.println("Latência (ms): " + response.headers().firstValue("X-Laya-Latency-Ms").orElse("N/A"));
    }
}
```

### B. Unix Domain Sockets Nativo no Java 16+
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
            String payload = "{\"input\": \"Avaliação de trade de alta frequência\", \"on_overflow\": \"error\"}";
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
            System.out.println("Resposta UDS:\n" + response);
        }
    }
}
```

---

## 🛡️ 6. Boas Práticas para Limites de Contexto

Os modelos Laya possuem limites estritos de tokens (ex: 512 ou 1024 tokens). Configure sempre o `on_overflow` de acordo com o caso de uso:

- `on_overflow: "error"` (**Padrão e Recomendado para Auditoria/Compliance**):
  - Retorna `HTTP 400 Bad Request` se exceder o limite. Garante que nenhuma informação foi suprimida silenciosamente.
- `on_overflow: "truncate_head"` (**Recomendado para Feeds em Tempo Real**):
  - Mantém os dados mais recentes (o final) e descarta o histórico antigo.
## 🧩 7. Avaliações Estruturadas com Múltiplas Perguntas (Multi-Question)

O Laya permite avaliar simultaneamente múltiplas dimensões de decisão em um único forward pass através do dicionário `questions` contendo os question types (`choice`, `score`, `noul`, `guardrail`).

### Exemplo Multi-Question em Python
```python
import httpx

payload = {
    "input": "Fui cobrado duas vezes. Por favor estorne a cobrança duplicada hoje.",
    "questions": {
        "department": {
            "type": "choice",
            "instructions": "Qual time deve tratar este chamado?",
            "criteria": {
                "billing": "faturas, pagamentos, estornos e reembolsos",
                "technical": "bugs, instabilidades e problemas na API",
                "sales": "novas compras e planos empresariais"
            }
        },
        "urgency": {
            "type": "score",
            "instructions": "Quão urgente é esta solicitação?",
            "criteria": ["não urgente", "em breve", "crítica"]
        },
        "refund": {
            "type": "noul",
            "instructions": "O cliente está solicitando dinheiro de volta?"
        }
    }
}

resp = httpx.post("http://localhost:8000/v1/decide", json=payload)
data = resp.json()

print("Departamento:", data["results"]["department"]["decision"]) # -> billing
print("Urgência:", data["results"]["urgency"]["decision"])         # -> em breve (level 1)
print("Solicitou Estorno:", data["results"]["refund"]["decision"]) # -> True
```

### Exemplo Multi-Question em PHP / Laravel
```php
<?php

use Illuminate\Support\Facades\Http;

$payload = [
    'input' => 'Fui cobrado duas vezes. Por favor estorne a cobrança duplicada hoje.',
    'questions' => [
        'department' => [
            'type' => 'choice',
            'instructions' => 'Qual time deve tratar este chamado?',
            'criteria' => [
                'billing' => 'faturas, pagamentos, estornos e reembolsos',
                'technical' => 'bugs, instabilidades e problemas na API',
                'sales' => 'novas compras e planos empresariais'
            ]
        ],
        'urgency' => [
            'type' => 'score',
            'instructions' => 'Quão urgente é esta solicitação?',
            'criteria' => ['não urgente', 'em breve', 'crítica']
        ],
        'refund' => [
            'type' => 'noul',
            'instructions' => 'O cliente está solicitando dinheiro de volta?'
        ]
    ]
];

$response = Http::baseUrl('http://localhost:8000')->post('/v1/decide', $payload);
$results = $response->json('results');

echo "Departamento: " . $results['department']['decision'] . "\n";
echo "Urgência: " . $results['urgency']['decision'] . "\n";
echo "Estorno Solicitado: " . ($results['refund']['decision'] ? 'SIM' : 'NÃO') . "\n";
```

### Exemplo Multi-Question em Rust
```rust
use reqwest::Client;
use serde_json::json;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = Client::new();

    let payload = json!({
        "input": "Fui cobrado duas vezes. Por favor estorne a cobrança duplicada hoje.",
        "questions": {
            "department": {
                "type": "choice",
                "instructions": "Qual time deve tratar este chamado?",
                "criteria": {
                    "billing": "faturas, pagamentos, estornos e reembolsos",
                    "technical": "bugs, instabilidades e problemas na API",
                    "sales": "novas compras e planos empresariais"
                }
            },
            "urgency": {
                "type": "score",
                "instructions": "Quão urgente é esta solicitação?",
                "criteria": ["não urgente", "em breve", "crítica"]
            },
            "refund": {
                "type": "noul",
                "instructions": "O cliente está solicitando dinheiro de volta?"
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

    println!("Resultados Estruturados:\n{}", serde_json::to_string_pretty(&res["results"])?);
    Ok(())
}
```

### Exemplo Multi-Question em Java
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
                "input": "Fui cobrado duas vezes. Por favor estorne a cobrança duplicada hoje.",
                "questions": {
                    "department": {
                        "type": "choice",
                        "instructions": "Qual time deve tratar este chamado?",
                        "criteria": {
                            "billing": "faturas, pagamentos, estornos e reembolsos",
                            "technical": "bugs, instabilidades e problemas na API",
                            "sales": "novas compras e planos empresariais"
                        }
                    },
                    "urgency": {
                        "type": "score",
                        "instructions": "Quão urgente é esta solicitação?",
                        "criteria": ["não urgente", "em breve", "crítica"]
                    },
                    "refund": {
                        "type": "noul",
                        "instructions": "O cliente está solicitando dinheiro de volta?"
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
        System.out.println("Resultados Estruturados:\n" + response.body());
    }
}
```
