# Benchmarking Guide

Multiple benchmarking tools are provided to test the inference server performance.

## 1. Python Load Tester (Recommended)

Most comprehensive and realistic load testing tool.

### Installation
No extra dependencies needed - uses standard library + requests.

### Usage

```bash
# Basic test (100 requests, 10 concurrent)
python3 load_test.py

# Custom parameters
python3 load_test.py --requests 1000 --concurrency 50 --batch-size 8

# Full options
python3 load_test.py --help
```

### Options

- `--url` - Base URL (default: http://localhost:8000)
- `--requests` / `-n` - Total number of requests (default: 100)
- `--concurrency` / `-c` - Concurrent connections (default: 10)
- `--batch-size` / `-b` - Texts per request (default: 4)

### Example Output

```
======================================================================
LOAD TEST
======================================================================
  Endpoint:     http://localhost:8000/encode
  Texts/req:    4
  Requests:     100
  Concurrency:  10
======================================================================

Progress: 100/100 requests completed

======================================================================
RESULTS
======================================================================

📊 Request Statistics:
  Total requests:    100
  Successful:        100 (100.0%)
  Failed:            0
  Total time:        8.45s
  Requests/sec:      11.84

⚡ Latency (per request):
  Mean:              84.23ms
  Median:            83.45ms
  Min:               78.12ms
  Max:               95.67ms
  Std Dev:           3.45ms
  p50:               83.45ms
  p95:               89.23ms
  p99:               92.34ms

🚀 Throughput:
  Total texts:       400
  Texts/sec:         47.3
  Time per text:     21.06ms
```

## 2. Apache Benchmark (ab)

Classic HTTP benchmarking tool. Simple but limited for POST requests.

### Installation

**macOS:**
```bash
# Usually pre-installed, or:
brew install apache2
```

**Linux:**
```bash
sudo apt-get install apache2-utils
```

### Usage

```bash
# Basic test
./bench_ab.sh

# Custom parameters
./bench_ab.sh http://localhost:8000/encode 1000 50

# Direct ab command
ab -n 100 -c 10 -p payload.json -T "application/json" http://localhost:8000/encode
```

## 3. wrk (Modern HTTP Benchmark)

Fast and powerful HTTP benchmarking tool.

### Installation

**macOS:**
```bash
brew install wrk
```

**Linux:**
```bash
git clone https://github.com/wg/wrk.git
cd wrk
make
sudo cp wrk /usr/local/bin/
```

### Usage

```bash
# 4 threads, 100 connections, 30 seconds
wrk -t4 -c100 -d30s -s bench_wrk.lua http://localhost:8000/encode

# Quick test
wrk -t2 -c10 -d10s -s bench_wrk.lua http://localhost:8000/encode
```

### Example Output

```
-----------------------------------------------
FAST-CLIP WRK BENCHMARK RESULTS
-----------------------------------------------
Total requests:    15423
Successful:        15423
Failed:            0
Duration:          30.01s
Requests/sec:      514.03

Latency Statistics:
  Mean:            19.45ms
  Stdev:           3.21ms
  Min:             12.34ms
  Max:             89.23ms
  50th percentile: 18.92ms
  90th percentile: 23.45ms
  99th percentile: 34.56ms
-----------------------------------------------
```

## 4. Curl Benchmark

Simple shell script using curl. No external dependencies.

### Usage

```bash
# Make executable
chmod +x bench_curl.sh

# Run test
./bench_curl.sh http://localhost:8000/encode 100
```

## Comparison

| Tool | Best For | Pros | Cons |
|------|----------|------|------|
| **load_test.py** | Realistic load testing | Full control, detailed stats, concurrent | Requires Python |
| **ab** | Quick tests | Pre-installed, simple | Limited POST support |
| **wrk** | High performance | Very fast, Lua scripting | Needs installation |
| **curl** | Simple tests | No dependencies | Basic, slower |

## Recommended Testing Strategy

### 1. Development Testing
```bash
python3 load_test.py -n 50 -c 5 -b 4
```

### 2. Performance Testing
```bash
python3 load_test.py -n 500 -c 50 -b 8
```

### 3. Stress Testing
```bash
python3 load_test.py -n 2000 -c 100 -b 16
```

### 4. Production Simulation
```bash
# Sustained load for 5 minutes
wrk -t8 -c100 -d300s -s bench_wrk.lua http://localhost:8000/encode
```

## Performance Tips

1. **Start the server first**: Make sure the server is running
2. **Warmup**: First few requests are slower (model loading, caching)
3. **Batch size**: Larger batches = better throughput but higher latency
4. **Concurrency**: Find the sweet spot (usually 10-50 for single server)
5. **Network**: Test locally first to isolate network latency

## Expected Performance (M1 Mac)

| Batch Size | Concurrent Requests | Throughput | Latency (p50) |
|------------|-------------------|------------|---------------|
| 1          | 10                | ~20/s      | ~45ms         |
| 4          | 10                | ~40/s      | ~90ms         |
| 8          | 20                | ~60/s      | ~160ms        |
| 16         | 30                | ~70/s      | ~240ms        |

## Troubleshooting

### Connection Refused
- Make sure server is running: `python3 fast_onnx_server.py`

### High Error Rate
- Reduce concurrency
- Check server logs
- Increase timeout

### Low Throughput
- Increase batch size
- Check CPU usage
- Consider using CoreML (Mac) or GPU acceleration
