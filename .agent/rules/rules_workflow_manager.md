<governance_logic name="rules_workflow_manager">

<meta>
  <id>"rules_workflow_manager"</id>
  <description>"Mandatory industrial cycle enforcement and task manifest lifecycle."</description>
  <globs>[]</globs>
  <alwaysApply>true</alwaysApply>
  <tags>["type:rule", "workflow", "manager", "phase-gate"]</tags>
  <priority>"CRITICAL"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### WORKFLOW AXIOMS

<scope>Core boot and task manifest lifecycle rules governing all MANAGER-orchestrated sessions.</scope>

#### Protocol Boot (Law 2)

Turn 0: route EXCLUSIVELY to PROTOCOL agent (`intent: "boot_validation"`). Verify roles, resources, Core Laws, and Active Bootloader bridge. Block all routing until status is "system_green". Bypass: none for production environments.

#### Task Manifest Lifecycle (Law 30)

P1 Mandate: create or overwrite `task.md` using `resources_task_template.md`. Stale Guard: missing or intent-mismatched `task.md` STOP immediately. Velocity: HALT turn immediately after `task.md` creation. Bypass: explicit emergency debugging requested by user.

</axiom_core>
<authority_matrix>

### WORKFLOW AUTHORITY

<scope>Phase whitelist and atomicity constraints enforcing the 6-Phase Industrial Standard.</scope>

#### Phase 1 Tool Whitelist (Law 31)

**Allowed:** `find_by_name`, `view_file`, `write_to_file` (see Active Bootloader for AI tool mapping).
**Banned:** `list_dir`, `grep_search`, `run_command`, `browser`, `read_url`. DENY banned tools; HALT on whitelist violation. Bypass: none.

#### Execution Cycle Atomicity (Law 33)

Sequence: P1(Task) P2(Context) P3(Plan) P4(Reflect) P4.5(Gate) P5(Exec) P6(Verify).
Zero-Velocity Mandate: max 1 phase per turn. Consolidated turns are FORBIDDEN. HALT and break turn after each logical phase. Bypass: `// turbo` annotations in authorized implementation plans.

> [!CAUTION]
> Protocol violations (missing JSON, wrong tool in P1) SESSION TERMINATION per Active Bootloader. No recovery. Stale `task.md` overwrite is NOT a violation — re-initialize P1 only.

</authority_matrix>
<compliance_testing>

### WORKFLOW AUDIT

<scope>Pre-execution checklist to verify boot integrity and phase isolation.</scope>

- [ ] **Check 1:** Turn 0 routed to PROTOCOL; "system_green" confirmed (Law 2).
- [ ] **Check 2:** `task.md` present, valid, and maps current request (Law 30).
- [ ] **Check 3:** Only whitelisted tools invoked during Phase 1 (Law 31).
- [ ] **Check 4:** Max 1 phase boundary crossed in current turn (Law 33).

</compliance_testing>

<cache_control />

</governance_logic>
