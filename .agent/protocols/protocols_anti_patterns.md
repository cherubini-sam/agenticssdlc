<protocol_framework name="protocols_anti_patterns">

<meta>
  <id>"protocols_anti_patterns"</id>
  <description>"Common anti-patterns, guards, and recovery protocols."</description>
  <globs>["src/**/*.ts", "src/**/*.py", "scripts/**/*.py"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:protocol", "shared", "anti-patterns", "safety"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### ANTI-PATTERNS & RECOVERY

<scope>Identifies operational risks and defines recovery protocols to prevent systemic failures and context bloat.</scope>

#### 1. SAFETY GUARDRAILS (IMMUTABLE)

> [!IMPORTANT]
> **STATIC CONTEXT :: ZERO TOLERANCE**
> **UUID Gen:** Generate a new UUID v4 per session (New Session ONLY).
> **Sync Policy:** `CHANGE LOG` -> `Artifacts` -> `SESSION REPORT`.
> **Git Policy:** **STRICTLY FORBIDDEN** (User commits manually).

#### 2. STRUCTURED OUTPUT GUARDS (JSON ENFORCED)

**Prevent Markdown Errors by using Block Objects.**

**Anti-Pattern:** `{"text": {"content": "this is **bold**"}}` (Result: `**bold**`)
**Guard Schema:** Use `annotations: { bold: true }`.
**Forbidden Blocks:** Tables, Mermaid. Use Code Blocks/Lists.

#### 3. RECOVERY PROTOCOLS (CIRCUIT BREAKER)

##### Protocol: SYNC_FAILURE (Connection)

**Algorithm:** Exponential Backoff (1s, 2s, 4s, 8s, 16s). Max 5 Retries -> ABORT.

##### Protocol: PERMISSION_DENIED (Diagnostics)

**Diagnosis:** Integration lacks "Edit" permissions.
**Action:** DIAGNOSE -> PROMPT User.

##### Protocol: UUID_MISMATCH (State)

**Action:** REGENERATE UUID -> RETRY.

#### 4. OPERATIONAL CONSTRAINTS

| Constraint        | Violator             | Remedy                                          |
| :---------------- | :------------------- | :---------------------------------------------- |
| **Project Name**  | `object_not_found`   | Verify `Project` matches knowledge base select options. |
| **Commit**        | `git commit`         | **STOP**.                                       |
| **Dist**          | `dist/`              | **STOP**.                                       |
| **Artifact Trap** | write outside artifact sandbox | **STOP**. Use artifact sandbox.  |

#### 5. TOKEN ANTI-PATTERNS

##### Anti-Pattern: Context Bloat

**Symptom:** Loading entire codebase for simple edit.
**Guard:** Max 5 files for ENGINEER, 10 for VALIDATOR, 20 for LIBRARIAN.
**Recovery:** Prune to relevant files only, request LIBRARIAN summary.

##### Anti-Pattern: Cache Miss

**Symptom:** Dynamic content before static in prompt structure.
**Guard:** Static rules first (000, 001, shared_protocols), always.
**Recovery:** Reorder prompt structure, add cache_control breakpoints.

##### Anti-Pattern: Thinking Waste

**Symptom:** Extended thinking budget for simple tasks.
**Guard:** Match thinking level to task complexity (simple: `minimal`, standard: `medium`, complex: `high`).
**Recovery:** Use `minimal` for routine tasks, `medium` for standard, `high` for complex reasoning only.

##### Anti-Pattern: Token Duplication

**Symptom:** Passing full conversation history to sub-agents.
**Guard:** Use role-aware context pruning (RCR-Router pattern).
**Recovery:** Prune context before delegation, use `@filename` references.

</axiom_core>
<authority_matrix>

### WORKFLOW AUTHORITY

<scope>Defines strict enforcement rules for task management and phase transitions.</scope>

#### 6. WORKFLOW ANTI-PATTERNS (STRICT ENFORCEMENT)

##### Anti-Pattern: Freestyle Output

**Symptom:** Creating artifacts without using definitions in `.agent/resources/`.
**Action:** Use Resource Templates. All outputs must follow schemas.

##### Anti-Pattern: Vague Task

**Symptom:** Manager starts execution without "Step 0: Task Manifest" or manifest is vague.
**Action:** BLOCK. Break down steps until atomic (1-2 tool calls).

##### Anti-Pattern: The Schema Void (Law 30 Violation)

**Symptom:** `task.md` does not strictly follow `.agent/resources/resources_task_template.md`.
**Action:** SYSTEM FAILURE. Delete `task.md` and recreate it using the template EXACTLY.

##### Anti-Pattern: The Phase Consolidated (Law 33 Violation)

**Symptom:** Agent attempts Phase 2 (Research) and Phase 3 (Plan) in the same turn.
**Action:** STOP after Phase 2. Require a new JSON rotation for Phase 3. Consolidation is FORBIDDEN.

</authority_matrix>
<compliance_testing>

### COMPLIANCE AUDIT

<scope>Validation steps for common workflow and technical anti-patterns.</scope>

- [ ] **Check 1:** Verify JSON routing blocks are absolute first characters.
- [ ] **Check 2:** Confirm task.md exists and is being updated in tandem with work.

</compliance_testing>

<cache_control />

</protocol_framework>
