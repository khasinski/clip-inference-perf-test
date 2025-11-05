#!/usr/bin/env python3
"""Quick throughput test for optimized Ruby server"""
import asyncio
import aiohttp
import time

async def measure_throughput(url: str, texts: list, concurrency: int = 50, duration_sec: int = 10):
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

async def main():
    print("Testing Ruby server with high thread count (8-32 threads)")
    print("=" * 60)

    single_text = ["Hello world"]
    completed, latencies = await measure_throughput("http://localhost:8003/encode", single_text, 50, 10)
    rps = completed / 10
    latencies.sort()

    print(f"Throughput: {rps:.1f} req/s")
    print(f"Mean latency: {sum(latencies)/len(latencies):.2f}ms")
    print(f"P95 latency: {latencies[int(len(latencies)*0.95)]:.2f}ms")
    print(f"Total requests: {completed}")

if __name__ == "__main__":
    asyncio.run(main())
