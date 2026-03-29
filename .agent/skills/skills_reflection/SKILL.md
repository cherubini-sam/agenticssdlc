<skill_manifest name="skills_reflection">

<meta>
  <id>"skills_reflection"</id>
  <description>"Skill for structured self-critique and output refinement"</description>
  <globs>["**/*.py", "**/*.md", ".contexts/review/**/*"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "reflection", "critique", "quality"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Structured self-critique and iterative output refinement.
**Triggers:** "review", "critique", "improve quality", "verify", "refine".

</io_contract>
<state_mode>Stateless (Quality Audit)</state_mode>
<dependencies>

- `resources/quality_scoring.md` (Rubric)
- Structural patterns for CoT/Few-Shot

</dependencies>
<env_vars>N/A</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. Reflection Cycle (Generate -> Critique -> Refine -> Verify)

1. **Generate:** Process output and document assumptions.
2. **Critique:** Multi-perspective analysis (Correctness, Completeness, Style, Efficiency).
3. **Refine:** Fix critical issues first; preserve functionality.
4. **Verify:** Calculate quality score and re-check requirements.

## 2. Reflection Prompts

Use targeted prompts for Code (edge cases, security), Documentation (clarity, examples), and Architecture (trade-offs, scaling).

</operational_steps>
<error_protocol>

Avoid anti-patterns: Confirmation Bias, Endless Refinement (Max 3 cycles), and Scope Creep.

</error_protocol>
<side_effect_protocol>
<idempotency_key>N/A</idempotency_key>
<rollback_logic>Keep the previous cycle's output as a backup in case refinement introduces errors.</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

- Maximum 3 reflection cycles before requiring human review.
- Enhancement logs must be kept separate from core bug fixes.

</permissions>
<rate_limit>

Assign severity (Critical/Major/Minor) to all issues and prioritize Critical fixes.

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
