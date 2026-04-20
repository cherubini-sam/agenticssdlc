---
name: skills-performance-profiling
description: "Identify and resolve performance bottlenecks via systematic profiling and optimization patterns."
---

## 1. Profiling Protocol (5-Step)

1. **Baseline** — Measure current p50/p95/p99 latency, memory peak, CPU %.
2. **Profile** — Identify hotspots with `cProfile` or `line_profiler`.
3. **Analyze** — Root-cause the slowness (I/O wait, CPU bound, GC pressure, N+1 queries).
4. **Optimize** — Apply targeted patterns (see §2).
5. **Verify** — Confirm improvement against baseline metrics; no regression on p99.

## 2. Optimization Patterns

| Pattern                            | When                  | Mechanism                  |
| :--------------------------------- | :-------------------- | :------------------------- |
| `@lru_cache`                       | Repeated pure calls   | Memoize on args hash       |
| Generator                          | Large in-memory lists | Lazy evaluation            |
| Batch DB ops                       | N+1 query loops       | Single query + dict lookup |
| `asyncio`                          | I/O-bound blocking    | Concurrent awaitable tasks |
| `np.vectorize` / pandas vectorized | Row-by-row loops      | Vectorized ops over arrays |

## 3. Timer Utility

```python
import time
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    yield
    print(f"{name}: {time.perf_counter() - start:.4f}s")

# Usage
with timer("embedding_batch"):
    embeddings = model.encode(texts)
```

## 4. Metrics to Track

| Metric        | Unit                 |
| :------------ | :------------------- |
| Response time | p50 / p95 / p99 (ms) |
| Throughput    | req/s                |
| Memory peak   | MB                   |
| CPU usage     | %                    |
