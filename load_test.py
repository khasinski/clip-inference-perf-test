#!/usr/bin/env python3
"""
Concurrent load testing for fast-clip inference server
Simulates real-world concurrent requests
"""
import requests
import time
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import argparse

class LoadTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/encode"

    def single_request(self, texts: List[str], request_id: int) -> Dict:
        """Make a single request and return timing info"""
        start = time.perf_counter()
        try:
            response = requests.post(
                self.endpoint,
                json={"texts": texts, "normalize": True},
                timeout=30
            )
            elapsed = time.perf_counter() - start

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "elapsed": elapsed,
                    "status_code": 200,
                    "request_id": request_id,
                    "num_texts": len(texts)
                }
            else:
                return {
                    "success": False,
                    "elapsed": elapsed,
                    "status_code": response.status_code,
                    "request_id": request_id
                }
        except Exception as e:
            elapsed = time.perf_counter() - start
            return {
                "success": False,
                "elapsed": elapsed,
                "error": str(e),
                "request_id": request_id
            }

    def run_load_test(
        self,
        texts: List[str],
        num_requests: int = 100,
        concurrency: int = 10
    ):
        """Run load test with specified concurrency"""

        print(f"\n{'='*70}")
        print(f"LOAD TEST")
        print(f"{'='*70}")
        print(f"  Endpoint:     {self.endpoint}")
        print(f"  Texts/req:    {len(texts)}")
        print(f"  Requests:     {num_requests}")
        print(f"  Concurrency:  {concurrency}")
        print(f"{'='*70}\n")

        results = []
        start_time = time.perf_counter()

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(self.single_request, texts, i)
                for i in range(num_requests)
            ]

            completed = 0
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                completed += 1

                # Progress indicator
                if completed % 10 == 0 or completed == num_requests:
                    print(f"Progress: {completed}/{num_requests} requests completed", end='\r')

        total_time = time.perf_counter() - start_time
        print("\n")

        # Analyze results
        self.print_results(results, total_time, len(texts))

    def print_results(self, results: List[Dict], total_time: float, texts_per_request: int):
        """Print formatted results"""

        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        if not successful:
            print("❌ All requests failed!")
            return

        times = [r["elapsed"] for r in successful]

        print(f"{'='*70}")
        print(f"RESULTS")
        print(f"{'='*70}\n")

        print(f"📊 Request Statistics:")
        print(f"  Total requests:    {len(results)}")
        print(f"  Successful:        {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"  Failed:            {len(failed)}")
        print(f"  Total time:        {total_time:.2f}s")
        print(f"  Requests/sec:      {len(results)/total_time:.2f}")

        print(f"\n⚡ Latency (per request):")
        print(f"  Mean:              {statistics.mean(times)*1000:.2f}ms")
        print(f"  Median:            {statistics.median(times)*1000:.2f}ms")
        print(f"  Min:               {min(times)*1000:.2f}ms")
        print(f"  Max:               {max(times)*1000:.2f}ms")
        print(f"  Std Dev:           {statistics.stdev(times)*1000:.2f}ms")
        print(f"  p50:               {statistics.quantiles(times, n=100)[49]*1000:.2f}ms")
        print(f"  p95:               {statistics.quantiles(times, n=100)[94]*1000:.2f}ms")
        print(f"  p99:               {statistics.quantiles(times, n=100)[98]*1000:.2f}ms")

        print(f"\n🚀 Throughput:")
        total_texts = len(successful) * texts_per_request
        print(f"  Total texts:       {total_texts}")
        print(f"  Texts/sec:         {total_texts/total_time:.1f}")
        print(f"  Time per text:     {statistics.mean(times)*1000/texts_per_request:.2f}ms")

        if failed:
            print(f"\n❌ Failures:")
            for f in failed[:5]:  # Show first 5 failures
                print(f"  Request {f['request_id']}: {f.get('error', f.get('status_code'))}")

def main():
    parser = argparse.ArgumentParser(description='Load test fast-clip inference server')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL')
    parser.add_argument('--requests', '-n', type=int, default=100, help='Total requests')
    parser.add_argument('--concurrency', '-c', type=int, default=10, help='Concurrent requests')
    parser.add_argument('--batch-size', '-b', type=int, default=4, help='Texts per request')

    args = parser.parse_args()

    # Test data
    test_texts = [
        "Machine learning and artificial intelligence",
        "Natural language processing with transformers",
        "Computer vision and deep learning models",
        "Semantic search and information retrieval",
    ]

    # Create batch
    texts = (test_texts * (args.batch_size // len(test_texts) + 1))[:args.batch_size]

    # Run test
    tester = LoadTester(args.url)
    tester.run_load_test(texts, args.requests, args.concurrency)

if __name__ == "__main__":
    main()
