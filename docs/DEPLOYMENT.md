# Laya API Deployment Guide

This guide covers production deployment patterns for **Laya API** across macOS (Apple Silicon native) and Linux environments (Docker with NVIDIA CUDA and CPU).

---

## 1. Apple Silicon Native Deployment (macOS)

For macOS machines (M1, M2, M3, M4), the native MLX engine runs directly against Apple's Unified Memory with Metal GPU acceleration.

### A. Run with `uv` (Recommended)
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run directly from source with automated environment creation
uv run laya-api serve --port 8000 --socket /tmp/laya.sock
```

### B. Setup as a macOS `launchd` Service
Create `~/Library/LaunchAgents/com.laya.api.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.laya.api</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/laya-api</string>
        <string>serve</string>
        <string>--port</string>
        <string>8000</string>
        <string>--socket</string>
        <string>/tmp/laya.sock</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/laya-api.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/laya-api.err</string>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.laya.api.plist
```

---

## 2. Docker Deployment (Linux / Cloud)

### A. NVIDIA CUDA GPU Acceleration
Requires [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).

#### Build & Run:
```bash
docker build -f docker/Dockerfile.cuda -t laya-api:cuda .

docker run -d \
  --name laya-api \
  --gpus all \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /var/run/laya:/var/run/laya \
  -e LAYA_SOCKET_PATH=/var/run/laya/laya.sock \
  laya-api:cuda
```

### B. CPU Mode
For instances without dedicated GPUs:
```bash
docker build -f docker/Dockerfile.cpu -t laya-api:cpu .

docker run -d \
  --name laya-api \
  --restart unless-stopped \
  -p 8000:8000 \
  laya-api:cpu
```

---

## 3. Kubernetes Deployment (NVIDIA GPU)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: laya-api
  labels:
    app: laya-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: laya-api
  template:
    metadata:
      labels:
        app: laya-api
    spec:
      containers:
      - name: laya-api
        image: laya-api:cuda
        ports:
        - containerPort: 8000
        env:
        - name: LAYA_MODEL
          value: "nandhakishorm/laya-base"
        - name: LAYA_BACKEND
          value: "torch_cuda"
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: 4Gi
            cpu: "2"
          requests:
            nvidia.com/gpu: 1
            memory: 2Gi
            cpu: "1"
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: laya-api-service
spec:
  selector:
    app: laya-api
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```
