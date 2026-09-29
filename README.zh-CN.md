# Laya API

<p align="center">
  <strong>专为 Laya 与 Laya-MLX 决策模型打造的超低延迟 OpenAI 与 Anthropic 兼容推理服务</strong>
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

## ⚡ 概述

**Laya API** 是一个高性能推理服务器，专为 [Laya](https://github.com/NandhaKishorM/laya) 和 [Laya-MLX](https://github.com/mizorewww/laya-mlx) 模型提供与 OpenAI (`/v1/chat/completions`) 和 Anthropic (`/v1/messages`) 兼容的标准接口，并提供超低握手开销的 **Unix Domain Socket (UDS)** 和 **WebSocket** 通信支持。

Laya 是非自回归的“系统 1 (System 1)”快速决策引擎，可在**单次前向传播 (single forward pass)** 中完成结构化分类、评分、安全护栏、路由与校准概率评估（延迟仅约 7–14 毫秒）。

---

## 🚀 核心特性

- **标准兼容**：开箱即用支持主流编程语言（Python、TypeScript/JavaScript、Go、Rust、Java、C# 等）的 OpenAI 与 Anthropic 官方 SDK。
- **硬件原生加速**：
  - **macOS (Apple Silicon)**：原生 [MLX](https://github.com/mizorewww/laya-mlx) 运行时，基于统一内存架构 (Unified Memory) 实现零 PyTorch 开销加速。
  - **Linux / 云端**：PyTorch 后端，支持 NVIDIA CUDA GPU 与 CPU 加速。
- **低握手传输协议**：
  - **Unix Domain Socket (`http+unix://`)**：同机进程间通信 (IPC) 延迟低于 0.3 毫秒。
  - **HTTP/2 Keep-Alive**：长连接池复用，消除频繁握手开销。
  - **WebSocket (`/v1/stream/decide`)**：双向全双工长连接，适合高频循环调用（如量化交易策略与实时风控）。
- **上下文长度严格校验**：请求接入层（Middleware）精准分词校验，防止因超长输入引发 OOM 或静默截断异常。
- **零冷启动 (Zero Cold Start)**：服务启动阶段强制预加载模型并执行 JIT 预热（Warm-up），确保首次调用即达最高性能。

---

## 🏎️ 性能与延迟基准

| 平台 / 后端 | 传输协议 | 前向推理耗时 | 网络与握手开销 | 端到端总延迟 |
| :--- | :--- | :--- | :--- | :--- |
| **Apple M3 Max (MLX)** | Unix Domain Socket (UDS) | 7.2 ms | < 0.3 ms | **7.5 ms** |
| **Apple M3 Max (MLX)** | HTTP/2 (Keep-Alive) | 7.2 ms | ~ 1.2 ms | **8.4 ms** |
| **NVIDIA RTX 4090 (CUDA)** | Unix Domain Socket (UDS) | 5.8 ms | < 0.3 ms | **6.1 ms** |
| **NVIDIA RTX 4090 (CUDA)** | HTTP/2 (Keep-Alive) | 5.8 ms | ~ 1.0 ms | **6.8 ms** |

---

## 📦 快速开始

### 1. 本地安装（macOS 与 Linux）

```bash
# 克隆仓库
git clone https://github.com/your-org/laya-api.git
cd laya-api

# 安装依赖（推荐使用 uv 或 pip）
pip install -e .

# 检查环境兼容性与硬件支持
laya-api doctor

# 启动服务（自动识别 Apple Silicon MLX 或 NVIDIA CUDA）
laya-api serve --port 8000
```

### 2. Docker 部署（Linux CUDA / CPU）

> [!NOTE]
> 在 macOS 上，请使用本地终端运行 (`laya-api serve`) 以获得 Apple Silicon MLX GPU 加速。macOS 上的 Docker 运行于 Linux 虚拟机中，无法调用 Metal GPU。

```bash
# NVIDIA CUDA（GPU 加速）
docker build -f docker/Dockerfile.cuda -t laya-api:cuda .
docker run --gpus all -p 8000:8000 laya-api:cuda

# CPU 模式
docker build -f docker/Dockerfile.cpu -t laya-api:cpu .
docker run -p 8000:8000 laya-api:cpu
```

---

## 💻 代码示例

### 使用 OpenAI Python SDK
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="laya-base",
    messages=[
        {"role": "user", "content": "请评估该工单分类：'发票 #102 支付失败'"}
    ]
)

print(response.choices[0].message.content)
```

### 使用 Anthropic Python SDK
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
        {"role": "user", "content": "评估 BTC/USDT 短线交易信号的执行风险"}
    ]
)

print(message.content[0].text)
```

### 高频循环调用（通过 Unix Domain Socket）
```python
import httpx

# 使用 Unix Domain Socket 消除网络栈开销
transport = httpx.HTTPTransport(uds="/tmp/laya.sock")
client = httpx.Client(transport=transport, base_url="http://localhost")

for order in stream_orders():
    res = client.post("/v1/decide", json={"input": order.raw_text})
    decision = res.json()
    if decision["label"] == "APPROVE":
        execute(order)
```

---

## ⚙️ 环境变量与配置项

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `LAYA_MODEL` | `nandhakishorm/laya-base` | HuggingFace 模型 ID 或本地权重路径 |
| `LAYA_BACKEND` | `auto` | 推理引擎选择：`auto`、`mlx`、`torch_cuda`、`torch_cpu` |
| `LAYA_HOST` | `0.0.0.0` | TCP 监听地址 |
| `LAYA_PORT` | `8000` | HTTP/2 与 WebSocket 监听端口 |
| `LAYA_SOCKET_PATH` | `/tmp/laya.sock` | Unix Domain Socket 文件路径（可选） |
| `LAYA_MAX_CONTEXT` | `1024` | 上下文窗口最大 Token 校验限制 |
| `LAYA_ON_OVERFLOW` | `error` | 上下文超长策略：`error`、`truncate_head`、`truncate_tail` |

---

## 📚 详细文档

- [多语言集成与协议实战指南 (HOW-TO)](docs/HOW_TO_GUIDE.zh-CN.md)
- [载荷格式与问题类型规范 (Payload Formats & Question Types)](docs/PAYLOAD_FORMATS.md)
- [系统架构设计文档 (Architecture)](docs/ARCHITECTURE.md)
- [API 接口参考手册 (API Reference)](docs/API_REFERENCE.md)
- [部署指南 (Deployment)](docs/DEPLOYMENT.md)

---

## 📄 开源许可证

本项目基于 Apache 2.0 许可证开源 - 详见 [LICENSE](LICENSE) 文件。
