<skill_manifest name="skills_project_onboarding">

<meta>
  <id>"skills_project_onboarding"</id>
  <description>"Skill for rapidly understanding new codebases"</description>
  <globs>["README.md", "package.json", "pyproject.toml", "setup.py", "Cargo.toml", "go.mod"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "onboarding", "analysis", "codebase-understanding"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Rapidly assimilate context from a new or unfamiliar codebase with automated analysis
**Triggers:** "onboard", "analyze project", "understand codebase", "summary", "project structure"

</io_contract>
<state_mode>Read-only (Context Assimilation)</state_mode>
<dependencies>

- `scripts/scripts_mapper.py` (Mapping)
- `scripts/scripts_classifier.py` (Arch Classification)
- `scripts/scripts_health_check.py` (Validation)
- `scripts/scripts_dep_analyzer.py` (Dependency Trees)
- `resources/onboarding_template.md` (Reporting)

</dependencies>
<env_vars>N/A</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. The "Smart Scan" Protocol

1. **Map:** Depth 3 directory tree.
2. **Stack:** ID frameworks/versions.
3. **Entry:** Locate `main`, `index`, `App`.
4. **Docs:** Read core manuals (README, etc.).
5. **Config:** ID environment setup.
6. **Tests:** Check coverage metrics.

## 2. Archetype Classification

ID project as Monolith, Microservices, Library, or Monorepo.

</operational_steps>
<error_protocol>

If archetype is unknown, perform manual scan of top-level directories to identify custom structures.

</error_protocol>
<side_effect_protocol>
<idempotency_key>Safe (Read-only)</idempotency_key>
<rollback_logic>N/A</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

- Read-only analysis.
- Restricted to filesystem boundary of the project.

</permissions>
<rate_limit>

Follow "Health Check" verification checklist for all reports.

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
