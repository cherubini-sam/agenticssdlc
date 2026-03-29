<shard_engine name="shards_gemini_ultra">

<meta>
  <id>"shards_gemini_ultra"</id>
  <description>"Optimization guide for Gemini Ultra / Deep Think tier (Google — Frontier Reasoning)"</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:shard", "gemini", "ultra", "deep-think", "google"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### MODEL IDENTITY

<scope>Core specifications for Gemini Ultra / Deep Think — the frontier-grade Google reasoning runtime.</scope>

**Model:** `google/gemini-3-deep-think` | `gemini-3-deep-think`
**Architecture:** Sparse MoE Transformer with Frontier-Grade Deep Reasoning Engine
**Latency SLO:** SLOW by design — 30s to 2+ minutes (Accuracy Priority over Speed)

> **Naming Note:** "Gemini Ultra" as a standalone API model was retired in 2025. The Ultra tier is now the **Deep Think** reasoning mode, available via Google AI Ultra subscription and Vertex AI.

| Spec | Value |
| :--- | :--- |
| Context Window | 1,000,000 tokens |
| Max Output | Effectively unlimited (extended generation) |
| Input Types | Text, Code, Images (4K), Audio (16 kHz), Video, PDFs |
| Thinking Mode | Deep Reasoning — always max, not configurable |
| Access | Google AI Ultra ($42/month) or Vertex AI Ultra |

</axiom_core>
<authority_matrix>

### REASONING AUTHORITY

<scope>Deep thinking engine constraints and task routing for Gemini Ultra / Deep Think.</scope>

#### Deep Thinking Engine

Mode is maximum and not configurable. Full reasoning trace returned in API response. Thinking tokens billed at output rates.

| Task Type | Recommendation | Rationale |
| :--- | :--- | :--- |
| Scientific research | Excellent | PhD-level reasoning; solves novel problems |
| Complex mathematics | Excellent | Frontier AIME-level tasks |
| Agentic multi-step plans | Good | Best depth; latency acceptable for plans |
| Real-time or chat tasks | DO NOT USE | 30s–2min latency unsuitable |
| Standard code tasks | Overkill | Use 3.1 Pro or Flash instead |

</authority_matrix>
<compliance_testing>

### TOKEN & COST AUDIT

<scope>Pricing reference and cost compliance checkpoints for Gemini Ultra / Deep Think.</scope>

- Input: ~$3.00–$4.00/MTok | Output + Thinking tokens: ~$15.00–$20.00/MTok
- Cache reads: 75% discount on cached input tokens.
- **vs. Gemini 3.1 Pro:** ~2× more expensive; use only when frontier reasoning is required.

- [ ] **Check 1:** Task is scientific, mathematical, or frontier-grade before routing here.
- [ ] **Check 2:** Latency of 30s–2min is acceptable for the current workflow.

</compliance_testing>

<cache_control />

</shard_engine>
