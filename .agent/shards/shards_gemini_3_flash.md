<shard_engine name="shards_gemini_3_flash">

<meta>
  <id>"shards_gemini_3_flash"</id>
  <description>"Optimization guide for Gemini 3 Flash (Google)"</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:shard", "gemini", "flash", "google"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### MODEL IDENTITY

<scope>Core specifications for Gemini 3 Flash — the low-latency Google runtime.</scope>

**Model:** `google/gemini-3-flash` | `gemini-3-flash`
**Architecture:** Sparse Mixture-of-Experts (MoE) Transformer
**Latency SLO:** Optimized for Speed (Low Latency Target)

| Spec | Value |
| :--- | :--- |
| Context Window | 200K tokens |
| Max Output | 64K tokens |
| Input Types | Text, Code, Images, Audio, Video |

</axiom_core>
<authority_matrix>

### REASONING AUTHORITY

<scope>Thinking level selection and task routing for Gemini 3 Flash.</scope>

#### Thinking Levels

| Level | Behavior |
| :--- | :--- |
| `minimal` | Maximum throughput (Q&A) |
| `low` | Low latency |
| `medium` | Balanced [DEFAULT] |
| `high` | Maximum depth |

Returns thought signatures for all part types (platform-managed).

</authority_matrix>
<compliance_testing>

### TOKEN & COST AUDIT

<scope>Pricing reference and cost compliance checkpoints for Gemini 3 Flash.</scope>

- Input: $0.50/MTok | Output: $3.00/MTok (without thinking) | Cached: 90% discount (explicit caching only).
- **Flash vs Pro:** ~4x cheaper. **Recommendation:** Default for most coding and text generation tasks.

- [ ] **Check 1:** Thinking level matches task complexity (default: `medium`).
- [ ] **Check 2:** Use `minimal` for high-volume Q&A to minimize cost.

</compliance_testing>

<cache_control />

</shard_engine>
