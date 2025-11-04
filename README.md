# ⚡ Fast-CLIP: Ultra-Fast M-CLIP Text Inference

Blazing fast inference for M-CLIP text embeddings with multiple optimization levels.

**✅ Fully tested on macOS (Intel & Apple Silicon)**

## 🚀 Quick Start

### Automated Setup (Recommended)

```bash
./setup.sh
```

### Manual Setup

```bash
pip3 install -r requirements.txt
python3 convert_to_onnx.py
```

This downloads the model and creates an optimized quantized ONNX version.

### Step 2: Start the Server

```bash
# Basic (100 concurrent connections)
python3 fast_onnx_server.py

# High concurrency (200 concurrent connections)
python3 fast_onnx_server.py --limit-concurrency 200 --backlog 4096

# Or use the convenience script
./start_server.sh

# With Gunicorn (production)
gunicorn -c gunicorn_config.py fast_onnx_server:app
```

### Step 3: Run Inference

```python
import requests
import numpy as np

response = requests.post(
    "http://localhost:8000/encode",
    json={"texts": ["Hello world", "Bonjour"], "normalize": True}
)

embeddings = np.array(response.json()["embeddings"])
print(f"Shape: {embeddings.shape}")
```

## 📊 Benchmarking

### Simple Benchmark

```bash
python3 benchmark.py
```

### Load Testing (Apache Benchmark Style)

**Python Load Tester (Recommended):**
```bash
# Basic test
python3 load_test.py

# Custom load test
python3 load_test.py --requests 500 --concurrency 50 --batch-size 8
```

**Curl Benchmark (Simple):**
```bash
./bench_curl.sh http://localhost:8000/encode 100
```

**Apache Benchmark (if installed):**
```bash
./bench_ab.sh http://localhost:8000/encode 100 10
```

**wrk (if installed):**
```bash
wrk -t4 -c100 -d30s -s bench_wrk.lua http://localhost:8000/encode
```

See [BENCHMARKING.md](BENCHMARKING.md) for detailed benchmarking guide.

Expected performance (tested on M1 Mac):
- **Single text**: ~9ms (108 texts/sec)
- **Batch of 4**: ~5.6ms per text (179 texts/sec)
- **Batch of 16**: ~4.1ms per text (242 texts/sec)
- **Batch of 32**: ~3.9ms per text (256 texts/sec!)
- **PyTorch baseline**: ~50-100ms per text

**Speedup: 10-25x faster than PyTorch!**

## 🎯 Why This is Fast

1. **ONNX Runtime**: Optimized graph execution
2. **INT8 Quantization**: 4x smaller, 2-3x faster
3. **Graph Optimization**: Fused operations, constant folding
4. **Batch Processing**: Vectorized operations
5. **Async Execution**: Non-blocking concurrent request handling
6. **Thread Pool**: Parallel CPU-bound inference

## 📦 What Gets Created

```
./model/
  ├── model.onnx              # Base ONNX model (~1.3GB)
  ├── model_quantized.onnx    # INT8 quantized (~350MB) ← USE THIS
  ├── tokenizer.json          # Fast tokenizer
  └── tokenizer_config.json   # Tokenizer config
```

## 🔥 Performance Tips

1. **Always batch requests** - 2.4x faster throughput
2. **Use appropriate batch sizes** - 16-32 for optimal throughput/latency
3. **Increase concurrency** - Use `--limit-concurrency 200` for high load
4. **Use Gunicorn** - Better process management in production

## API Reference

### POST /encode

```json
{
  "texts": ["text1", "text2"],
  "normalize": true
}
```

Response:
```json
{
  "embeddings": [[...], [...]],
  "shape": [2, 768]
}
```

### GET /health

Check server status.

## Requirements

- Python 3.8+
- 2GB RAM minimum
- **macOS**: Works on both Intel and Apple Silicon (M1/M2/M3)
- **Linux/Windows**: Also supported

## Performance

Tested on M1 MacBook Pro:
- Single text: ~9ms (108 texts/sec)
- Batch of 4: ~5.6ms per text (179 texts/sec)
- Batch of 16: ~4.1ms per text (242 texts/sec)
- Batch of 32: ~3.9ms per text (256 texts/sec!)

The quantized ONNX model with optimized CPU execution provides excellent performance on modern hardware without requiring GPUs.

## License

MIT
