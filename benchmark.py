"""
Benchmark different inference approaches
"""
import requests
import time
import numpy as np
from typing import List

def benchmark_server(texts: List[str], url: str = "http://localhost:8000", warmup: int = 5, iterations: int = 100):
    """Benchmark the inference server"""

    print(f"\n{'='*60}")
    print(f"Benchmarking: {url}")
    print(f"Texts: {len(texts)}")
    print(f"Warmup: {warmup}, Iterations: {iterations}")
    print(f"{'='*60}\n")

    # Health check
    try:
        health = requests.get(f"{url}/health").json()
        print(f"✓ Server status: {health['status']}")
        print(f"✓ Provider: {health.get('provider', 'unknown')}\n")
    except Exception as e:
        print(f"❌ Server not reachable: {e}")
        return

    # Warmup
    print("Warming up...")
    for _ in range(warmup):
        requests.post(f"{url}/encode", json={"texts": texts, "normalize": True})

    # Benchmark
    print(f"Running {iterations} iterations...")
    times = []

    for i in range(iterations):
        start = time.perf_counter()
        response = requests.post(
            f"{url}/encode",
            json={"texts": texts, "normalize": True},
            timeout=30
        )
        elapsed = time.perf_counter() - start
        times.append(elapsed)

        if i == 0:
            # Verify response
            data = response.json()
            print(f"✓ Response shape: {data['shape']}")

    times = np.array(times)

    print(f"\n📊 Results:")
    print(f"  Mean: {times.mean()*1000:.2f}ms")
    print(f"  Median: {np.median(times)*1000:.2f}ms")
    print(f"  Min: {times.min()*1000:.2f}ms")
    print(f"  Max: {times.max()*1000:.2f}ms")
    print(f"  Std: {times.std()*1000:.2f}ms")
    print(f"  Throughput: {len(texts)/times.mean():.1f} texts/sec")
    print(f"  Per text: {times.mean()*1000/len(texts):.2f}ms")

if __name__ == "__main__":
    # Test with different batch sizes
    test_texts = [
        "Hello world",
        "Machine learning is amazing",
        "Natural language processing",
        "Computer vision and deep learning",
    ]

    print("="*60)
    print("FAST-CLIP INFERENCE BENCHMARK")
    print("="*60)

    # Benchmark batch sizes
    for batch_size in [1, 4, 16, 32]:
        texts = test_texts * (batch_size // len(test_texts)) + test_texts[:batch_size % len(test_texts)]
        texts = texts[:batch_size]
        benchmark_server(texts, iterations=50)

    print("\n" + "="*60)
    print("Benchmark complete!")
    print("="*60)
