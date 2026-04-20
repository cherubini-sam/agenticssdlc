<shard_engine name="shards_generic_llm">

<meta>
  <id>"shards_generic_llm"</id>
  <description>"Safe-defaults optimization guide for any unrecognized or third-party LLM"</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:shard", "generic", "fallback", "any-provider"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### MODEL IDENTITY

<scope>Conservative safe-defaults for any unrecognized or third-party LLM fallback.</scope>

**Model:** Any unrecognized model
**Architecture:** Unknown — assume OpenAI-compatible REST API (most common standard; validate before use)
**Latency SLO:** Unknown — apply conservative timeouts

| Spec | Conservative Assumption |
| :--- | :--- |
| Context Window | 128K tokens (treat 8K as hard floor) |
| Max Output | 4K–8K tokens |
| Input Types | Text-only (do NOT attempt multimodal without verification) |
| Extended Thinking | NOT supported — use prompt-based CoT |
| Function Calling | Assume OpenAI-compatible; validate before chaining |

</axiom_core>
<authority_matrix>

### REASONING AUTHORITY

<scope>Prompt-based reasoning strategy and agentic safe defaults for unknown models.</scope>

#### Reasoning Strategy (Prompt-Based CoT)

No native reasoning pipeline assumed. Inject CoT via system prompt. Keep chains to ≤4 steps.

| Task Type | Strategy | Rationale |
| :--- | :--- | :--- |
| Simple Q&A | Direct prompt | No CoT overhead needed |
| Multi-step reasoning | Prompt CoT (`"Think step by step"`) | Universal fallback |
| Tool/function use | Validate schema before execution | Malformed calls common on unknown models |
| Structured output | Provide explicit JSON schema | Do not rely on `response_format` support |

#### Agentic Safe Defaults

```json
{
  "temperature": 0.2,
  "top_p": 0.9,
  "max_tokens": 4000,
  "seed": "<randomize_per_retry>",
  "stream": false
}
```

Streaming DISABLED — breaks tool detection, JSON parsing, and retry logic in agentic contexts.

</authority_matrix>
<compliance_testing>

### TOKEN & COST AUDIT

<scope>Pricing assumptions and risk mitigation checklist for unknown model runtimes.</scope>

- **Assumed tier:** Mid ($1.00–$3.00/MTok input | $2.00–$10.00/MTok output)
- Prompt caching: assume NOT supported unless documented.
- Batch API: assume NOT supported unless documented.
- Set explicit `max_tokens` per call — unknown models may generate runaway output.

- [ ] **Check 1:** Model ID verified against shard catalog in `config/settings.json`; no matching named shard found.
- [ ] **Check 2:** `max_tokens` explicitly set in every request.
- [ ] **Check 3:** Function calling schema validated before chaining tool calls.
- [ ] **Check 4:** Reasoning chain ≤4 steps; validation checkpoint added if longer.

</compliance_testing>

<cache_control />

</shard_engine>
