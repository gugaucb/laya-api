# Laya API

<p align="center">
  <strong>API de Inferência de Ultra-Baixa Latência Compatível com OpenAI e Anthropic para Modelos Laya e Laya-MLX</strong>
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

## ⚡ Visão Geral

O **Laya API** disponibiliza APIs REST de alta velocidade compatíveis com os padrões OpenAI (`/v1/chat/completions`) e Anthropic (`/v1/messages`), além de protocolos de baixo handshake como **Unix Domain Sockets (UDS)** e **WebSockets**, para os modelos [Laya](https://github.com/NandhaKishorM/laya) e [Laya-MLX](https://github.com/mizorewww/laya-mlx).

O Laya é um motor de decisão não-autoregressivo ("System 1") projetado para avaliações estruturadas (classificação, scoring, guardrails, roteamento e probabilidades calibradas) em um **único forward pass** (~7–14 ms de latência).

---

## 🚀 Principais Recursos

- **Compatibilidade Padrão**: Funciona de forma transparente com SDKs oficiais da OpenAI e Anthropic em qualquer linguagem de programação (Python, TypeScript/JavaScript, Go, Rust, Java, C#, etc.).
- **Aceleração Nativa de Hardware**:
  - **macOS (Apple Silicon)**: Motor [MLX](https://github.com/mizorewww/laya-mlx) nativo sem overhead de PyTorch na Unified Memory.
  - **Linux / Cloud**: Backend PyTorch com suporte a NVIDIA CUDA e CPU.
- **Transportes de Baixo Handshake**:
  - **Unix Domain Sockets (`http+unix://`)**: IPC com latência de sub-milissegundo para agentes rodando na mesma máquina.
  - **HTTP/2 Keep-Alive**: Pool de conexões persistentes para SDKs clientes.
  - **WebSockets (`/v1/stream/decide`)**: Conexão duplex contínua para loops em tempo real.
- **Proteção de Janela de Contexto**: Validação estrita de tokenização na ingestão da requisição para prevenir erros de estouro de memória (OOM) ou truncamento indesejado.
- **Zero Cold Start**: Pré-carregamento do modelo e aquecimento (warm-up JIT) obrigatório no boot antes de abrir as portas de rede.

---

## 🏎️ Benchmarks de Desempenho e Latência

| Plataforma / Backend | Protocolo de Transporte | Forward Pass | Overhead de Rede | Latência Total Ponta a Ponta |
| :--- | :--- | :--- | :--- | :--- |
| **Apple M3 Max (MLX)** | Unix Domain Socket (UDS) | 7.2 ms | < 0.3 ms | **7.5 ms** |
| **Apple M3 Max (MLX)** | HTTP/2 (Keep-Alive) | 7.2 ms | ~ 1.2 ms | **8.4 ms** |
| **NVIDIA RTX 4090 (CUDA)** | Unix Domain Socket (UDS) | 5.8 ms | < 0.3 ms | **6.1 ms** |
| **NVIDIA RTX 4090 (CUDA)** | HTTP/2 (Keep-Alive) | 5.8 ms | ~ 1.0 ms | **6.8 ms** |

---

## 📦 Início Rápido

### 1. Instalação Local (macOS e Linux)

```bash
# Clone o repositório
git clone https://github.com/your-org/laya-api.git
cd laya-api

# Instale as dependências (via uv ou pip)
pip install -e .

# Valide a compatibilidade de hardware e backends
laya-api doctor

# Inicie o servidor (detecta automaticamente Apple Silicon MLX ou NVIDIA CUDA)
laya-api serve --port 8000
```

### 2. Execução via Docker (Linux CUDA / CPU)

> [!NOTE]
> No macOS, utilize a execução nativa local (`laya-api serve`) para ter aceleração via GPU/Metal com MLX. O Docker no macOS roda sobre VM Linux e não tem acesso ao Metal.

```bash
# NVIDIA CUDA (Acelerado por GPU)
docker build -f docker/Dockerfile.cuda -t laya-api:cuda .
docker run --gpus all -p 8000:8000 laya-api:cuda

# CPU Fallback
docker build -f docker/Dockerfile.cpu -t laya-api:cpu .
docker run -p 8000:8000 laya-api:cpu
```

---

## 💻 Exemplos de Código

### Usando o SDK OpenAI em Python
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="laya-base",
    messages=[
        {"role": "user", "content": "Classificar ticket de suporte: 'Falha no pagamento da fatura #102'"}
    ]
)

print(response.choices[0].message.content)
```

### Usando o SDK Anthropic em Python
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
        {"role": "user", "content": "Avaliar risco da operação de trade para o par BTC/USDT"}
    ]
)

print(message.content[0].text)
```

### Loop de Alta Frequência via Unix Domain Socket
```python
import httpx

# Conexão via Unix Domain Socket para overhead zero de rede
transport = httpx.HTTPTransport(uds="/tmp/laya.sock")
client = httpx.Client(transport=transport, base_url="http://localhost")

for order in stream_orders():
    res = client.post("/v1/decide", json={"input": order.raw_text})
    decision = res.json()
    if decision["label"] == "APPROVE":
        execute(order)
```

---

## ⚙️ Variáveis de Ambiente e Configuração

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `LAYA_MODEL` | `nandhakishorm/laya-base` | ID do HuggingFace ou caminho local dos pesos |
| `LAYA_BACKEND` | `auto` | Motor de inferência: `auto`, `mlx`, `torch_cuda`, `torch_cpu` |
| `LAYA_HOST` | `0.0.0.0` | Endereço IP do servidor TCP |
| `LAYA_PORT` | `8000` | Porta para o servidor HTTP/2 e WebSocket |
| `LAYA_SOCKET_PATH` | `/tmp/laya.sock` | Caminho do Unix Domain Socket (opcional) |
| `LAYA_MAX_CONTEXT` | `1024` | Limite máximo de tokens para validação de contexto |
| `LAYA_ON_OVERFLOW` | `error` | Comportamento ao exceder limite: `error`, `truncate_head`, `truncate_tail` |

---

## 📚 Documentação Adicional

- [Especificação de Arquitetura](docs/ARCHITECTURE.md)
- [Referência da API](docs/API_REFERENCE.md)
- [Guia de Deploy](docs/DEPLOYMENT.md)

---

## 📄 Licença

Este projeto é distribuído sob a licença Apache 2.0 - veja o arquivo [LICENSE](LICENSE) para mais detalhes.
