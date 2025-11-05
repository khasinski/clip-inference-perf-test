# Server Performance Comparison: Python vs Rust vs Elixir vs Ruby

## Summary Results

| Metric | Python | Rust | Elixir | Ruby | Winner |
|--------|--------|------|--------|------|--------|
| **Single Text Latency** | 10.0ms | 10.1ms | 9.8ms | 9.1ms | **Ruby** (9% faster than Python, 10% faster than Rust) |
| **Batch Latency (4 texts)** | 23.6ms | 38.0ms | 24.4ms | 22.7ms | **Ruby** (4% faster than Python, 40% faster than Rust) |
| **Throughput (50 concurrent)** | 252 req/s | 225 req/s | 114 req/s | 131 req/s | **Python** (12% more than Rust, 121% more than Elixir) |

**Ruby wins latency tests, Python wins throughput!**

## Detailed Test Results

### Test 1: Single Text Latency (100 sequential requests)

| Server | Mean | Median | P95 | P99 |
|--------|------|--------|-----|-----|
| Ruby | 9.1ms | 9.0ms | 10.4ms | 11.2ms |
| Elixir | 9.8ms | 9.7ms | 11.2ms | 12.1ms |
| Python | 10.0ms | 9.9ms | 10.8ms | 11.5ms |
| Rust | 10.1ms | 10.0ms | 11.0ms | 11.8ms |

### Test 2: Batch Processing (batch of 4 texts, 100 sequential requests)

| Server | Mean | Median | P95 | P99 |
|--------|------|--------|-----|-----|
| Ruby | 22.7ms | 22.5ms | 24.1ms | 25.8ms |
| Python | 23.6ms | 23.4ms | 25.0ms | 26.2ms |
| Elixir | 24.4ms | 24.2ms | 26.5ms | 28.1ms |
| Rust | 38.0ms | 37.8ms | 40.2ms | 43.5ms |

### Test 3: High Concurrency (50 concurrent clients, 10 seconds)

| Server | Throughput | Mean Latency | P95 Latency |
|--------|------------|--------------|-------------|
| Python | 252 req/s | 198.2ms | 245.8ms |
| Rust | 225 req/s | 222.1ms | 268.4ms |
| Ruby | 131 req/s | 381.5ms | 492.3ms |
| Elixir | 114 req/s | 438.6ms | 561.7ms |

## Architecture Comparison

### Python Server
- **Framework:** FastAPI + Uvicorn
- **Concurrency:** Async/await with thread pool executor
- **ONNX:** Single session, multi-threaded (num_cpus/2 threads)
- **Memory:** ~2GB (1 model instance)
- **Port:** 8000

**Strengths:**
- Fastest latency for both single and batch requests
- Highest throughput under load
- Lower memory usage (single model instance)
- Simpler codebase, easier to maintain
- Direct ONNX Runtime integration

**Weaknesses:**
- Python GIL may limit extreme concurrency scenarios
- Slightly higher variance in P99 latency

### Rust Server
- **Framework:** Axum + Tokio
- **Concurrency:** Session pool (one session per CPU core)
- **ONNX:** Multiple sessions with round-robin distribution
- **Memory:** ~2GB × num_cpus (multiple model instances)
- **Port:** 8001

**Strengths:**
- Memory safety and thread safety guarantees
- Single binary deployment
- Consistent P95/P99 latencies

**Weaknesses:**
- Significantly slower batch processing (65% slower)
- Higher memory usage (N model instances)
- More complex concurrency management
- Session pool creates overhead for batches

### Elixir Server
- **Framework:** Plug + Bandit + BEAM VM
- **Concurrency:** GenServer + Actor model (Elixir processes)
- **ONNX:** Ortex (ONNX Runtime bindings via Rust NIFs)
- **Tokenizer:** HuggingFace tokenizers (Rust bindings)
- **Memory:** ~2GB (1 model instance in GenServer)
- **Port:** 8002

**Strengths:**
- Leverages BEAM VM's legendary concurrency for routing
- Excellent single-text latency (2% faster than Python)
- Competitive batch processing
- Fault tolerance built-in (supervisor trees)
- Native ONNX Runtime integration

**Weaknesses:**
- Poor throughput under high concurrency (114 req/s, 54% of Python)
- GenServer becomes a bottleneck with 50+ concurrent requests
- Backend transfer overhead for normalization operations
- Newer library ecosystem (Ortex ~0.1)

### Ruby Server
- **Framework:** Sinatra + Puma
- **Concurrency:** Puma thread pool (default configuration)
- **ONNX:** onnxruntime gem (Ruby bindings to ONNX Runtime)
- **Tokenizer:** tokenizers gem (HuggingFace tokenizers bindings)
- **Memory:** ~2GB (1 model instance)
- **Port:** 8003

**Strengths:**
- **Best single-text latency** (9.1ms, 9% faster than Python)
- **Best batch processing** (22.7ms, 4% faster than Python)
- Simple, elegant Ruby code
- Mature gem ecosystem (onnxruntime ~0.10, tokenizers ~0.6)
- Direct ONNX Runtime integration with Numo arrays

**Weaknesses:**
- Poor throughput under high concurrency (131 req/s, 52% of Python)
- Puma's threading model less efficient than Python's async + threads
- Higher latency variance under load (P95: 492ms vs Python's 246ms)
- Ruby's GIL limits parallelism

## Analysis and Insights

### 1. Ruby's Surprising Latency Performance
Ruby wins both single-text (9.1ms) and batch (22.7ms) latency tests despite being an interpreted language. This suggests:
- The onnxruntime gem has efficient C bindings with minimal overhead
- ONNX Runtime's C++ core does the heavy lifting, not Ruby
- Puma's threading is efficient for low-concurrency scenarios

### 2. Python's Throughput Dominance
Python achieves 252 req/s (92% more than Ruby, 121% more than Elixir) due to:
- Uvicorn's async/await + thread pool is optimized for high concurrency
- Better handling of 50+ concurrent connections
- Lower latency variance under load (P95: 246ms vs Ruby's 492ms)

### 3. The Concurrency Bottleneck Pattern
Ruby, Elixir, and Rust all struggle with high concurrency compared to Python:
- **Elixir (114 req/s)**: GenServer becomes a serialization point
- **Ruby (131 req/s)**: Puma's thread pool + GIL limits parallelism
- **Rust (225 req/s)**: Session pool overhead, but still better than Ruby/Elixir

### 4. Batch Processing Reveals Architecture Efficiency
- **Ruby & Python (22-24ms)**: Single session = all cores available
- **Rust (38ms)**: Session pool = each batch gets fraction of cores
- Single session design clearly wins for batch workloads

## Recommendations

**Use Python when:**
- ✅ **High concurrency is critical** (50+ concurrent requests)
- ✅ **Best overall performance** under production load
- ✅ Lower latency variance matters (P95: 246ms)
- ✅ Integration with Python ML ecosystem needed
- ✅ You want mature async/await with excellent ONNX support

**Use Ruby when:**
- ✅ **Lowest latency is the priority** (9.1ms single, 22.7ms batch)
- ✅ Low to moderate concurrency (< 20 concurrent requests)
- ✅ Integration with existing Ruby/Rails applications
- ✅ Simple deployment in Ruby ecosystem
- Note: 52% of Python's throughput under high load

**Use Rust when:**
- Memory safety is critical for your application
- You need a single binary deployment
- Moderate concurrency requirements (225 req/s is acceptable)
- You're willing to accept slower batch processing for safety guarantees

**Use Elixir when:**
- You need massive concurrency for routing (but not inference!)
- Fault tolerance is paramount (telecom, banking)
- You're building a distributed system
- **Caution**: GenServer bottleneck limits inference throughput to 114 req/s

## Conclusion

**The results reveal a latency vs throughput tradeoff:**

### For Production Workloads: Python Wins
Python is the best choice for production ONNX inference servers:
- **121% higher throughput** than Elixir (252 vs 114 req/s)
- **92% higher throughput** than Ruby (252 vs 131 req/s)
- **12% higher throughput** than Rust (252 vs 225 req/s)
- Much lower latency variance under load (P95: 246ms vs Ruby's 492ms)
- Mature async/await + thread pool handles high concurrency gracefully

### Ruby's Surprising Performance
Ruby wins all latency tests but can't handle high concurrency:
- **Best single-text latency**: 9.1ms (9% faster than Python)
- **Best batch latency**: 22.7ms (4% faster than Python)
- But only 52% of Python's throughput (131 vs 252 req/s)
- Good choice for low-concurrency, latency-sensitive use cases

### The Single Session Insight
Ruby and Python both use single ONNX sessions (vs Rust's session pool), explaining their superior batch performance. The difference in throughput comes from the web framework and concurrency model, not ONNX Runtime itself.

**Recommendation**: Use Python unless you have < 20 concurrent requests AND need the absolute lowest latency (then consider Ruby).

## Test Environment
- **Hardware:** Apple Silicon Mac (M-series)
- **Model:** M-CLIP XLM-Roberta-Large-Vit-B-32 (INT8 quantized ONNX)
- **Test Date:** 2025-11-04
- **Concurrent Load:** 50 clients
- **Test Duration:** 10 seconds per throughput test
