<protocol_framework name="protocols_cli">

<meta>
  <id>"protocols_cli"</id>
  <description>"Unified standards for non-interactive CLI execution."</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:protocol", "cli", "execution", "safety"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### CLI EXECUTION STANDARDS

<scope>Unified governance for ALL CLI interfaces to ensure Law 19 (Immediate Execution) and Anti-Hang compliance.</scope>

#### 1. Non-Interactive Execution

**FORBIDDEN:** Commands that open a browser or wait for keyboard input.
**MANDATORY:** Use headless flags (`--force`, `-y`, `--headless`). **TIMEOUT:** Kill processes exceeding 60s without output.

#### 2. Output & Credentials

**Output:** Prefer structured output (`--json`, `--output json`). Minimize terminal noise (Law 19). Redirect `stderr` where appropriate.
**Credentials:** NEVER output to console, markdown, or logs. USE Environment Variables or local ignored config files.

#### 3. Containment (Law 5)

All CLI operations scoped to project root. Block root-level (`/`) operations unless explicitly whitelisted.

</axiom_core>
<authority_matrix>

### TOOL-SPECIFIC REGISTRY

<scope>Per-tool rules are defined in dedicated skills under `.agent/skills/`. Delegate to the appropriate skill when a specific CLI tool is involved (Law 37).</scope>

#### 4. Safety Override Pattern

For any CLI tool that targets a live or production resource:

1. **Default:** BLOCK the operation.
2. **Override:** User must set an explicit `FORCE_<TOOL>_<ACTION>=true` flag in the current turn.
3. **Confirmation:** Agent MUST emit a visible warning before proceeding.

</authority_matrix>
<compliance_testing>

### TEST VECTORS

<scope>Verification commands to confirm non-interactive compliance for all registered CLI tools.</scope>

#### 5. Test Vector

Execute command with `-y` or `--force` to verify non-interactive flow. Confirm no browser or prompt is triggered.

</compliance_testing>

<cache_control />

</protocol_framework>
