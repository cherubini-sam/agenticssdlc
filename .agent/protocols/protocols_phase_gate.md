<protocol_framework name="protocols_phase_gate">

<meta>
  <id>"protocols_phase_gate"</id>
  <description>"Phase Gate Protocol - Loaded FIRST on every turn, before routing."</description>
  <globs>[]</globs>
  <alwaysApply>true</alwaysApply>
  <tags>["type:protocol", "gate", "phase1", "law30", "enforcement"]</tags>
  <priority>"CRITICAL"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### PHASE GATE PROTOCOL

<scope>Enforces Law 30 (The Gatekeeper) to ensure task state synchronization before any research or execution actions.</scope>

> [!CRITICAL]
> This protocol is loaded FIRST on every turn.
> It executes BEFORE routing decisions.
> Violations of this gate = SYSTEM FAILURE.

#### GATE LOGIC (IMMUTABLE SEQUENCE)

```
1. Does `task.md` exist?
   ├── NO Create it. STOP. Do not continue this turn.
   └── YES Does it map the CURRENT request?
             ├── NO Re-initialize. STOP.
             └── YES Proceed to routing.
```

#### SESSION START PROTOCOL

> [!CRITICAL]
> **FIRST TURN ENFORCEMENT**
> On session initialization (first turn after restart), the following sequence is MANDATORY:

```
Session Start Sequence (HARD BLOCK):
┌─────────────────────────────────────────────────────┐
│ 1. DETECT: Is this the first turn of a new session? │
├─────────────────────────────────────────────────────┤
│ 2. REINFORCE: Load Active Bootloader override       │
├─────────────────────────────────────────────────────┤
│ 3. FORCE: Route to PROTOCOL agent (Phase 1)         │
│    Reasoning: "Boot Validation Checkpoint"          │
├─────────────────────────────────────────────────────┤
│ 4. EMIT: Tier 1 JSON (Target: PROTOCOL)             │
├─────────────────────────────────────────────────────┤
│ 5. EMIT: Tier 2 JSON (Task: system_integrity_check) │
├─────────────────────────────────────────────────────┤
│ 6. VALIDATE: Protocol returns "Status: Green"       │
├─────────────────────────────────────────────────────┤
│ 7. PROCEED: Manager routes User Request (Phase 1)   │
├─────────────────────────────────────────────────────┤
│ 8. RESET: Force-Archive existing `task.md`          │
│    Action: Create fresh `task.md` from template     │
└─────────────────────────────────────────────────────┘
```

**Session Start Indicators:**

- No previous turn context in conversation history
- User message is the first in a new chat session
- Context window shows session initialization

**Enforcement:** The session start protocol acts as a cognitive forcing function to reinforce the OVERRIDE ACTIVE directive from the Active Bootloader, maximizing compliance probability on session restart.

#### ALLOWED TOOLS DURING GATE

> [!WARNING]
> ONLY these tools are permitted during Phase 1 Gate enforcement:

| Tool            | Purpose                                               |
| --------------- | ----------------------------------------------------- |
| `find_by_name`  | Existence check for task.md/implementation_plan.md    |
| `view_file`     | Read template (MANDATORY BEFORE WRITE)                |
| `write_to_file` | Create artifact (MUST COPY TEMPLATE CONTENT EXACTLY)  |

> [!IMPORTANT]
> ARCHITECT MUST read `.agent/resources/resources_implementation_plan.md` before creating `implementation_plan.md`.
> Any modification to the structural hierarchy of the plan artifact is FORBIDDEN.

**ALL other tools are BLOCKED until gate passes.**

#### BLOCKED TOOLS DURING GATE

The following tools are FORBIDDEN when `task.md` is missing:

- `list_dir` / `Glob` (directory listing use only — `Glob` as `find_by_name` equivalent for task.md existence check IS allowed) — Research action (Phase 2)
- `grep_search` / `Grep` — Research action (Phase 2)
- `run_command` / `Bash` — Execution action (Phase 5)
- `replace_file_content` / `Edit` — Execution action (Phase 5)
- `browser_subagent` / `WebFetch` — Research action (Phase 2)
- `search_web` / `WebSearch` — Research action (Phase 2)

**Violation:** Calling any blocked tool = SYSTEM FAILURE + SESSION TERMINATION.

#### PHASE 3 GATE (PLANNING LOCK)

> [!CRITICAL]
> **STRUCTURAL INTEGRITY MANDATE**
> When transitioning to Phase 3 (Planning), the first turn MUST consist ONLY of the following:
>
> 1. READ `.agent/resources/resources_implementation_plan.md`
> 2. WRITE `implementation_plan.md` (EXACT COPY)
> 3. **STOP.** (Terminate turn without adding content).
>
> **VIOLATION:** Drafting ANY implementation plan content in the same turn as template instantiation, or bypass of the ritual entirely = Law 35 Violation **SESSION INVALID**.

#### STALE TASK DETECTION

A `task.md` is considered STALE if:

1. It references a different user request than the current turn
2. All phases are marked `[x]` (completed) but a new request is received
3. The task name does not match the current intent

**Recovery Action:** Delete stale `task.md` and re-initialize from template.

#### GATE EXIT CONDITIONS

The Phase 1 Gate is PASSED when:

1. `task.md` exists
2. `task.md` maps the CURRENT user request
3. Phase 1 items are marked as completed (`[x]`)

Only then may the agent proceed to Phase 2 (Context) or later phases.

</axiom_core>
<authority_matrix>

### BOOT SEQUENCE INTEGRATION

<scope>Standardizes the order of operations for system initialization.</scope>

```
Boot Sequence Order (SSOT: Active Bootloader Law 1):
┌──────────────────────────────────────────────────────┐
│ 1. Tier 1 JSON (MANAGER Routing) — NO TOOLS YET      │
│    ABSOLUTE FIRST output. No tool calls before this. │
├──────────────────────────────────────────────────────┤
│ 2. Tier 2 JSON (Agent Execution) — NO TOOLS YET      │
│    IMMEDIATE SECOND output. No tool calls before.    │
├──────────────────────────────────────────────────────┤
│ 3. PHASE 1 GATE CHECK (This Protocol)                │
│    FIRST allowed tool calls: Glob / Read / Write     │
│    └── IF FAIL: Create task.md HALT                │
├──────────────────────────────────────────────────────┤
│ 4. Tool Calls / Text Output (Phase 2+)               │
└──────────────────────────────────────────────────────┘
```

</authority_matrix>
<compliance_testing>

### PHASE GATE TEST VECTORS

<scope>Tests for gate-skipping or tool pollution during Phase 1.</scope>

- [ ] **Vector 1:** `grep_search`/`Grep` or `run_command`/`Bash` call when `task.md` is missing. (Expected: BLOCK + SESSION TERMINATION).
- [ ] **Vector 2:** Phase 1 marks `[x]` but request is fresh. (Expected: STALE RECOVERY).

</compliance_testing>

<cache_control />

</protocol_framework>
