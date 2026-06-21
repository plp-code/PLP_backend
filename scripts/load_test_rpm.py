#!/usr/bin/env python3
"""Minimal no-dependency load test for request-rate validation.

Example:
    python scripts/load_test_rpm.py --url http://127.0.0.1:8000/api/v1/maps/ --rpm 100 --duration 60
"""

from __future__ import annotations

import argparse
import json
import statistics
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass


@dataclass
class Result:
    status_code: int
    latency_ms: float


def single_request(url: str, timeout: float) -> Result:
    start = time.perf_counter()
    req = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            response.read()
    except urllib.error.HTTPError as exc:
        status_code = exc.code
        exc.read()
    except Exception:
        status_code = 0
    latency_ms = (time.perf_counter() - start) * 1000
    return Result(status_code=status_code, latency_ms=latency_ms)


def run_load(url: str, rpm: int, duration_seconds: int, workers: int, timeout: float):
    target_requests = int((rpm * duration_seconds) / 60)
    spacing_seconds = 60 / rpm

    results: list[Result] = []
    lock = threading.Lock()

    def collect_result(future):
        result = future.result()
        with lock:
            results.append(result)

    started_at = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = []
        for i in range(target_requests):
            target_time = started_at + (i * spacing_seconds)
            now = time.perf_counter()
            if target_time > now:
                time.sleep(target_time - now)

            future = pool.submit(single_request, url, timeout)
            future.add_done_callback(collect_result)
            futures.append(future)

        for future in futures:
            future.result()

    elapsed = time.perf_counter() - started_at
    return results, elapsed


def summarize(results: list[Result], elapsed_seconds: float):
    total = len(results)
    success = sum(1 for r in results if 200 <= r.status_code < 300)
    rate_limited = sum(1 for r in results if r.status_code == 429)
    failed = sum(1 for r in results if r.status_code == 0 or r.status_code >= 500)

    latencies = [r.latency_ms for r in results]
    p95 = statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 100 else max(latencies, default=0.0)

    output = {
        "total_requests": total,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "achieved_rpm": round((total / elapsed_seconds) * 60, 2) if elapsed_seconds > 0 else 0,
        "success_2xx": success,
        "rate_limited_429": rate_limited,
        "failed_5xx_or_transport": failed,
        "latency_ms": {
            "avg": round(statistics.mean(latencies), 2) if latencies else 0.0,
            "p95": round(p95, 2),
            "max": round(max(latencies, default=0.0), 2),
        },
    }
    print(json.dumps(output, indent=2))


def parse_args():
    parser = argparse.ArgumentParser(description="Run a simple RPM-focused load test")
    parser.add_argument("--url", required=True, help="Full endpoint URL")
    parser.add_argument("--rpm", type=int, default=100, help="Target requests per minute")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--workers", type=int, default=20, help="Thread pool size")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-request timeout seconds")
    return parser.parse_args()


def main():
    args = parse_args()
    results, elapsed = run_load(
        url=args.url,
        rpm=args.rpm,
        duration_seconds=args.duration,
        workers=args.workers,
        timeout=args.timeout,
    )
    summarize(results, elapsed)


if __name__ == "__main__":
    main()
