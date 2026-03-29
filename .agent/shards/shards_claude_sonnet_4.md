<shard_engine name="shards_claude_sonnet_4">

<meta>
  <id>"shards_claude_sonnet_4"</id>
  <description>"Optimization guide for Claude Sonnet 4.6 (Anthropic)"</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:shard", "claude", "sonnet", "anthropic"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### MODEL IDENTITY

<scope>Core specifications for Claude Sonnet 4.6 — the default agent runtime.</scope>

**Model:** `anthropic/claude-sonnet-4-6` | `claude-sonnet-4-6`
**Architecture:** Transformer with Adaptive Thinking
**Latency SLO:** Standard (Production Ready)

| Spec | Value |
| :--- | :--- |
| Context Window | 200K tokens |
| Max Output | 128K tokens |
| Input Types | Text, Code, Images |

</axiom_core>
<authority_matrix>

### REASONING AUTHORITY

<scope>Thinking effort levels and task routing decisions for Sonnet 4.6.</scope>

#### Adaptive Thinking (Effort Levels)

| Level | Behavior | Use Case |
| :--- | :--- | :--- |
| `low` | Minimal reasoning | Q&A, high-throughput |
| `medium` | Balanced depth [DEFAULT] | Standard coding, agents |
| `high` | Deep reasoning | Architecture, complex tasks |
| `max` | Maximum effort | Hardest frontier problems |

Replaces `budget_tokens` system. Thinking returned in `thinking` blocks.

</authority_matrix>
<compliance_testing>

### TOKEN & COST AUDIT

<scope>Pricing reference and cost compliance checkpoints for Sonnet 4.6.</scope>

- Input: $3.00/MTok (<200K) | $6.00/MTok (>200K) | Output: $15.00/MTok (<200K) | $22.50/MTok (>200K)
- Cached input: 90% discount.
- **Recommendation:** Default choice for coding, agents, and most production workloads. 40% cheaper than Opus 4.6.

- [ ] **Check 1:** Effort level matches task complexity (default: `medium`).
- [ ] **Check 2:** Request stays within 200K context to avoid tiered pricing.

</compliance_testing>

<cache_control />

</shard_engine>
