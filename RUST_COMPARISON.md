# Python vs Rust Server Comparison

## Performance Summary

| Metric | Python | Rust | Winner |
|--------|--------|------|--------|
| **Single Text Latency** | 9.4ms | 10.1ms | Python (7% faster) |
| **Batch Latency (4 texts)** | 22.1ms | 37.0ms | Python (40% faster) |
| **Throughput (50 concurrent)** | 257 req/s | 261 req/s | Rust (1.5% faster) |

## Detailed Results

### Test 1: Single Text Latency (100 sequential requests)

**Python:**
- Mean: 9.36ms
- Median: 8.93ms
- P95: 12.32ms
- P99: 18.72ms

**Rust:**
- Mean: 10.09ms
- Median: 9.03ms
- P95: 17.90ms
- P99: 27.22ms

### Test 2: Batch Processing (batch of 4 texts, 100 sequential requests)

**Python:**
- Mean: 22.06ms
- Median: 21.96ms
- P95: 23.02ms
- P99: 24.00ms

**Rust:**
- Mean: 36.96ms
- Median: 36.62ms
- P95: 40.27ms
- P99: 42.30ms

### Test 3: High Concurrency (50 concurrent clients, 10 seconds)

**Python:**
- Mean: 196.13ms
- Median: 193.09ms
- P95: 246.80ms
- P99: 273.45ms
- Throughput: 257.2 req/s

**Rust:**
- Mean: 193.31ms
- Median: 186.42ms
- P95: 338.06ms
- P99: 415.61ms
- Throughput: 261.1 req/s

## Architecture Differences

### Python Server
- **Framework:** FastAPI + Uvicorn
- **Concurrency:** Async with thread pool executor
- **ONNX:** Single session with multi-threading (num_cpus/2 threads)
- **Memory:** ~2GB (1 model instance)

### Rust Server
- **Framework:** Axum + Tokio
- **Concurrency:** Session pool (one session per CPU core)
- **ONNX:** Multiple sessions with 2 threads each
- **Memory:** ~2GB × num_cpus (multiple model instances)

## Analysis

### Why Python is Faster for Batches
The Python server uses a single ONNX session with more threads allocated for inference. When processing a batch, all available CPU cores can work on the single batch.

The Rust server uses a session pool where each session has fewer threads. While this improves concurrency for multiple requests, it reduces performance for individual batches.

### Why Rust is (Slightly) Better Under Load
The Rust server's session pool allows true parallel processing of multiple requests. When 50 concurrent requests arrive, they can be distributed across multiple session instances, reducing contention.

The Python server uses async + thread pool, which works well but still has some overhead from the GIL and async coordination.

### Trade-offs

**Use Python when:**
- Processing large batches is common
- You want simpler deployment and lower memory usage
- Single-request latency is critical
- You need easy integration with Python ecosystem

**Use Rust when:**
- High concurrency is the priority
- You have plenty of RAM for multiple model instances
- You want a single binary deployment
- You prefer static typing and memory safety

## Recommendation

**For this use case, Python is the better choice:**
1. Lower latency for both single and batch requests
2. Lower memory footprint (1 model vs N models)
3. Easier to maintain and extend
4. Performance difference under load is negligible (1.5%)

The Rust implementation is a good learning exercise and shows that Rust can match Python's performance, but the complexity and memory overhead don't justify the minimal throughput gain.

## Hardware Used
- Apple Silicon Mac (M-series)
- num_cpus: varies by machine
- Model: M-CLIP XLM-Roberta-Large-Vit-B-32 (INT8 quantized)
