# Laya API

<p align="center">
  <strong>Ultra-Fast OpenAI & Anthropic-Compatible Inference API for Laya & Laya-MLX Models</strong>
</p>

<p align="center">
  <a href="README.pt-BR.md">Português</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.md">English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Backend-Apple_Silicon_MLX_%7C_NVIDIA_CUDA_%7C_PyTorch-green.svg" alt="Backend Support">
  <img src="https://img.shields.io/badge/Protocol-OpenAI_%2F_Anthropic_%2F_UDS_%2F_WebSocket-orange.svg" alt="Protocols">
  <img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License">
</p>

---

## ⚡ Overview

**Laya API** exposes high-speed OpenAI (`/v1/chat/completions`) and Anthropic (`/v1/messages`) compatible REST APIs, alongside low-handshake **Unix Domain Sockets (UDS)** and **WebSockets**, for [Laya](https://github.com/NandhaKishorM/laya) and [Laya-MLX](https://github.com/mizorewww/laya-mlx) models.

Laya is a non-autoregressive "System 1" decision engine designed for fast, typed evaluations (classification, scoring, guardrails, routing, and calibrated probabilities) in a **single forward pass** (~7–14 ms latency).

---

## 🚀 Key Features

- **Standard Compatibility**: Plug-and-play support with standard OpenAI and Anthropic SDKs (Python, TypeScript/JavaScript, Go, Rust, Java, C#, etc.).
- **Hardware Acceleration**:
  - **macOS (Apple Silicon)**: Native [MLX](https://github.com/mizorewww/laya-mlx) engine with zero PyTorch overhead on Unified Memory.
  - **Linux / Cloud**: PyTorch backend with NVIDIA CUDA and CPU acceleration.
- **Low-Handshake Transports**:
  - **Unix Domain Sockets (`http+unix://`)**: Sub-millisecond Inter-Process Communication (IPC) for co-located agents.
  - **HTTP/2 Keep-Alive**: Persistent connection pooling for client SDKs.
  - **WebSockets (`/v1/stream/decide`)**: Duplex connection for continuous real-time loops.
- **Context Limit Protection**: Strict pre-flight tokenization validation to prevent Out-Of-Memory (OOM) and truncation runtime crashes.
- **Zero Cold Start**: Guaranteed model pre-loading and JIT warm-up during boot before accepting traffic.

---

## 🏎️ Performance & Latency Benchmarks

| Platform / Backend | Transport Protocol | Forward Pass | Network Overhead | Total End-to-End Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Apple M3 Max (MLX)** | Unix Domain Socket (UDS) | 7.2 ms | < 0.3 ms | **7.5 ms** |
| **Apple M3 Max (MLX)** | HTTP/2 (Keep-Alive) | 7.2 ms | ~ 1.2 ms | **8.4 ms** |
| **NVIDIA RTX 4090 (CUDA)** | Unix Domain Socket (UDS) | 5.8 ms | < 0.3 ms | **6.1 ms** |
| **NVIDIA RTX 4090 (CUDA)** | HTTP/2 (Keep-Alive) | 5.8 ms | ~ 1.0 ms | **6.8 ms** |

---

## 📦 Quickstart

### 1. Local Installation (macOS & Linux)

```bash
# Clone the repository
git clone https://github.com/your-org/laya-api.git
cd laya-api

# Install dependencies (using uv or pip)
pip install -e .

# Check hardware and backend compatibility
laya-api doctor

# Start the server (Auto-detects Apple Silicon MLX or NVIDIA CUDA)
laya-api serve --port 8000
```

### 2. Docker Deployment (Linux CUDA / CPU)

> [!NOTE]
> On macOS, use local native execution (`laya-api serve`) to utilize Apple Silicon MLX GPU acceleration. Docker on macOS does not support Metal/GPU passthrough.

```bash
# NVIDIA CUDA (GPU Accelerated)
docker build -f docker/Dockerfile.cuda -t laya-api:cuda .
docker run --gpus all -p 8000:8000 laya-api:cuda

# CPU Fallback
docker build -f docker/Dockerfile.cpu -t laya-api:cpu .
docker run -p 8000:8000 laya-api:cpu
```

---

## 💻 Code Examples

### Using OpenAI Python SDK
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="laya-base",
    messages=[
        {"role": "user", "content": "Classify support ticket: 'Payment failed for invoice #102'"}
    ]
)

print(response.choices[0].message.content)
```

### Using Anthropic Python SDK
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
        {"role": "user", "content": "Evaluate trading risk for BTC/USDT scalp signal"}
    ]
)

print(message.content[0].text)
```

### High-Frequency Loop via Unix Domain Socket
```python
import httpx

# Connect over Unix Domain Socket for zero-network overhead
transport = httpx.HTTPTransport(uds="/tmp/laya.sock")
client = httpx.Client(transport=transport, base_url="http://localhost")

for order in stream_orders():
    res = client.post("/v1/decide", json={"input": order.raw_text})
    decision = res.json()
    if decision["label"] == "APPROVE":
        execute(order)
```

---

## ⚙️ Configuration & Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LAYA_MODEL` | `nandhakishorm/laya-base` | Model HuggingFace ID or local weights path |
| `LAYA_BACKEND` | `auto` | Backend engine: `auto`, `mlx`, `torch_cuda`, `torch_cpu` |
| `LAYA_HOST` | `0.0.0.0` | Host IP to bind TCP listener |
| `LAYA_PORT` | `8000` | Port for HTTP/2 and WebSocket server |
| `LAYA_SOCKET_PATH` | `/tmp/laya.sock` | Path to Unix Domain Socket (optional) |
| `LAYA_MAX_CONTEXT` | `1024` | Maximum token limit for context window validation |
| `LAYA_ON_OVERFLOW` | `error` | Handling for context overflow: `error`, `truncate_head`, `truncate_tail` |

---

## 📚 Documentation

- [Multi-Language Integration & Protocol HOW-TO Guide](docs/HOW_TO_GUIDE.md)
- [Payload Formats & Question Types Specification](docs/PAYLOAD_FORMATS.md)
- [Versioning & Release Strategy](docs/VERSIONING_AND_RELEASES.md)
- [Docker Hub & CI/CD Setup Guide](docs/DOCKER_HUB_SETUP.md)
- [Architecture Specification](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

---

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
