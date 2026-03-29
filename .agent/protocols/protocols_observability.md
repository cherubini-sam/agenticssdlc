<protocol_framework name="protocols_observability">

<meta>
  <id>"protocols_observability"</id>
  <description>"Standards for logging, monitoring, and debugging output."</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:protocol", "observability", "logging", "monitoring"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### OBSERVABILITY PROTOCOL [THE EYE]

<scope>Defines trace schema, monitoring metrics, and log structure for all agent actions.</scope>

#### 1. Trace Schema

Every agent action MUST emit a trace:

```json
{
  "trace_id": "tr_<uuid>",
  "span_id": "sp_<uuid>",
  "parent_span_id": "sp_<uuid>|null",
  "agent": "MANAGER|ARCHITECT|ENGINEER|...",
  "action": "route|read|write|execute|search",
  "timestamp": "ISO8601",
  "duration_ms": 1234,
  "tokens": {"input": 1000, "output": 500, "thinking": 200},
  "cost_usd": 0.0015,
  "status": "success|error|timeout",
  "metadata": {}
}
```

Span hierarchy: `MANAGER.route (root) ENGINEER.execute Read/Write/VALIDATOR.verify`

#### 2. Monitoring Metrics

**Performance:** `latency_p50` >10s | `latency_p95` >30s | `latency_p99` >60s | `throughput` <1 rpm alert.
**Tokens:** `tokens_per_request` >50K | `tokens_session_total` >500K | `cache_hit_rate` <50% alert.
**Cost:** `cost_per_request` >$1.00 | `cost_session_total` >$10.00 | `cost_daily_total` >$50.00 alert.
**Errors:** `error_rate` >5% | `timeout_rate` >2% | `retry_rate` >10% alert.

#### 3. Log Structure

| Level   | Use Case          | Retention    |
| :------ | :---------------- | :----------- |
| `DEBUG` | Dev tracing       | Session only |
| `INFO`  | Normal operations | 7 days       |
| `WARN`  | Potential issues  | 30 days      |
| `ERROR` | Failures          | 90 days      |

```json
{"level": "INFO", "timestamp": "ISO8601", "trace_id": "tr_abc123", "agent": "ENGINEER", "action": "write_file", "message": "...", "metadata": {}}
```

</axiom_core>
<authority_matrix>

### ALERTING & EXPORT AUTHORITY

<scope>Defines alert severity tiers and OpenTelemetry export targets for operational governance.</scope>

#### 4. Alerting Rules

**Critical (Immediate):** Error rate >10% for 5min | latency p99 >120s | cost >$5.00/req | security violation.
**Warning (Batched):** Error rate >5% for 15min | latency p95 >30s | session tokens >400K | cache hit <30%.
**Info (Daily):** Cost summary | agent utilization | top errors.

#### 5. Telemetry Export

```
gen_ai.system = "<provider>"  |  gen_ai.request.model = "..."  |  gen_ai.usage.input_tokens = N  |  gen_ai.usage.output_tokens = N
```

Export: OTLP | structured JSON | metrics endpoint.

</authority_matrix>
<compliance_testing>

### PRIVACY & RETENTION AUDIT

<scope>Validation rules for data masking, retention enforcement, and compliance with Law 6 (Secret Sanitization).</scope>

#### 6. Privacy & Security

- API keys: `sk-...****` | Passwords: `[REDACTED]` | PII: Hash or mask.

**Retention:** Traces 7d | Logs 30d | Metrics 90d | Errors 90d.

</compliance_testing>

<cache_control />

</protocol_framework>
