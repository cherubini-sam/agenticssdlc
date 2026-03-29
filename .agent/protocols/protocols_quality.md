<protocol_framework name="protocols_quality">

<meta>
  <id>"protocols_quality"</id>
  <description>"Content and output quality validation checkpoints."</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:protocol", "quality", "standards", "validation"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### SHARED CONTENT QUALITY STANDARDS

<scope>Defines content depth, writing style, naming conventions, and artifact schemas for all agent-produced output.</scope>

> [!IMPORTANT]
> **Emoji Policy:** STRICTLY FORBIDDEN. **Tone:** Technical, Professional, Zero-Fluff.
> **Input:** `@File` preferred. **Output:** Unified Diff or New File.

#### 1. Content Depth (Zero Tolerance)

**Forbidden:** "TODO", "TBD", Placeholders. **Requirement:** Complete, working code/docs.

#### 2. Writing Style

**Allowed:** Passive (desc), Active (instr). **Forbidden:** Slang, First-person.

#### 3. Naming Conventions

`README.md`: "{Project} Documentation" | `CHEATSHEET.md`: "{Project} Cheatsheet"

#### 4. Artifact Schemas (JSON Enforced)

- **Session Report:** `executive_summary`, `activities`, `blockers`, `next_steps`, `metrics`.
- **Architecture Decision:** `context`, `decision`, `rationale`, `alternatives`, `consequences`.
- **Conversation Log:** `user_request`, `solution`, `plan`.

</axiom_core>
<authority_matrix>

### DEFINITION OF DONE

<scope>Strict completion criteria enforcing 6-Phase workflow compliance and template fidelity.</scope>

#### 5. Definition of Done (Strict 6-Phase)

- **Workflow Completion:** All 6 phases (1–6) verified.
- **Context Retention:** 100% of artifacts saved.
- **Template Compliance:** Artifacts match `.agent/resources/` definitions exactly.

</authority_matrix>
<compliance_testing>

### VERIFICATION PROTOCOL

<scope>Pre-completion checklist to validate quality gate compliance before session close.</scope>

#### 6. Verification Protocol

Before completion: No emojis | Copyright present | No placeholders | Schemas valid | Phase Isolation enforced (Law 33).

</compliance_testing>

<cache_control />

</protocol_framework>
