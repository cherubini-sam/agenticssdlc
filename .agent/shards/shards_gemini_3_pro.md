<shard_engine name="shards_gemini_3_pro">

<meta>
  <id>"shards_gemini_3_pro"</id>
  <description>"Optimization guide for Gemini 3.1 Pro (Google)"</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:shard", "gemini", "pro", "google"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### MODEL IDENTITY

<scope>Core specifications for Gemini 3.1 Pro — the flagship Google reasoning runtime.</scope>

**Model:** `google/gemini-3.1-pro` | `gemini-3.1-pro`
**Architecture:** Sparse MoE Transformer with Enhanced Reasoning
**Latency SLO:** Frontier Intelligence Tier (Reasoning Depth Priority)

| Spec | Value |
| :--- | :--- |
| Context Window | 1,000,000 tokens (Native) |
| Max Output | 64K tokens |
| Input Types | Text, Code, Images, Audio, Video |

</axiom_core>
<authority_matrix>

### REASONING AUTHORITY

<scope>Thinking level selection and task routing for Gemini 3.1 Pro.</scope>

#### Thinking Levels

| Level | Behavior |
| :--- | :--- |
| `low` | Minimizes latency |
| `medium` | Balanced |
| `high` | Maximum depth [DEFAULT] |

`minimal` NOT supported. Returns thought signatures for all part types.

</authority_matrix>
<compliance_testing>

### TOKEN & COST AUDIT

<scope>Pricing reference and cost compliance checkpoints for Gemini 3.1 Pro.</scope>

- Input: $2.00/MTok (<200K) | $4.00/MTok (>200K) | Output: $12.00/MTok (<200K) | $18.00/MTok (>200K)
- Caching: $0.20–$0.40/MTok | Storage: $4.50/MTok/hr | Cached: 90% discount.
- **Recommendation:** Best-value flagship for complex reasoning, coding, and agentic tasks.

- [ ] **Check 1:** Task requires reasoning depth beyond Flash capability before routing here.
- [ ] **Check 2:** Context fits within 200K to avoid tiered pricing when possible.

</compliance_testing>

<cache_control />

</shard_engine>
