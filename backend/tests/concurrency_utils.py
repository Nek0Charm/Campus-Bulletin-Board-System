"""
Shared helper utilities for concurrency/race-condition tests.

Uses ThreadPoolExecutor + threading.Barrier to fire truly concurrent HTTP requests
against the FastAPI app, since the backend uses synchronous SQLAlchemy and the
event loop serializes async requests within a single worker.
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable


def race_requests(
    callables: list[Callable[[], Any]], timeout: float = 10.0
) -> list[Any]:
    """Execute callables concurrently, synchronized by a threading.Barrier.

    Each callable should create its own TestClient(app) internally — TestClient
    is not thread-safe for shared use.  The barrier guarantees all threads start
    their work at (roughly) the same moment.

    Returns a list of results in completion order (not argument order).
    """
    n = len(callables)
    barrier = threading.Barrier(n)
    results: list[Any] = []
    lock = threading.Lock()

    def worker(fn: Callable[[], Any]) -> None:
        barrier.wait(timeout=timeout)
        try:
            result = fn()
        except Exception as exc:
            result = exc
        with lock:
            results.append(result)

    with ThreadPoolExecutor(max_workers=n) as executor:
        futures = [executor.submit(worker, fn) for fn in callables]
        for future in futures:
            future.result(timeout=timeout + 5)

    return results
