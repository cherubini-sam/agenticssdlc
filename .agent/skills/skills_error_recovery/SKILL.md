<skill_manifest name="skills_error_recovery">

<meta>
  <id>"skills_error_recovery"</id>
  <description>"Skill for systematic debugging and error recovery"</description>
  <globs>["**/*.log", "**/*.err", "**/error*", "**/*traceback*"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "debugging", "recovery", "troubleshooting"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Systematic debugging and error resolution with automated diagnostics
**Triggers:** "debug", "fix error", "troubleshoot", "why failing", "exception", "crash"

</io_contract>
<state_mode>Stateless (Diagnostic Analysis)</state_mode>
<dependencies>

- `scripts/scripts_diagnostics.py` (Pattern Detection)
- `scripts/scripts_stack_analyzer.py` (Source Highlighting)
- `resources/recovery_templates.md` (Common Patterns)

</dependencies>
<env_vars>N/A</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. Diagnostic Protocol (5-Step Method)

1. **Reproduce:** Iterate steps to trigger error.
2. **Isolate:** Narrow down source (file/line).
3. **Analyze:** Diagnostic read of traces/logs.
4. **Hypothesize:** Form 3 root causes.
5. **Test:** Systematic verification.

## 2. Stack Trace Analysis

Read bottom to top to identify ownership (documented in protocol).

## 3. Recovery Actions

- **Rollback:** Revert if caused by regression.
- **Patch:** Immediate minimal fix.
- **Refactor:** Architectural fix if necessary.

</operational_steps>
<error_protocol>

Use `scripts/scripts_diagnostics.py` to identify failure modes and suggest root causes.

</error_protocol>
<side_effect_protocol>
<idempotency_key>N/A</idempotency_key>
<rollback_logic>Undo any temporary patches if validation test fails (refer to Phase 6 checklist).</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

- Read-mostly diagnostics.
- Automated recovery limited to known patterns in `recovery_templates.md`.

</permissions>
<rate_limit>

Follow the 5-Step diagnostic protocol; skip no steps.

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
