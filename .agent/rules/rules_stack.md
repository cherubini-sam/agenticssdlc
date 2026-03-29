<governance_logic name="rules_stack">

<meta>
  <id>"rules_stack"</id>
  <description>"Technical stack specifications and token budget policing."</description>
  <globs>[]</globs>
  <alwaysApply>true</alwaysApply>
  <tags>["type:rule", "stack", "performance", "environment"]</tags>
  <priority>"HIGH"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### TOKEN & COST AXIOMS

<scope>Core token budget and cost thresholds governing all agent inference operations across supported model families.</scope>

#### LLM Runtime — Supported Models

Model is detected per session via `CLAUDE.md` model detection block and loaded as an immutable shard.

| Shard | Model ID | Context In | Max Out | Reasoning |
| :--- | :--- | :--- | :--- | :--- |
| `shards_claude_haiku_4` | `claude-haiku-4-5` | 200K | 64K | Budget-controlled (opt-in) |
| `shards_claude_sonnet_4` | `claude-sonnet-4-6` | 200K | 128K | Adaptive effort (low/medium/high/max) |
| `shards_claude_opus_4` | `claude-opus-4-6` | 200K (1M beta) | 128K | Adaptive effort — default: high |
| `shards_gemini_3_flash` | `gemini-3-flash` | 200K | 64K | Levels: minimal/low/medium/high |
| `shards_gemini_3_pro` | `gemini-3.1-pro` | 1M | 64K | Levels: low/medium/high — default: high |
| `shards_gemini_ultra` | `gemini-3-deep-think` | 1M | Unlimited | Deep Reasoning — always max, not configurable |
| `shards_generic_llm` | Any unrecognized model | Assume 128K | Assume 4K–8K | Prompt-based CoT only |

Cache Min: 1024 tokens (Anthropic) / 4096 tokens (Google). Consult active shard for pricing.

#### Cost Controls

| Threshold | Action |
| :--- | :--- |
| Single request > 50K tokens | LOG WARNING |
| Session total > 500K tokens | STOP + REQUEST CHECKPOINT |

Bypass: manual user override for large-scale codebase migrations.

</axiom_core>
<compliance_testing>

### STACK AUDIT

<scope>Pre-execution checklist to validate stack and token budget compliance.</scope>

- [ ] **Check 1:** Active model matches a recognized shard; shard loaded and immutable for session.
- [ ] **Check 2:** Request token count < 50K; session total < 500K.
- [ ] **Check 3:** Pytest suite present for all Python source code.
- [ ] **Check 4:** Infrastructure targets match authoritative stack configuration.

</compliance_testing>

<cache_control />

</governance_logic>
