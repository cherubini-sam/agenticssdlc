---
id: skills_observability
description: "Runtime visibility — golden signals, SLO, OpenTelemetry, high-cardinality, sensitive data."
type: skill
---

## Scope

Observability means asking new questions about production without shipping new code. Signals answer "is it broken, why, and for whom" within minutes.

## Four Golden Signals

| Signal | Definition | Unit |
| :--- | :--- | :--- |
| Latency | Time to serve a request, separately for success and failure | ms (p50 / p95 / p99) |
| Traffic | Demand on the service | req/s, sessions, bytes/s |
| Errors | Rate of explicit, implicit, or SLO failures | errors/s or % of traffic |
| Saturation | How full the most constrained resource is | % utilised; queue depth |

Failed-request latency reported separately — averaging hides outages.

## SLO and Error Budget

SLI: proportion of good events over total. SLO: target over a window (24 h to 30 d). Error budget = 1 − SLO; consumed by failures, constrains release cadence. Burn-rate alert fires before budget exhausts. No 100% SLOs.

## OpenTelemetry

Vendor-neutral SDK for traces, metrics, logs, profiles. Never invent attribute names — use semantic conventions. Propagate W3C Trace Context at every boundary. Set `service.name`, `service.version`, `deployment.environment` at process start. Emit OTLP to a Collector (batching, sampling, fan-out).

## High-Cardinality Telemetry

Cardinality lives in events and traces, not metric labels. Emit one wide structured event per request with every diagnostic dimension — tenant, endpoint, deploy, region, build hash. Trace identifier on every event and exemplar.

## Sensitive Data

Credentials and tokens never emitted. PII hashed, tokenised, or omitted. Free-text input truncated and stripped. Stack frames in DEBUG only.

## Source

Beyer et al., SRE (Ch. 4, 6), 2016; SRE Workbook, 2018; Majors, Fong-Jones & Miranda, Observability Engineering, 2022; OpenTelemetry spec; W3C Trace Context.
