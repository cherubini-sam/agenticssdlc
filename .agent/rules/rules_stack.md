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

#### LLM Runtime — Active Shard

Model is detected per session from: (1) `$AGENT_ACTIVE_MODEL` env var (takes precedence); (2) active bootloader model detection block. Loaded as an immutable shard.

| Shard | Model ID | Context In | Max Out | Reasoning |
| :--- | :--- | :--- | :--- | :--- |
| `shards_generic_llm` | Any model | Assume 128K | Assume 4K–8K | Prompt-based CoT only |

Shard catalog is intentionally minimal — one universal fallback. Add named shards by creating `shards_<provider>_<tier>.md` and registering in `config/settings.json` `shard_catalog`.

Cache min: 1024 tokens (short-context providers) / 4096 tokens (long-context providers). Consult active shard for exact pricing.

#### Cost Controls

| Threshold | Action |
| :--- | :--- |
| Single request > 50K tokens | LOG WARNING |
| Session total > 500K tokens | STOP + REQUEST CHECKPOINT |

Bypass: manual user override for large-scale codebase migrations.

</axiom_core>
<authority_matrix>

### 4-TIER MODEL ROUTING STRATEGY

<scope>Authoritative routing rules mapping task complexity to model tier. Deviations require user approval.</scope>

| Tier | Target | Use Case | Trigger Classification |
| :--- | :--- | :--- | :--- |
| Tier 1 | Highest-capability model in active shard family | Architecture, security audits, complex orchestration, frontier reasoning | `system_design`, `security_audit`, `complex_reasoning` |
| Tier 2 | Dynamic — orchestrator selects based on load | Complex tasks where depth is uncertain; defaults to balanced tier | `inherit` — MANAGER sets dynamically |
| Tier 3 | Balanced model in active shard family | Standard implementation, debugging, unit tests, bulk engineering | `implementation`, `refactor`, `bug_fix`, `test_generation` |
| Tier 4 | Fastest / cheapest model in active shard family | Read-only exploration, documentation, codebase search, analysis | `exploration`, `documentation`, `analysis` |

**Routing rule:** Expensive models plan and orchestrate; efficient models execute in parallel.

LOG WARNING and notify user on any stack deviation. Bypass: explicit user override for environment-specific configurations.

</authority_matrix>
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
