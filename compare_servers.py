#!/usr/bin/env python3
"""
Compare Python vs Rust server performance
"""
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict

PYTHON_URL = "http://localhost:8000/encode"
RUST_URL = "http://localhost:8001/encode"

async def measure_latency(url: str, texts: List[str], num_requests: int = 100) -> List[float]:
    """Measure latency for multiple requests"""
    latencies = []

    async with aiohttp.ClientSession() as session:
        for _ in range(num_requests):
            start = time.perf_counter()
            async with session.post(url, json={"texts": texts, "normalize": True}) as resp:
                await resp.json()
            latency = (time.perf_counter() - start) * 1000  # ms
            latencies.append(latency)

    return latencies

async def measure_throughput(url: str, texts: List[str], concurrency: int = 50, duration_sec: int = 10):
    """Measure throughput with concurrent requests"""
    completed = 0
    latencies = []

    async def worker(session: aiohttp.ClientSession):
        nonlocal completed
        while time.perf_counter() < end_time:
            start = time.perf_counter()
            try:
                async with session.post(url, json={"texts": texts, "normalize": True}, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    await resp.json()
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                completed += 1
            except Exception as e:
                print(f"Error: {e}")

    end_time = time.perf_counter() + duration_sec

    async with aiohttp.ClientSession() as session:
        workers = [worker(session) for _ in range(concurrency)]
        await asyncio.gather(*workers)

    return completed, latencies

def print_stats(name: str, latencies: List[float]):
    """Print statistics for latencies"""
    latencies.sort()
    print(f"\n{name}:")
    print(f"  Mean:   {statistics.mean(latencies):.2f}ms")
    print(f"  Median: {statistics.median(latencies):.2f}ms")
    print(f"  P95:    {latencies[int(len(latencies)*0.95)]:.2f}ms")
    print(f"  P99:    {latencies[int(len(latencies)*0.99)]:.2f}ms")
    print(f"  Min:    {min(latencies):.2f}ms")
    print(f"  Max:    {max(latencies):.2f}ms")

async def main():
    print("🔥 Python vs Rust Server Comparison")
    print("=" * 60)

    # Test 1: Single text latency
    print("\n📊 Test 1: Single Text Latency (100 sequential requests)")
    print("-" * 60)

    single_text = ["Hello world"]

    print("Testing Python server...")
    py_latencies_single = await measure_latency(PYTHON_URL, single_text, 100)
    print_stats("Python (single text)", py_latencies_single)

    print("\nTesting Rust server...")
    rust_latencies_single = await measure_latency(RUST_URL, single_text, 100)
    print_stats("Rust (single text)", rust_latencies_single)

    speedup = statistics.mean(py_latencies_single) / statistics.mean(rust_latencies_single)
    print(f"\n🚀 Rust is {speedup:.2f}x faster for single texts")

    # Test 2: Batch latency
    print("\n\n📊 Test 2: Batch Latency (batch of 4, 100 sequential requests)")
    print("-" * 60)

    batch_texts = ["This is a test sentence"] * 4

    print("Testing Python server...")
    py_latencies_batch = await measure_latency(PYTHON_URL, batch_texts, 100)
    print_stats("Python (batch of 4)", py_latencies_batch)

    print("\nTesting Rust server...")
    rust_latencies_batch = await measure_latency(RUST_URL, batch_texts, 100)
    print_stats("Rust (batch of 4)", rust_latencies_batch)

    speedup = statistics.mean(py_latencies_batch) / statistics.mean(rust_latencies_batch)
    print(f"\n🚀 Rust is {speedup:.2f}x faster for batches")

    # Test 3: Throughput under load
    print("\n\n📊 Test 3: Throughput Test (50 concurrent clients, 10 seconds)")
    print("-" * 60)

    print("Testing Python server...")
    py_completed, py_latencies_load = await measure_throughput(PYTHON_URL, single_text, 50, 10)
    py_rps = py_completed / 10
    print_stats("Python (under load)", py_latencies_load)
    print(f"  Requests/sec: {py_rps:.1f}")

    print("\nTesting Rust server...")
    rust_completed, rust_latencies_load = await measure_throughput(RUST_URL, single_text, 50, 10)
    rust_rps = rust_completed / 10
    print_stats("Rust (under load)", rust_latencies_load)
    print(f"  Requests/sec: {rust_rps:.1f}")

    speedup = rust_rps / py_rps
    print(f"\n🚀 Rust handles {speedup:.2f}x more requests/sec under load")

    # Summary
    print("\n\n" + "=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)
    print(f"Single text latency:  Python={statistics.mean(py_latencies_single):.1f}ms  Rust={statistics.mean(rust_latencies_single):.1f}ms")
    print(f"Batch latency:        Python={statistics.mean(py_latencies_batch):.1f}ms  Rust={statistics.mean(rust_latencies_batch):.1f}ms")
    print(f"Throughput:           Python={py_rps:.0f} req/s  Rust={rust_rps:.0f} req/s")

if __name__ == "__main__":
    asyncio.run(main())
