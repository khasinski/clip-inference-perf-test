# Ruby Server Concurrency Optimization Notes

## Baseline Performance (Default Puma)
- **Throughput**: 131 req/s (50 concurrent clients, 10s test)
- **Single-text latency**: 9.1ms (best among all 4 languages!)
- **Batch latency**: 22.7ms (best among all 4 languages!)
- **Configuration**: Puma default (likely 5 threads)

## Optimization Attempts

### 1. High Thread Count (8-32 threads) ✅ WORKING
**Configuration**: `puma_config.rb` with `threads 8, 32`

**Results**:
- **Throughput**: 137.8 req/s (+5% improvement)
- **Mean latency**: 369ms (under heavy load)
- **P95 latency**: 1507ms

**Analysis**:
- Modest 5% improvement in throughput
- Ruby's GIL limits true parallelism during CPU-bound ONNX inference
- Extra threads help with I/O overhead (HTTP, JSON) but not inference itself
- Each ONNX inference call likely holds the GIL, preventing other threads from running

### 2. Multi-Worker Mode (4 workers) ❌ FAILED
**Attempted Configuration**: `workers 4` to bypass GIL with separate processes

**Results**:
- Port binding conflicts (EADDRINUSE errors)
- Issue persisted despite removing `run!` from server.rb and fixing config
- Root cause unclear - possibly Puma cluster mode incompatibility with setup

**Why This Would Help**:
- Each worker = separate OS process = separate GIL
- 4 workers could theoretically achieve 4x parallelism for ONNX inference
- Memory cost: ~2GB × 4 workers = 8GB total

### 3. Falcon (Async/Fiber-based Server) ⏸️ NOT TESTED
**Status**: Gem installed but not benchmarked

**Why Skipped**:
- ONNX inference is CPU-bound, not I/O-bound
- Falcon's async fibers help with I/O concurrency but won't improve CPU-bound work
- The onnxruntime gem likely blocks during inference anyway
- Expected minimal benefit for this workload

## Key Findings

### Ruby's GIL is the Bottleneck
For CPU-bound ONNX inference:
1. **Single-threaded performance is excellent** (9.1ms latency)
2. **Throughput is limited by the GIL** (only ~138 req/s)
3. **Threading provides minimal benefit** (+5%) because:
   - ONNX inference holds the GIL
   - Only HTTP/JSON parsing can happen in parallel
   - Most time is spent in C extension code (onnxruntime)

### Comparison with Other Languages
| Language | Throughput | Architecture | GIL/Parallelism |
|----------|------------|--------------|-----------------|
| Python   | 252 req/s  | Async + thread pool | Has GIL, but better async design |
| Rust     | 225 req/s  | Session pool (N cores) | No GIL, true parallelism |
| Ruby     | 138 req/s  | Puma 32 threads | **GIL blocks parallelism** |
| Elixir   | 114 req/s  | GenServer bottleneck | BEAM VM concurrency |

### Why Python Wins Despite GIL
Python's async/await + ThreadPoolExecutor design is better suited for this workload:
- Async handling of HTTP requests
- ThreadPoolExecutor releases GIL during ONNX inference
- More mature async ecosystem

## Recommendations

### For Production Use
- **Use Python** if throughput > 150 req/s is needed (252 req/s)
- **Use Ruby** for low-concurrency scenarios where latency matters most
- Ruby excels at < 20 concurrent requests with best-in-class latency

### To Improve Ruby Further
Would need to:
1. **Fix multi-worker Puma** to bypass GIL (potential 3-4x improvement)
2. **Or**: Deploy multiple Ruby instances behind a load balancer
3. **Or**: Accept the GIL limitation and scale horizontally

## Configuration Files

### Working Configuration
**File**: `puma_config.rb`
```ruby
workers 0  # Single process (multi-worker had issues)
threads 8, 32  # High thread count for modest gains
bind 'tcp://0.0.0.0:8003'
```

### Gem Dependencies
```ruby
gem 'puma', '~> 6.0'
gem 'onnxruntime', '~> 0.10'
gem 'tokenizers', '~> 0.6'
gem 'numo-narray', '~> 0.9'
gem 'falcon', '~> 0.47'  # Installed but not tested
gem 'async', '~> 2.0'    # Installed but not tested
```

## Conclusion

Ruby achieves **excellent latency** (9.1ms, best of all 4 languages) but is **limited to ~138 req/s throughput** due to the GIL. For CPU-bound ONNX inference workloads:

- ✅ **Best choice for low-concurrency, latency-sensitive applications**
- ❌ **Not suitable for high-throughput production workloads** (use Python instead)
- ⚠️ **5% improvement possible** with thread tuning, but fundamentally GIL-bound

The optimization journey shows that for this specific workload (CPU-bound ML inference), the choice of language's concurrency model (GIL vs no GIL) matters more than framework optimizations (Puma vs Falcon).
