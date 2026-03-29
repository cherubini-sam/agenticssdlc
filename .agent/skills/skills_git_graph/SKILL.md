<skill_manifest name="skills_git_graph">

<meta>
  <id>"skills_git_graph"</id>
  <description>"Skill for visualizing and interpreting git history"</description>
  <globs>["**/.git/**"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "git", "visualization"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Visualize and articulate commit history, branching, and merges.
**Triggers:** "visualize git", "graph history", "show commits", "who changed x".

</io_contract>
<state_mode>Read-only (Git Ops)</state_mode>
<dependencies>

- `git` CLI

</dependencies>
<env_vars>N/A</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. Visualization Command

When requested, ALWAYS run:

```bash
git log --graph --oneline --all --decorate --color=always -n 20
```

## 2. Interpretation Logic

- **`*` (Asterisk):** Commit.
- **`|` / `\` / `/`:** Branch lines/merges.
- HEAD: Current pointer.

</operational_steps>
<error_protocol>

If git log fails, verify `.git` directory presence and permissions.

</error_protocol>
<side_effect_protocol>
<idempotency_key>Safe (Read-only)</idempotency_key>
<rollback_logic>N/A</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

- Read-only history visualization.
- Limited to top 20 commits by default to prevent buffer overflow.

</permissions>
<rate_limit>

Constraint: articulates history narratively, does not modify commits.

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
