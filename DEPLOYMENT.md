# Production Deployment Guide

## Concurrency & Performance

### Understanding Concurrency

The server handles concurrency at multiple levels:

1. **Workers**: Separate processes (each loads model ~2GB RAM)
2. **Async concurrency**: Single worker handles many requests simultaneously
3. **Thread pool**: CPU-bound inference runs in threads

### Recommended Configuration

#### Development (1-10 req/sec)
```bash
python3 fast_onnx_server.py
# Default: 1 worker, 100 concurrent connections
```

#### Production - Single Server (10-100 req/sec)
```bash
python3 fast_onnx_server.py \
    --workers 1 \
    --limit-concurrency 200 \
    --backlog 2048
```

**Why 1 worker?**
- Each worker loads model (~2GB RAM)
- Async + thread pool provides excellent concurrency
- Avoids memory overhead

#### Production - High Load (100+ req/sec)
```bash
# Option 1: Multiple workers (needs more RAM)
python3 fast_onnx_server.py \
    --workers 2 \
    --limit-concurrency 200 \
    --backlog 2048
# Memory: ~4GB (2 workers × 2GB)

# Option 2: Better - Multiple instances + load balancer
# See "Load Balancing" section below
```

### Using Gunicorn (Production-Ready)

Gunicorn provides better process management:

```bash
# Install
pip install gunicorn

# Run
gunicorn -c gunicorn_config.py fast_onnx_server:app

# Custom workers
WORKERS=2 gunicorn -c gunicorn_config.py fast_onnx_server:app
```

**Benefits:**
- Automatic worker restart on failure
- Graceful shutdown/reload
- Better monitoring
- Production-tested

### Quick Start Script

```bash
# Simple start
./start_server.sh

# Custom concurrency
CONCURRENCY=500 ./start_server.sh

# Custom workers (more RAM needed)
WORKERS=2 CONCURRENCY=200 ./start_server.sh
```

## Performance Tuning

### 1. Thread Pool Size

ONNX Runtime uses multiple threads:
- Default: 50% of CPU cores
- Adjust in `fast_onnx_server.py:36-37`

```python
num_threads = max(1, os.cpu_count() // 2)  # Current
num_threads = os.cpu_count()  # Use all cores (may be slower)
```

### 2. Connection Limits

```bash
# Max concurrent connections
--limit-concurrency 200  # Default: 100

# Connection backlog (queue)
--backlog 2048  # Default: 2048
```

### 3. Batch Size

Larger batches = better throughput, higher latency:

| Batch Size | Latency | Throughput | Use Case |
|------------|---------|------------|----------|
| 1          | 9ms     | 108/sec    | Real-time API |
| 4-8        | 20-40ms | 180/sec    | Interactive |
| 16-32      | 60-125ms| 250/sec    | Batch processing |

**Client-side batching:**
```python
# Good - batch multiple texts
embeddings = client.encode(["text1", "text2", "text3"])

# Better - even larger batches for throughput
embeddings = client.encode(texts_list)  # 16-32 texts
```

## Load Balancing

For >250 texts/sec, use multiple instances:

### Option 1: Nginx Load Balancer

**nginx.conf:**
```nginx
upstream fast_clip {
    least_conn;  # Or: round_robin, ip_hash
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}

server {
    listen 8000;

    location / {
        proxy_pass http://fast_clip;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

**Start multiple instances:**
```bash
# Terminal 1
python3 fast_onnx_server.py --port 8001

# Terminal 2
python3 fast_onnx_server.py --port 8002

# Terminal 3
python3 fast_onnx_server.py --port 8003

# Terminal 4
python3 fast_onnx_server.py --port 8004
```

**Result:** 1000+ texts/sec (4 × 250/sec)

### Option 2: Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "8000:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - fast-clip-1
      - fast-clip-2
      - fast-clip-3
      - fast-clip-4

  fast-clip-1:
    build: .
    environment:
      - PORT=8001

  fast-clip-2:
    build: .
    environment:
      - PORT=8002

  fast-clip-3:
    build: .
    environment:
      - PORT=8003

  fast-clip-4:
    build: .
    environment:
      - PORT=8004
```

```bash
docker-compose up -d --scale fast-clip=4
```

### Option 3: Kubernetes

For cloud deployment, see `k8s/` directory (if available) or use:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fast-clip
spec:
  replicas: 4
  selector:
    matchLabels:
      app: fast-clip
  template:
    metadata:
      labels:
        app: fast-clip
    spec:
      containers:
      - name: fast-clip
        image: fast-clip:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "3Gi"
            cpu: "2"
---
apiVersion: v1
kind: Service
metadata:
  name: fast-clip
spec:
  selector:
    app: fast-clip
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

## Monitoring

### Health Checks

```bash
# Check if server is ready
curl http://localhost:8000/health

# Response:
# {"status": "ready", "provider": "CPUExecutionProvider"}
```

### Metrics

Add Prometheus metrics (optional):

```bash
pip install prometheus-fastapi-instrumentator
```

```python
# Add to fast_onnx_server.py
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Logging

```bash
# View logs
tail -f /var/log/fast-clip.log

# Or with gunicorn
gunicorn ... --access-logfile /var/log/access.log --error-logfile /var/log/error.log
```

## Resource Requirements

### Memory

| Configuration | RAM Needed | Max Throughput |
|---------------|------------|----------------|
| 1 worker      | 2GB        | 250/sec        |
| 2 workers     | 4GB        | 500/sec        |
| 4 workers     | 8GB        | 1000/sec       |

### CPU

- **Recommended**: 4+ cores
- **Minimum**: 2 cores
- More cores = better performance for concurrent requests

### Disk

- Model: 535MB
- Total: 1GB (with dependencies)

## Testing Concurrency

### 1. Concurrent Requests Test

```bash
# Test with 50 concurrent requests
python3 load_test.py -n 500 -c 50 -b 4
```

### 2. Sustained Load Test

```bash
# 5 minute sustained load
wrk -t8 -c100 -d300s -s bench_wrk.lua http://localhost:8000/encode
```

### 3. Spike Test

```bash
# Quick spike of 200 concurrent
python3 load_test.py -n 1000 -c 200 -b 8
```

## Troubleshooting

### High Latency

1. **Check concurrency limits:**
   ```bash
   --limit-concurrency 500  # Increase
   ```

2. **Check batch size:**
   - Larger batches = higher latency but better throughput

3. **Check CPU usage:**
   ```bash
   htop  # Should use multiple cores
   ```

### Connection Refused / Timeout

1. **Increase backlog:**
   ```bash
   --backlog 4096
   ```

2. **Increase timeout:**
   ```bash
   --timeout-keep-alive 10
   ```

### Memory Issues

1. **Reduce workers:**
   ```bash
   --workers 1  # Each worker = 2GB RAM
   ```

2. **Use load balancer instead**

### Slow Startup

- Normal: Model loading takes 5-10 seconds
- First request may be slower (warmup)

## Best Practices

1. ✅ **Single worker + high concurrency** for best RAM efficiency
2. ✅ **Use load balancer** for scaling beyond 250 texts/sec
3. ✅ **Always batch requests** client-side
4. ✅ **Set appropriate timeouts** (60-120s for large batches)
5. ✅ **Monitor health endpoint** for uptime checks
6. ✅ **Use gunicorn in production** for process management
7. ✅ **Set resource limits** in containers
8. ⚠️ **Don't use too many workers** (wastes RAM)
9. ⚠️ **Don't send huge batches** (>64 texts) in single request

## Example Production Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Convert model (one time)
python3 convert_to_onnx.py

# 3. Start with gunicorn
gunicorn -c gunicorn_config.py fast_onnx_server:app

# 4. Test
curl -X POST http://localhost:8000/encode \
  -H "Content-Type: application/json" \
  -d '{"texts":["test"]}'

# 5. Monitor
curl http://localhost:8000/health
```

## Cloud Deployment

### AWS EC2
- **Instance**: c6i.2xlarge (8 vCPU, 16GB RAM)
- **Expected**: 500-1000 texts/sec (2-4 workers)

### Google Cloud
- **Instance**: c2-standard-8 (8 vCPU, 32GB RAM)
- **Expected**: 1000+ texts/sec (4-8 workers)

### Azure
- **Instance**: F8s_v2 (8 vCPU, 16GB RAM)
- **Expected**: 500-1000 texts/sec (2-4 workers)

### Docker (Optional)

If you want to use Docker, create a simple Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Convert model during build
RUN python3 convert_to_onnx.py

EXPOSE 8000

CMD ["python3", "fast_onnx_server.py", "--limit-concurrency", "200"]
```

Build and run:
```bash
docker build -t fast-clip .
docker run -p 8000:8000 fast-clip
```
