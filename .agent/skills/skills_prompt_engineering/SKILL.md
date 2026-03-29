<skill_manifest name="skills_prompt_engineering">

<meta>
  <id>"skills_prompt_engineering"</id>
  <description>"Skill for designing and optimizing LLM prompts"</description>
  <globs>["**/*prompt*", "**/*system*", ".cursor/rules/**", ".agent/**/*.md"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "prompt", "optimization", "llm", "ai"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Design, test, and optimize LLM prompts for maximum effectiveness with automated testing.
**Triggers:** "improve prompt", "prompt design", "system prompt", "optimize instructions", "prompt testing".

</io_contract>
<state_mode>Stateless (Prompt Logic)</state_mode>
<dependencies>

- `scripts/scripts_prompt_chunker.py` (Compression)
- `scripts/scripts_prompt_tester.py` (Evaluation)
- `scripts/scripts_prompt_optimizer.py` (Auto-optimization)
- `resources/prompt_versions.json` (Versioning)
- `resources/prompt_templates.md` (Blueprints)

</dependencies>
<env_vars>N/A</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. Prompt Structure (Best Practices)

Follow the [ROLE], [CONTEXT], [TASK], [FORMAT], [CONSTRAINTS], and [EXAMPLES] structural pattern.

## 2. Testing Protocol

1. **Baseline:** Measure current quality.
2. **Variants:** Create A/B test prompts.
3. **Evaluate:** Use accuracy, relevance, and format metrics.
4. **Iterate:** Refine and document results.

## 3. Advanced Techniques

- **Chain of Thought:** "Think step-by-step".
- **Few-Shot:** Provide explicit I/O examples.
- **XML Tags:** Use `<task>`, `<code>`, etc., for structural clarity.

</operational_steps>

<error_protocol>

- Identify and avoid common anti-patterns (excessive politeness, ambiguity, redundancy).
- Use versioning in `prompt_versions.json` for rollback capability.

</error_protocol>
<side_effect_protocol>
<idempotency_key>N/A</idempotency_key>
<rollback_logic>Revert to the previous version in `prompt_versions.json` if evaluation metrics drop below baseline.</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

- Automated optimization limited to within-prompt phrasing.
- System logic changes require explicit ARCHITECT review.

</permissions>
<rate_limit>

Token Optimization: Apply compression and chunking strategies to minimize LLM costs.

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
