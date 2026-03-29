<shard_engine name="shards_claude_haiku_4">

<meta>
  <id>"shards_claude_haiku_4"</id>
  <description>"Optimization guide for Claude Haiku 4.5 (Anthropic — High-Throughput)"</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:shard", "claude", "haiku", "anthropic"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### MODEL IDENTITY

<scope>Core specifications for Claude Haiku 4.5 — the high-throughput, latency-critical runtime.</scope>

**Model:** `anthropic/claude-haiku-4-5` | `claude-haiku-4-5` | `claude-haiku-4-5-20251001`
**Architecture:** Transformer with Extended Thinking (Budget-Controlled)
**Latency SLO:** FAST — Sub-200ms (Real-Time Priority)

| Spec | Value |
| :--- | :--- |
| Context Window | 200K tokens |
| Max Output | 64K tokens |
| Input Types | Text, Images (multimodal) |
| Extended Thinking | Budget-controlled (opt-in) — NOT adaptive effort |

</axiom_core>
<authority_matrix>

### REASONING AUTHORITY

<scope>Extended thinking budget allocation and task routing for Haiku 4.5.</scope>

#### Extended Thinking (Budget-Controlled)

Opt-in only. Requires explicit budget parameter. Disabled by default. Adaptive effort NOT supported.

| Task Type | Thinking Mode | Rationale |
| :--- | :--- | :--- |
| Real-time chat | Disabled | Latency priority, sub-200ms target |
| Simple code tasks | Disabled | Base capability sufficient |
| Multi-step reasoning | Budget: 4K–8K | Enable when CoT is required |
| Agentic debugging | Budget: 8K–16K | Maximum supported budget |

</authority_matrix>
<compliance_testing>

### TOKEN & COST AUDIT

<scope>Pricing reference and cost compliance checkpoints for Haiku 4.5.</scope>

- Input: $1.00/MTok | Output: $5.00/MTok
- Cache Write: $1.25/MTok (5-min TTL) | Cache Read: $0.10/MTok (90% savings)
- Batch API: 50% discount on all tiers.
- **Cost vs. Sonnet 4.6:** 66% cheaper. Achieves ~90% of Sonnet 4.5 quality.

- [ ] **Check 1:** Extended thinking disabled for latency-critical paths.
- [ ] **Check 2:** Thinking budget ≤ 16K tokens when enabled.

</compliance_testing>

<cache_control />

</shard_engine>
