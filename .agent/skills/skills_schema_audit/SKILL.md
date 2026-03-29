<skill_manifest name="skills_schema_audit">

<meta>
  <id>"skills_schema_audit"</id>
  <description>"USE WHEN validating .agent/ directory XML schema compliance, running a full integrity audit at session start, or after any structural change to protocols, roles, rules, or shards."</description>
  <globs>[".agent/**/*.md"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "audit", "schema", "validation", "integrity", "protocol"]</tags>
  <priority>"HIGH"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>

#### 1. Trigger Conditions & Invocation

##### 1.1 Invocation Signals

This skill MUST be invoked by PROTOCOL (Phase 1) or any agent when:

- A new session starts and `protocol_status` has not been confirmed this session.
- Any `.agent/*.md` file is created, modified, or deleted.
- An agent reports a schema violation it cannot self-resolve.
- The user explicitly requests an integrity audit.
- A merge or rebase touches the `.agent/` directory.

**Law 36 mandate:** Agents MUST check `.agent/skills/` before proceeding. This skill is the authoritative handler for all `.agent/` schema compliance work.

##### 1.2 Inputs & Outputs

**Input:** The `.agent/` directory tree (read-only).
**Output:** A structured audit report (see §4 Report Format). The report is the ONLY artifact produced. No files are modified by this skill.

</interface_definition>

<execution_logic>

#### 2. Canonical Schema Reference (SSOT)

##### 2.1 Domain Root Tag Required Children

| Domain | Root Tag | Required Children (in order) |
|:-------|:---------|:-----------------------------|
| `protocols/` | `<protocol_framework name="...">` | `<meta>`, `<axiom_core>`, `<authority_matrix>`, `<compliance_testing>`, `<cache_control />` |
| `roles/` | `<agent_construct name="...">` | `<meta>`, `<imports>`, `<profile_core>`, `<capability_matrix>`, `<interaction_bus>`, `<cache_control />` |
| `rules/` | `<governance_logic name="...">` | `<meta>`, `<enforcement_block name="...">` (1+), `<recovery_protocol>`, `<audit_requirements>`, `<cache_control />` |
| `shards/` (model) | `<shard_engine name="...">` | `<meta>`, `<model_configuration>`, `<reasoning_matrix>`, `<cache_control />` |
| `shards/shards_architecture.md` | `<system_map name="...">` | `<meta>`, `<topology>`, `<agent_roster>`, `<cache_control />` |
| `resources/` | `<artifact_template name="...">` | `<meta>`, `<instantiation_config>`, `<content_body>`, `<variable_dictionary>`, `<lifecycle_policy>`, `<cache_control />` |
| `skills/` SKILL.md | `<skill_manifest name="...">` | `<meta>`, `<interface_definition>`, `<execution_logic>`, `<safety_bounds>`, `<cache_control />` |

##### 2.2 Canonical `<meta>` Fields (all domains, strict order)

```xml
<meta>
  <id>          — string, matches filename without extension
  <description> — string, starts with "USE WHEN" for roles/skills, descriptive for others
  <globs>       — array (may be empty)
  <alwaysApply> — boolean
  <tags>        — array, first element MUST be "type:<domain>"
  <priority>    — enum: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
  <version>     — semver string e.g. "1.0.0"
</meta>
```

NO other fields permitted in `<meta>`.

**Domain tag values:** `type:protocol` | `type:role` | `type:rule` | `type:shard` | `type:resource` | `type:skill`

##### 2.3 Deep Child Tag Reference — Roles

| Container | Required Children (exact, in order) |
|:----------|:------------------------------------|
| `<profile_core>` | `<prime_directive>`, `<cognitive_style>`, `<failure_mode>` |
| `<capability_matrix>` | `<skill_registry>`, `<memory_access>`, `<supervision_override>` |
| `<supervision_override>` | `<workflow_constraints>` and/or `<artifact_reference>` only — no raw markdown |
| `<interaction_bus>` | `<upstream_link>`, `<downstream_link>`, `<telemetry_hooks>` |

**§9.1 title rules:**
- MANAGER: `##### 9.1 TRANSPARENCY LOCK (Law 1)`
- All other roles: `##### 9.1 AGENT EXECUTION TRANSPARENCY (Law 1) — ABSOLUTE FIRST ACTION`

##### 2.4 Deep Child Tag Reference — Rules

| Container | Required Children |
|:----------|:------------------|
| `<enforcement_block>` | `<trigger_event>`, `<condition_logic>`, `<consequence_action>`, `<bypass_condition>` |
| `<recovery_protocol>` | `<remediation_steps>` |
| `<audit_requirements>` | `<log_level>`, `<retention_policy>` |

##### 2.5 Deep Child Tag Reference — Shards

| Container | Required Children (in order) |
|:----------|:-----------------------------|
| `<model_configuration>` | `<target_family>`, `<inference_parameters>`, `<context_strategy>` |
| `<inference_parameters>` | `<temperature>`, `<seed>` |
| `<reasoning_matrix>` | `<chain_of_thought>`, `<token_budget>`, `<latency_slo>` [+ `<grounding_config>` Gemini only] |
| `<topology>` | `<directory_tree>`, `<filesystem_zones>` |
| `<agent_roster>` | `<supervisor_layer>`, `<workflow_graph>`, `<skill_registry>` |

---

#### 3. Audit Procedure (10 Steps — Execute Sequentially)

> **TOOL CONSTRAINT:** Use `Read` and `Glob` only. No `Grep`, `Bash`, `Edit`, or `Write`.
> **SERIAL EXECUTION:** One file read per turn. Do not batch.

##### 3.1 Step 1 — Inventory Check

1. Read `.agent/shards/shards_architecture.md`.
2. Extract the canonical file list from `<directory_tree>`.
3. Use `Glob` to find all `.md` files on disk under `.agent/`.
4. **Report:** any file listed in `<directory_tree>` but missing on disk; any `.md` file on disk not listed in `<directory_tree>`.

##### 3.2 Step 2 — Root Tag Audit

For each structured `.md` file (protocols, roles, rules, shards, resources, SKILL.md in skills):

- First non-blank line MUST be the correct opening root tag for its domain (see §2.1).
- Last non-blank line MUST be the matching closing root tag.
- The `name` attribute in the root tag MUST match the filename without extension.

**Report:** any mismatch.

##### 3.3 Step 3 — Meta Block Audit

For each file:

- `<meta>` MUST be the first child of the root tag.
- All 7 canonical fields MUST be present, in the exact order shown in §2.2, with no extras.
- `<id>` value MUST match filename without extension.
- `<tags>` first element MUST be `"type:<correct_domain>"`.
- `<priority>` MUST be one of the four valid enum values.

**Report:** missing fields | extra fields | wrong order | value violations.

##### 3.4 Step 4 — Domain Schema Audit

For each file, verify required child tags exist in canonical order (see §2.1):

- protocols/ `<axiom_core>`, `<authority_matrix>`, `<compliance_testing>`
- roles/ `<imports>`, `<profile_core>`, `<capability_matrix>`, `<interaction_bus>`
- rules/ 1+ `<enforcement_block>`, `<recovery_protocol>`, `<audit_requirements>`
- shards/ model `<model_configuration>`, `<reasoning_matrix>`
- shards_architecture `<topology>`, `<agent_roster>`
- resources/ `<instantiation_config>`, `<content_body>`, `<variable_dictionary>`, `<lifecycle_policy>`
- skills/ SKILL.md `<interface_definition>`, `<execution_logic>`, `<safety_bounds>`

**Report:** missing tags | wrong order | unexpected tags.

##### 3.5 Step 5 — Role Deep Audit

For each file in `roles/`:

- Verify `<profile_core>`, `<capability_matrix>`, `<interaction_bus>` children per §2.3.
- `<supervision_override>` MUST contain ONLY `<workflow_constraints>` and/or `<artifact_reference>` as XML children. Raw markdown directly inside `<supervision_override>` (without these wrappers) is a violation.
- Verify §9.1 title matches the canonical string for this agent type (§2.3).

**Report:** missing | extra | misnamed child tags | wrong §9.1 title | unwrapped markdown in `<supervision_override>`.

##### 3.6 Step 6 — Rule Deep Audit

For each file in `rules/`:

- Every `<enforcement_block>` contains all 4 children (§2.4).
- `<recovery_protocol>` contains `<remediation_steps>`.
- `<audit_requirements>` contains `<log_level>` and `<retention_policy>`.

**Report:** missing child tags.

##### 3.7 Step 7 — Shard Deep Audit

For model shards (NOT `shards_architecture`):

- Verify `<model_configuration>`, `<inference_parameters>`, `<reasoning_matrix>` children per §2.5.
- Gemini files only: `<grounding_config>` MUST be present after `<latency_slo>`.

For `shards_architecture`:

- Verify `<topology>` and `<agent_roster>` children per §2.5.

**Report:** missing | extra | wrong-order tags.

##### 3.8 Step 8 — Section Numbering Audit

For each file, extract all markdown section headings with numbers (e.g., `#### 1.`, `##### 1.1`). Verify the numeric sequence is strictly ascending (1, 2, 3…) top-to-bottom with no gaps.

**Special rule for `protocols_database.md`:** §1–§6 MUST be in `<axiom_core>`, §7 in `<authority_matrix>`, §8 in `<compliance_testing>`.

**Report:** any gap, duplicate, or out-of-order section number.

##### 3.9 Step 9 — `<cache_control />` Audit

For each structured file:

- `<cache_control />` MUST be present as a self-closing tag on its own line.
- It MUST be the last element before the root closing tag.

**Report:** missing or misplaced `<cache_control />`.

##### 3.10 Step 10 — Forbidden Patterns

For each file, scan for:

- `<tools>` tag inside `<meta>` (forbidden — belongs in `<skill_registry>`).
- Placeholder text: `TODO`, `TBD`, `[Desc]` outside of `resources/` template files.
- Any emoji in tag names, section headings, or non-UI content.

**Report:** every instance with `file:line` reference.

---

#### 4. Report Format (Emit Exactly)

```
# SYSTEM INTEGRITY AUDIT REPORT
**Date:** [ISO8601]
**Files Audited:** [N]
**Violations Found:** [N]
**Status:** PASS | FAIL

## Summary Table
| Check | Files Checked | Violations |
|:------|:-------------|:-----------|
| Step 1 — Inventory       | N | N |
| Step 2 — Root Tags       | N | N |
| Step 3 — Meta Block      | N | N |
| Step 4 — Domain Schema   | N | N |
| Step 5 — Role Deep Audit | N | N |
| Step 6 — Rule Deep Audit | N | N |
| Step 7 — Shard Deep Audit| N | N |
| Step 8 — Section Numbers | N | N |
| Step 9 — cache_control   | N | N |
| Step 10 — Forbidden      | N | N |

## Violations (if any)
For each violation:
> **[STEP N — CHECK NAME]** `file_path:line_number`
> **Found:** [what was found]
> **Expected:** [what was expected]
> **Severity:** CRITICAL | HIGH | MEDIUM | LOW

## Clean Files
[List all files with zero violations]

---
[if violations == 0]: ALL CHECKS PASSED. System integrity confirmed.
[if violations > 0]:  INTEGRITY VIOLATIONS DETECTED. Resolve before next session.
```

</execution_logic>

<safety_bounds>

#### 5. Execution Constraints

| Constraint | Rule |
|:-----------|:-----|
| **Read-Only** | This skill NEVER writes, edits, or deletes any file. |
| **Tool Allow-List** | `Read`, `Glob` only. `Grep`, `Bash`, `Edit`, `Write` are BLOCKED. |
| **Serial Reads** | Files MUST be read one at a time. No parallel batching. |
| **No Inference** | All checks are deterministic against the §2 schema reference. No probabilistic judgment. |
| **Scope Lock** | Audit scope is `.agent/` only. Do not traverse workspace source trees. |
| **Remediation** | This skill reports violations only. Fixes are delegated to ENGINEER after PROTOCOL signs off the report. |

</safety_bounds>

<cache_control />

</skill_manifest>
