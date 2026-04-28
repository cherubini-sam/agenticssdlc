---
id: skills_performance_profiling
description: "Runtime performance — baseline, hotspot analysis, targeted optimisation, regression guard."
type: skill
---

## Scope

Performance work is grounded in measurement: capture a baseline, find the dominant cost, change one thing, prove the change improved the target without regressing anything else.

## Baseline

| Metric | Required |
| :--- | :--- |
| Latency | p50, p95, p99 under representative load |
| Throughput | Sustained requests per second at the target error rate |
| Memory | Peak resident memory during the workload |
| CPU | Average and peak utilisation per worker |
| Workload definition | Scenario, request mix, duration, concurrency — recorded with the baseline |

A baseline from a different workload, environment, or build is not comparable.

## Hotspot Analysis

Capture CPU and wall-clock profiles under the baseline workload. Classify each hotspot — I/O wait, CPU bound, allocator pressure, lock contention, N+1 calls. Rank by cumulative time, not self time. Reproducible across at least two runs.

## Optimisation Patterns

| Pattern | When |
| :--- | :--- |
| Memoisation | Repeated pure calls dominate |
| Lazy iterator / streaming | Large in-memory collections cause memory pressure |
| Batched dependency calls | N+1 query loops |
| Async I/O concurrency | I/O-bound blocking |
| Vectorised operations | Row-by-row loops over uniform data |
| Index or read-path projection | A hot read pattern hits a full scan |
| Connection or object pool | Setup cost dwarfs the work |

Apply one pattern per measurement cycle.

## Regression Guard

Re-baseline after the change. Target metric improves; p99 does not regress; memory does not grow. Baselines stored machine-readable alongside code. Performance tests run in the build pipeline. Documented rollback threshold.

Any p99 regression is a failure even when the median improves.

## Source

Beyer et al., SRE (Ch. 6), 2016; Gregg, Systems Performance, 2nd ed., 2020.
