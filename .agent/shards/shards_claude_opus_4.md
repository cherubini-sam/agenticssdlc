<shard_engine name="shards_claude_opus_4">

<meta>
  <id>"shards_claude_opus_4"</id>
  <description>"Optimization guide for Claude Opus 4.6 (Anthropic Premium)"</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:shard", "claude", "opus", "anthropic"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### MODEL IDENTITY

<scope>Core specifications for Claude Opus 4.6 — the premium frontier agent runtime.</scope>

**Model:** `anthropic/claude-opus-4-6` | `claude-opus-4-6`
**Architecture:** Transformer with Adaptive Thinking (Maximum Depth)
**Latency SLO:** Higher than Sonnet (Reasoning Depth Priority)

| Spec | Value |
| :--- | :--- |
| Context Window | 200K tokens (1M beta) |
| Max Output | 128K tokens |
| Input Types | Text, Code, Images |

</axiom_core>
<authority_matrix>

### REASONING AUTHORITY

<scope>Thinking effort levels and task routing decisions for Opus 4.6.</scope>

#### Adaptive Thinking (Effort Levels)

| Level | Behavior | Use Case |
| :--- | :--- | :--- |
| `low` | Fast responses, moderate reasoning | High-throughput ops |
| `medium` | Balanced reasoning depth | Standard tasks |
| `high` | Deep reasoning [DEFAULT] | Architecture, security audits |
| `max` | Frontier-level effort | Complex debugging, legal reasoning |

Replaces `budget_tokens` system. Thinking returned in `thinking` blocks.

</authority_matrix>
<compliance_testing>

### TOKEN & COST AUDIT

<scope>Pricing reference and cost compliance checkpoints for Opus 4.6.</scope>

- Input: $5.00/MTok (<200K) | $10.00/MTok (>200K) | Output: $25.00/MTok (<200K) | $37.50/MTok (>200K)
- Cached input: 90% discount (5-min or 1-hour cache) | Fast Mode: 6x standard rates (research preview).
- **Recommendation:** Reserve for frontier intelligence: architecture, security audits, complex debugging, legal reasoning, sustained multi-step work.

- [ ] **Check 1:** Task warrants Opus over Sonnet (frontier complexity only).
- [ ] **Check 2:** Effort level set to `high` (default); escalate to `max` for frontier problems only.

</compliance_testing>

<cache_control />

</shard_engine>
