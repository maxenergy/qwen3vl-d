"""Benchmark and load testing script.

Simple benchmark tool for testing API performance.
"""

import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

BASE_URL = "http://localhost:8000"


def benchmark_endpoint(
    endpoint: str,
    method: str = "GET",
    json_data: Dict = None,
    requests_count: int = 100,
    concurrent: int = 10
) -> Dict[str, Any]:
    """Benchmark an API endpoint.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        json_data: JSON data for POST/PUT requests
        requests_count: Total number of requests
        concurrent: Number of concurrent requests

    Returns:
        Dictionary with benchmark results
    """
    url = f"{BASE_URL}{endpoint}"
    durations = []
    errors = 0

    print(f"Benchmarking {method} {endpoint}")
    print(f"Total requests: {requests_count}, Concurrent: {concurrent}")

    def make_request():
        start = time.time()
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=json_data)
            else:
                response = requests.request(method, url, json=json_data)

            duration = time.time() - start
            return duration, response.status_code
        except Exception as e:
            return None, str(e)

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=concurrent) as executor:
        futures = [executor.submit(make_request) for _ in range(requests_count)]

        for future in as_completed(futures):
            duration, status = future.result()
            if duration is None:
                errors += 1
            else:
                durations.append(duration)

    total_time = time.time() - start_time

    if durations:
        return {
            "endpoint": endpoint,
            "method": method,
            "total_requests": requests_count,
            "successful": len(durations),
            "errors": errors,
            "total_time": total_time,
            "requests_per_second": len(durations) / total_time,
            "avg_response_time": statistics.mean(durations),
            "min_response_time": min(durations),
            "max_response_time": max(durations),
            "median_response_time": statistics.median(durations),
            "p95_response_time": sorted(durations)[int(len(durations) * 0.95)],
            "p99_response_time": sorted(durations)[int(len(durations) * 0.99)]
        }
    else:
        return {"error": "All requests failed", "errors": errors}


def run_benchmarks():
    """Run comprehensive benchmarks."""
    results = []

    # Benchmark health endpoint
    results.append(benchmark_endpoint("/api/v1/health", requests_count=1000, concurrent=50))

    # Benchmark projects list
    results.append(benchmark_endpoint("/api/v1/projects", requests_count=500, concurrent=20))

    # Print results
    print("\n" + "="*80)
    print("BENCHMARK RESULTS")
    print("="*80)

    for result in results:
        if "error" in result:
            print(f"\n{result['endpoint']}: ERROR - {result['error']}")
            continue

        print(f"\nEndpoint: {result['endpoint']}")
        print(f"  Total Requests: {result['total_requests']}")
        print(f"  Successful: {result['successful']}")
        print(f"  Errors: {result['errors']}")
        print(f"  Requests/sec: {result['requests_per_second']:.2f}")
        print(f"  Avg Response Time: {result['avg_response_time']*1000:.2f}ms")
        print(f"  Min Response Time: {result['min_response_time']*1000:.2f}ms")
        print(f"  Max Response Time: {result['max_response_time']*1000:.2f}ms")
        print(f"  P95 Response Time: {result['p95_response_time']*1000:.2f}ms")
        print(f"  P99 Response Time: {result['p99_response_time']*1000:.2f}ms")


if __name__ == "__main__":
    run_benchmarks()
