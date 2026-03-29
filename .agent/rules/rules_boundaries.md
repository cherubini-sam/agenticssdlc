<governance_logic name="rules_boundaries">

<meta>
  <id>"rules_boundaries"</id>
  <description>"Strict system constraints for security, context management, and filesystem firewalls."</description>
  <globs>[]</globs>
  <alwaysApply>true</alwaysApply>
  <tags>["type:rule", "boundaries", "security", "safety"]</tags>
  <priority>"HIGH"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### SECURITY AXIOMS

<scope>Core security constraints and context limits governing all agent operations.</scope>

#### Security Redlines

REDACT all secrets: keys, passwords, and sensitive identifiers MUST be masked (`******`). Zero External Access: NO network access without explicit user permission (Law 7). Destruction Guard: structural commands (`rm`, `delete`, `drop`) REQUIRE Dry Run verification before execution. BLOCK unauthorized access; DENY destructive commands without Dry Run.

#### Context Boundaries

Max 5 active files per turn for surgical access. STOP for mapping if > 5 files required. Phase 2 BYPASS ACTIVE: protocol/role/config files during Phase 2 initialization are exempt from the 5-file cap (10–20 system files legitimate). Cap resumes at Phase 3. Bypass: manual user override for batch operations.

</axiom_core>
<authority_matrix>

### BOUNDARY AUTHORITY

<scope>Filesystem zones and phase transition rules enforcing Law 5 and Law 33.</scope>

#### Filesystem Firewall (Law 5)

| Zone | Path | Access |
| :--- | :--- | :--- |
| Artifact Sandbox | `task.md`, `implementation_plan.md`, Reports | R/W |
| Workspace | `./` Code, Configs, Tests | R/W |
| Agent Config | `.agent/protocols/` | READ ONLY |
| Forbidden | `/`, `.git` | BLOCK |

BLOCK tool execution in forbidden zones; REJECT writes outside designated R/W paths.

#### Phase Firewall (Law 33)

Illegal combinations in one turn: P2+P3, P3+P5, P5+P6. Safety: if terminal output is `[OUTPUT NOT AVAILABLE]`, mandatory fetch (Loop 2) required before acting. HALT and enforce turn-break lifecycle protocol. Bypass: explicit `// turbo` annotations in approved plans.

</authority_matrix>
<compliance_testing>

### BOUNDARY AUDIT

<scope>Pre-action checklist to verify security and isolation constraints.</scope>

- [ ] **Check 1:** No secrets exposed in any output stream (Law 6).
- [ ] **Check 2:** Active file count ≤ 5 (Phase 2 exemption applied if applicable).
- [ ] **Check 3:** All writes target authorized zones only (Law 5).
- [ ] **Check 4:** No illegal phase combinations in current turn (Law 33).

</compliance_testing>

<cache_control />

</governance_logic>
