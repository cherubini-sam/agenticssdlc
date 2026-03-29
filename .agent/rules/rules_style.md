<governance_logic name="rules_style">

<meta>
  <id>"rules_style"</id>
  <description>"Hygiene, formatting, and implementation standards for artifacts and code."</description>
  <globs>[]</globs>
  <alwaysApply>true</alwaysApply>
  <tags>["type:rule", "style", "formatting", "hygiene"]</tags>
  <priority>"HIGH"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### STYLE AXIOMS

<scope>Core language, formatting, and code hygiene standards governing all agent output and artifact generation.</scope>

#### Language (Law 18)

Input other language: output other language (100% strictness). Exception: technical terms, code, and comments prioritize clarity. On mismatch: REGENERATE output; FORCE other language for user-facing messaging. Bypass: explicit user request for English or technical documentation.

#### Formatting (Law 19)

Zero Fluff. `thinking_process` tag MANDATORY for complex reasoning and multi-tool logic. No emojis in source code, filenames, or system artifacts. Standard: Markdown. Bypass: UI mockup generation or explicitly creative requests.

#### Code Standards

Type annotations mandatory (static analysis compatibility). Docstrings: standard format for the active language. Error handling required on all file and network I/O. Prohibited: no-op stubs, `TODO`, commented-out blocks, placeholder markers in production. Delete old files immediately after successful refactor.

</axiom_core>
<authority_matrix>

### ARTIFACT AUTHORITY

<scope>Enforcement hierarchy for artifact schema compliance and coding standard violation handling.</scope>

#### Artifact Schema (Law 33)

Scope: `task.md` and `implementation_plan.md` in the artifact sandbox. H2 (`##`) for major logical sections. Checkbox syntax (`- [ ]` pending, `- [x]` complete) for status. Plan updates MUST append a "Revision History" section — never truncate design history. REJECT update if structural hierarchy is broken or history is truncated.

#### Violation Consequences

| Violation | Action |
| :--- | :--- |
| Language mismatch | REGENERATE in correct language; LOG WARNING |
| Emoji in critical path | LOG WARNING + strip |
| Placeholder / pass-zombie in production | HALT execution; DENY commit |
| Artifact hierarchy or history broken | REJECT update |

</authority_matrix>
<compliance_testing>

### STYLE AUDIT

<scope>Pre-output checklist to enforce hygiene standards on every agent turn.</scope>

- [ ] **Check 1:** Output language matches session language (Law 18).
- [ ] **Check 2:** No emojis in code, filenames, or system artifacts (Law 19).
- [ ] **Check 3:** No TODO / TBD / placeholder markers / no-op stubs in production code (Law 11).
- [ ] **Check 4:** Artifact hierarchy uses H2 + checkbox syntax (Law 33).

</compliance_testing>

<cache_control />

</governance_logic>
