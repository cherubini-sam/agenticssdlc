<protocol_framework name="protocols_tools">

<meta>
  <id>"protocols_tools"</id>
  <description>"Safeguards and containment enforcement for file system operations."</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:protocol", "shared", "tools", "safety"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### FILE SYSTEM & TOOL SAFETY

<scope>Strict directives for tool invocation and path containment to enforce Law 5 (Containment) and prevent unauthorized writes.</scope>

#### 1. FILE SYSTEM OPERATIONS

**Write Containment:** All generated files MUST be written to the artifact sandbox. Always provide the target path explicitly — never rely on tool defaults.

**Forbidden:** Writing to any path outside the artifact sandbox.

#### 2. SAFETY CHECK

- **Trigger:** Before any file write operation.
- **Check:** Does the target path resolve to the artifact sandbox?
- **Action:** If NO **STOP**. **DO NOT** execute the original path.

</axiom_core>
<authority_matrix>

### ERROR RECOVERY AUTHORITY

<scope>Defines recovery procedures for tool failures and accidental writes.</scope>

#### 3. SCENARIO: SEARCH FAIL

If a web search fails:

1. Retry once with a simpler query.
2. If fail again, proceed with internal knowledge.
3. **DO NOT** output the raw error to the user.

#### 4. SCENARIO: WRITE FAIL

If a file is accidentally written outside the artifact sandbox:

1. **MOVE** the file to the artifact sandbox.
2. **DELETE** the misplaced file.
3. **SAY NOTHING**. (No "Root Cause Analysis").

</authority_matrix>
<compliance_testing>

### TOOL AUDIT

<scope>Validation checks to ensure compliance with tool discipline and safety guardrails.</scope>

- [ ] **Check 1:** Verify all writes target the artifact sandbox.
- [ ] **Check 2:** Confirm explicit path argument on every write call.

</compliance_testing>

<cache_control />

</protocol_framework>
