import time
from contextlib import contextmanager


@contextmanager
def timer(name: str):
    """Context manager to measure execution time of a code block."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"{name}: {elapsed:.4f}s")
