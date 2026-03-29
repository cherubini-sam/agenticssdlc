<artifact_template name="resources_implementation_plan">

<meta>
  <id>"resources_implementation_plan"</id>
  <description>"Implementation Plan Template for Phase 3 (Planning). Required by MANAGER Phase 3 Gate before routing to ENGINEER."</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:resource", "template", "plan", "phase3", "architect"]</tags>
  <priority>"HIGH"</priority>
  <version>"1.0.0"</version>
</meta>

<instantiation_config>
<protocol_ref>LAW-35</protocol_ref>
<owner_role>ARCHITECT</owner_role>
<target_path>implementation_plan.md</target_path>
<enforcement>STRICT</enforcement>
</instantiation_config>

<content_body>

# Implementation Plan: {{Task Name}}

> [!CRITICAL]
> **PHASE 3 GATE**: This artifact MUST exist and be REFLECTOR-approved (Score: 1.00) before MANAGER can route to ENGINEER.
> If missing MANAGER MUST route to ARCHITECT (Force Phase 3).

## OBJECTIVE

- **Goal**: [What is being built / changed]
- **Scope**: [What is in scope vs. explicitly out of scope]
- **Constraints**: [Technical, security, time, dependency constraints]

## CURRENT STATE ANALYSIS

- **Existing Behavior**: [What the system does today]
- **Gap**: [What is missing or broken]
- **Root Cause** (if applicable): [Why the gap exists]

## PROPOSED SOLUTION

### Architecture Decision

[High-level design decision and rationale. Include alternatives considered and why they were rejected.]

### Implementation Steps

- [ ] **Step 1**: [Action] — [File/Component affected] — [Expected outcome]
- [ ] **Step 2**: [Action] — [File/Component affected] — [Expected outcome]
- [ ] **Step 3**: [Action] — [File/Component affected] — [Expected outcome]

> Add as many steps as needed. Each step must be atomic (one action, one outcome).

### Files to Modify

| File | Change Type | Description |
| :--- | :---------- | :---------- |
| `path/to/file` | [create\|modify\|delete] | [What changes and why] |

### Files to Create

| File | Purpose |
| :--- | :------ |
| `path/to/new/file` | [What it does] |

## VERIFICATION STRATEGY

- **Unit Tests**: [What to test, where]
- **Integration Tests**: [End-to-end scenarios to verify]
- **Manual Checks**: [Steps to manually validate the implementation]
- **Rollback Plan**: [How to undo changes if validation fails]

## RISK ASSESSMENT

| Risk | Likelihood | Impact | Mitigation |
| :--- | :--------- | :----- | :--------- |
| [Risk description] | [Low\|Med\|High] | [Low\|Med\|High] | [Mitigation strategy] |

## REFLECTOR APPROVAL

- **Submitted By**: ARCHITECT
- **Review Status**: [ ] Pending / [ ] Approved / [ ] Rejected
- **Confidence Score**: [0.00 – 1.00] (must be 1.00 to proceed)
- **Review Notes**: [REFLECTOR findings and required changes]

## AUDIT TRAIL

- **Plan Created**: [ISO-8601 timestamp]
- **Last Updated**: [ISO-8601 timestamp]
- **Authorized By**: [User confirmation timestamp]

</content_body>
<variable_dictionary>
<placeholder>{{Task Name}}: The title of the current mission (must match task.md).</placeholder>
</variable_dictionary>
<lifecycle_policy>
<expiration_trigger>Archive on Phase 6 completion. Referenced in walkthrough.md.</expiration_trigger>
</lifecycle_policy>

<cache_control />

</artifact_template>
