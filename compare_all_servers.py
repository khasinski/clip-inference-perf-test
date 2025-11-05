#!/usr/bin/env python3
"""
Compare Python vs Rust vs Elixir vs Ruby server performance
"""
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict

SERVERS = {
    "Python": "http://localhost:8000/encode",
    "Rust": "http://localhost:8001/encode",
    "Elixir": "http://localhost:8002/encode",
    "Ruby": "http://localhost:8003/encode",
}

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
                pass  # Ignore errors during load test

    end_time = time.perf_counter() + duration_sec

    async with aiohttp.ClientSession() as session:
        workers = [worker(session) for _ in range(concurrency)]
        await asyncio.gather(*workers)

    return completed, latencies

def print_stats(name: str, latencies: List[float]):
    """Print statistics for latencies"""
    latencies.sort()
    print(f"  {name:8s}  Mean: {statistics.mean(latencies):6.2f}ms  Median: {statistics.median(latencies):6.2f}ms  P95: {latencies[int(len(latencies)*0.95)]:6.2f}ms  P99: {latencies[int(len(latencies)*0.99)]:6.2f}ms")

async def main():
    print("🔥 Server Performance Comparison: Python vs Rust vs Elixir")
    print("=" * 80)

    # Test 1: Single text latency
    print("\n📊 Test 1: Single Text Latency (100 sequential requests)")
    print("-" * 80)

    single_text = ["Hello world"]
    results_single = {}

    for name, url in SERVERS.items():
        print(f"Testing {name}...")
        latencies = await measure_latency(url, single_text, 100)
        results_single[name] = latencies
        print_stats(name, latencies)

    # Find winner
    winner = min(results_single.items(), key=lambda x: statistics.mean(x[1]))
    print(f"\n🏆 Winner: {winner[0]} ({statistics.mean(winner[1]):.2f}ms avg)")

    # Test 2: Batch latency
    print("\n\n📊 Test 2: Batch Latency (batch of 4, 100 sequential requests)")
    print("-" * 80)

    batch_texts = ["This is a test sentence"] * 4
    results_batch = {}

    for name, url in SERVERS.items():
        print(f"Testing {name}...")
        latencies = await measure_latency(url, batch_texts, 100)
        results_batch[name] = latencies
        print_stats(name, latencies)

    # Find winner
    winner = min(results_batch.items(), key=lambda x: statistics.mean(x[1]))
    print(f"\n🏆 Winner: {winner[0]} ({statistics.mean(winner[1]):.2f}ms avg)")

    # Test 3: Throughput under load
    print("\n\n📊 Test 3: Throughput Test (50 concurrent clients, 10 seconds)")
    print("-" * 80)

    results_throughput = {}

    for name, url in SERVERS.items():
        print(f"Testing {name}...")
        completed, latencies = await measure_throughput(url, single_text, 50, 10)
        rps = completed / 10
        results_throughput[name] = (rps, latencies)
        print(f"  {name:8s}  Throughput: {rps:6.1f} req/s  Mean latency: {statistics.mean(latencies):6.2f}ms  P95: {latencies[int(len(latencies)*0.95)]:6.2f}ms")

    # Find winner
    winner = max(results_throughput.items(), key=lambda x: x[1][0])
    print(f"\n🏆 Winner: {winner[0]} ({winner[1][0]:.1f} req/s)")

    # Summary Table
    print("\n\n" + "=" * 80)
    print("📈 SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Metric':<30} {'Python':>12} {'Rust':>12} {'Elixir':>12} {'Ruby':>12}")
    print("-" * 80)
    print(f"{'Single text latency (ms)':<30} {statistics.mean(results_single['Python']):>12.1f} {statistics.mean(results_single['Rust']):>12.1f} {statistics.mean(results_single['Elixir']):>12.1f} {statistics.mean(results_single['Ruby']):>12.1f}")
    print(f"{'Batch latency (ms)':<30} {statistics.mean(results_batch['Python']):>12.1f} {statistics.mean(results_batch['Rust']):>12.1f} {statistics.mean(results_batch['Elixir']):>12.1f} {statistics.mean(results_batch['Ruby']):>12.1f}")
    print(f"{'Throughput (req/s)':<30} {results_throughput['Python'][0]:>12.0f} {results_throughput['Rust'][0]:>12.0f} {results_throughput['Elixir'][0]:>12.0f} {results_throughput['Ruby'][0]:>12.0f}")

if __name__ == "__main__":
    asyncio.run(main())
