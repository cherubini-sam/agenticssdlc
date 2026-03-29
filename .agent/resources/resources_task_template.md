<artifact_template name="resources_task_template">

<meta>
  <id>"resources_task_template"</id>
  <description>"Standard Atomic Task Schema for 6-Phase Industrial Workflow (MANAGER)"</description>
  <globs>[]</globs>
  <alwaysApply>true</alwaysApply>
  <tags>["type:resource", "template", "task", "workflow", "manager"]</tags>
  <priority>"CRITICAL"</priority>
  <version>"1.0.0"</version>
</meta>

<instantiation_config>
<protocol_ref>LAW-30</protocol_ref>
<owner_role>MANAGER</owner_role>
<target_path>task.md</target_path>
<enforcement>STRICT</enforcement>
<integrity_check>SHA-256</integrity_check>
</instantiation_config>

<content_body>

# Task: {{Task Name}}

> [!CRITICAL]
> **SYSTEM INTEGRITY ALERT (LAW-30)**: Adherence to this schema is **NON-NEGOTIABLE**.
> Any deviation from the defined Input/Output chain constitutes a **SYSTEM FAILURE**.
> Strict structural compliance is required to maintain audit trail integrity.

> [!CRITICAL]
> **SINGLETON STATE DIRECTIVE**:
>
> 1. **EPHEMERAL**: This file is **PERMANENTLY ERASED** on new task initiation.
> 2. **ATOMIC**: Mark `[x]` and **SAVE** immediately after every step.
> 3. **TRUTH**: Do not rely on context window. If not saved here, **it did not happen**.

## PRE-FLIGHT INITIALIZATION

- [ ] **[LAW-1] Format Priority**: Output stream initialized with JSON.
- [ ] **[LAW-30] Schema Validation**: `task.md` structure matches current version requirements.
- [ ] **[LAW-34] State Synchronization**: Execution environment verified as Phase 1.
- [ ] **[SEC-01] Path Isolation**: Write access constrained strictly to artifact sandbox.

> [!CRITICAL]
> **MANDATORY STATE VERIFICATION**:
> Review PRE-FLIGHT INITIALIZATION checks.
>
> - **IF ANY** are empty (`[ ]`): You are **FORBIDDEN** from proceeding and review the state.
> - **IF ALL** are checked (`[x]`): You are **ALLOWED** to proceed to OPERATIONAL RISK ASSESSMENT.

## OPERATIONAL RISK ASSESSMENT

- **Security Classification**: [LOW|MEDIUM|HIGH]
- **Data Sensitivity**: [PUBLIC|INTERNAL|CONFIDENTIAL]
- **Resource Impact**: [NEGLIGIBLE|MODERATE|CRITICAL]

## MISSION OBJECTIVES

- **Primary Directive**: [Concise Goal Statement]
- **Strategic Context**: [Business or System justification]
- **Definition of Done (DoD)**: [Specific, measurable completion criteria]

## 6-PHASE INDUSTRIAL WORKFLOW

- [ ] Phase 1: Task Breakdown (Gap Analysis)
  - [ ] [MANAGER] Initialize Task Manifest (instantiate template from `.agent/resources/resources_task_template.md`).
  - [ ] [MANAGER] Verify and confirm Phase 1 gate passed.
  - [ ] [ARCHITECT] Define scope and map relevant capabilities for Skill Mandate (source: `.agent/skills/index.json`).
  - **DoD**: Task manifest is initialized, granular, and scope is locked.

- [ ] Phase 2: Context Retrieval (Research)
  - [ ] [ARCHITECT] Analyze requirements and gather content.
  - [ ] [LIBRARIAN] Aggregate knowledge base assets and fetch files.
  - **DoD**: All required context is loaded into active memory.

- [ ] Phase 3: Planning (Architect Design)
  - [ ] [ARCHITECT] Initialize Implementation Plan (instantiate template from `.agent/resources/resources_implementation_plan.md`).
  - [ ] [ARCHITECT] Draft technical content and define verification strategy.
  - **DoD**: Plan is fully documented, feasible, and verifiable.

- [ ] Phase 4: Critique (Reflector Audit)
  - [ ] [REFLECTOR] Conduct compliance audit and review Implementation Plan.
  - [ ] [ARCHITECT] Review Implementation Plan and remediate deficiencies.
  - [ ] [MANAGER] Request user authorization to proceed (output authorization request directly to user).
  - **DoD**: Plan is validated by Reflector and authorized by User.

- [ ] Phase 5: Execution (Engineer Build)
  - [ ] [ENGINEER] Execute implementation.
  - [ ] [PROTOCOL] Enforce Security Standards.
  - [ ] [LIBRARIAN] Synchronize Documentation.
  - **DoD**: Code is implemented, audited, and documented.

- [ ] Phase 6: System verification (Validator Test)
  - [ ] [VALIDATOR] Execute validation and test suite.
  - [ ] [MANAGER] Generate proof of work (compile `walkthrough.md`).
  - [ ] [MANAGER] Finalize session (sanitize artifact sandbox).
  - **DoD**: System passes all validations and session state is archived.

## AUDIT TRAIL

- **Timestamp Created**: [ISO-8601]

</content_body>
<variable_dictionary>
<placeholder>Definitions of {{Task Name}}: The title of the current mission.</placeholder>
<overrides>Phase-specific DoD overrides can be injected dynamically.</overrides>
</variable_dictionary>
<lifecycle_policy>
<expiration_trigger>Delete on mission completion(Phase 6).</expiration_trigger>
</lifecycle_policy>

<cache_control />

</artifact_template>
