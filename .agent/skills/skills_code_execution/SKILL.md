<skill_manifest name="skills_code_execution">

<meta>
  <id>"skills_code_execution"</id>
  <description>"Skill for sandboxed code execution and data analysis"</description>
  <globs>["**/*.py", "scripts/**/*", "data/**/*"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "execution", "sandbox", "analysis"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Execute Python code in sandboxed environment for data analysis and computation
**Triggers:** "run code", "execute", "analyze data", "compute", "calculate", "visualize"

</io_contract>
<state_mode>Stateless (Sandboxed)</state_mode>
<dependencies>

- `scripts/validator.py` (Validation Logic)
- `resources/output_template.json` (Formatting)

</dependencies>

<env_vars>N/A</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. Execution Protocol

### Step 1: Code Validation

Use the validation logic in `scripts/validator.py` to identify forbidden patterns before execution.

### Step 2: Sandbox Setup

- Create isolated execution environment
- Pre-load allowed libraries
- Set resource limits
- Redirect stdout/stderr

### Step 3: Execution

- Run code with timeout
- Capture all output
- Handle exceptions gracefully
- Collect artifacts (plots, data)

### Step 4: Result Processing

- Format output using the `output_template.json` in `resources/`
- Encode images as base64
- Summarize large outputs
- Report execution metadata

</operational_steps>
<error_protocol>

### Error Handling

- **Security Violation:** If `contains_forbidden_pattern(code)` from `scripts/validator.py` returns true, abort execution and report the detected patterns.
- **Resource Limits:** Handle `TimeoutError` and `MemoryError` by reporting them in the status field of the output JSON.

</error_protocol>
<side_effect_protocol>
<idempotency_key>N/A (Read-mostly analysis)</idempotency_key>
<rollback_logic>Terminate sandbox process and purge temporary artifacts.</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

## 2. Sandbox Constraints

### Allowed Operations

- Mathematical computation (numpy, scipy)
- Data manipulation (pandas)
- String processing
- JSON/CSV parsing
- Visualization (matplotlib, basic plots)
- File reading (within sandbox)

### Forbidden Operations

- Network access (requests, urllib)
- File system writes (outside sandbox)
- System calls (os.system, subprocess)
- Package installation (pip, conda)
- Environment variable access
- Process spawning

</permissions>
<rate_limit>

| Resource       | Limit        |
| :------------- | :----------- |
| Execution time | 5 minutes    |
| Memory         | 512 MB       |
| Output size    | 10 MB        |
| File reads     | Sandbox only |

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
