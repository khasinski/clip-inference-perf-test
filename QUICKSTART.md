# Fast-CLIP Quick Start Guide

Get up and running in 3 minutes!

## 🚀 Installation

```bash
# Run the setup script (downloads model, converts to ONNX)
./setup.sh
```

This will:
1. Download the M-CLIP model (~1.3GB)
2. Convert it to optimized ONNX format (~535MB)
3. Install all dependencies

**Time:** ~3-5 minutes (depending on internet speed)

## 🏃 Start the Server

```bash
python3 fast_onnx_server.py
```

Server will start on `http://localhost:8000`

You should see:
```
✓ Model loaded with CoreMLExecutionProvider (on Mac)
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 💻 Use the API

### Option 1: Python Client (Easiest)

```python
from client import FastClipClient

client = FastClipClient()

# Single text
embedding = client.encode("Hello world")
print(embedding.shape)  # (1, 512)

# Batch (faster!)
texts = ["Hello", "Bonjour", "Hola"]
embeddings = client.encode(texts)
print(embeddings.shape)  # (3, 512)

# Similarity
score = client.similarity("cat", "feline")
print(score)  # ~0.85
```

### Option 2: Direct HTTP

```bash
curl -X POST http://localhost:8000/encode \
  -H "Content-Type: application/json" \
  -d '{"texts":["Hello world"],"normalize":true}'
```

### Option 3: Any HTTP Library

**JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/encode', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    texts: ['Hello world'],
    normalize: true
  })
});
const data = await response.json();
console.log(data.embeddings);
```

**Go:**
```go
import "bytes"
import "net/http"

payload := []byte(`{"texts":["Hello"],"normalize":true}`)
resp, _ := http.Post("http://localhost:8000/encode",
    "application/json", bytes.NewBuffer(payload))
```

## 🧪 Test It

```bash
# Run the test client
python3 client.py

# Run benchmarks
python3 benchmark.py
python3 load_test.py
```

## ⚡ Performance Tips

1. **Batch your requests** - 10x faster!
   ```python
   # Slow: 10 requests
   for text in texts:
       embed = client.encode(text)

   # Fast: 1 request
   embeddings = client.encode(texts)
   ```

2. **Use normalized embeddings** (default)
   ```python
   client.encode(texts, normalize=True)  # Required for similarity
   ```

3. **Increase concurrency for production**:
   ```bash
   python3 fast_onnx_server.py --limit-concurrency 200
   ```

## 📊 Check Performance

```bash
# Simple benchmark
python3 benchmark.py

# Load test
python3 load_test.py -n 100 -c 10 -b 4
```

Expected on M1 Mac:
- Single text: ~9ms (108 texts/sec)
- Batch of 4: ~5.6ms per text (179 texts/sec)
- Batch of 16: ~4.1ms per text (242 texts/sec)
- Batch of 32: ~3.9ms per text (256 texts/sec)

## 🛑 Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## 📚 Next Steps

- Read [README.md](README.md) for full documentation
- See [BENCHMARKING.md](BENCHMARKING.md) for load testing
- Check [MACOS.md](MACOS.md) for Mac-specific tips

## ❓ Common Issues

**"Connection refused"**
- Make sure server is running: `python3 fast_onnx_server.py`

**"Model not found"**
- Run setup first: `./setup.sh`

**Slow performance**
- Use batching (most important!)
- Check you're using the quantized model
- Increase concurrency: `--limit-concurrency 200`

## 🎯 Example Use Cases

### Semantic Search
```python
# Encode documents
docs = ["Python programming", "Machine learning", "Web development"]
doc_embeds = client.encode(docs)

# Encode query
query_embed = client.encode("AI and ML")

# Find most similar
similarities = query_embed @ doc_embeds.T
best_match = docs[similarities.argmax()]
```

### Multilingual
```python
# Works with 48 languages!
texts = ["Hello", "Bonjour", "Hola", "你好", "こんにちは"]
embeddings = client.encode(texts)
# All embeddings are comparable!
```

### Clustering
```python
import numpy as np
from sklearn.cluster import KMeans

texts = ["cat", "dog", "car", "truck", "apple", "orange"]
embeddings = client.encode(texts)

kmeans = KMeans(n_clusters=3)
clusters = kmeans.fit_predict(embeddings)
```

## 🚀 Production Deployment

See `Dockerfile` and `docker-compose.yml` for containerized deployment.

```bash
docker-compose up
```

That's it! You're ready to go! 🎉
