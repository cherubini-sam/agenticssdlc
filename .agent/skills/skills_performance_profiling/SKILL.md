<skill_manifest name="skills_performance_profiling">

<meta>
  <id>"skills_performance_profiling"</id>
  <description>"Skill for performance analysis and optimization"</description>
  <globs>["**/*.py", "**/*.ts", "**/*.js"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "performance", "profiling", "optimization"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Identify and resolve performance bottlenecks
**Triggers:** "optimize performance", "slow", "profile", "bottleneck", "speed up"

</io_contract>
<state_mode>Read-write (Performance Tuning)</state_mode>
<dependencies>

- `cProfile`, `line_profiler`, `memory_profiler`
- `snakeviz` (Visualization)

</dependencies>
<env_vars>N/A</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. Profiling Protocol (5-Step Method)

1. **Baseline:** Measure time, memory, CPU.
2. **Profile:** Identify hotspots via tools.
3. **Analyze:** Diagnostic root cause slowness.
4. **Optimize:** Apply targeted patterns (caching, batching, generators).
5. **Verify:** improvement metrics check.

## 2. Optimization Patterns

- Use `lru_cache` for expensive calls.
- Use Generators for memory efficiency.
- Use Batching for DB operations.

</operational_steps>
<error_protocol>

If optimization degrades throughput, revert to baseline and re-profile for overlooked locks.

</error_protocol>
<side_effect_protocol>
<idempotency_key>N/A</idempotency_key>
<rollback_logic>Revert code changes if p99 latency increases post-optimization.</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

- Profile on production data only with sampled datasets/sandboxes.
- Tooling limited to specified library list (cProfile, etc.).

</permissions>
<rate_limit>

Track: Response time (p50/p95/p99), Throughput, Memory Peak, CPU %.

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
