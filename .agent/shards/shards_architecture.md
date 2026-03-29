<system_map name="shards_architecture">

<meta>
  <id>"shards_architecture"</id>
  <description>"SYSTEM ARCHITECTURE - The Directory Map & Agent Roster."</description>
  <globs>[]</globs>
  <alwaysApply>true</alwaysApply>
  <tags>["type:shard", "core", "map", "architecture"]</tags>
  <priority>"HIGH"</priority>
  <version>"1.0.0"</version>
</meta>

<topology>
<directory_tree>

#### 1. File System Truth

```text
  .agent/
  ├── artifacts/              # [RUNTIME] Artifact sandbox — auto-created, gitignored, excluded from ingestion
  ├── config/
  │   └── settings.json       # [SSOT] Master Settings File
  ├── protocols/              # [SHARED] Behavioral Standards & Manuals (technology-agnostic)
  │   ├── protocols_anti_patterns.md
  │   ├── protocols_cli.md
  │   ├── protocols_communication.md
  │   ├── protocols_core_laws.md
  │   ├── protocols_evaluation.md
  │   ├── protocols_mode_matrix.md
  │   ├── protocols_observability.md
  │   ├── protocols_phase_gate.md
  │   ├── protocols_quality.md
  │   ├── protocols_references.md
  │   ├── protocols_timing.md
  │   └── protocols_tools.md
  ├── resources/              # [TEMPLATES] Blueprint markdown files
  │   ├── resources_implementation_plan.md
  │   └── resources_task_template.md
  ├── roles/                  # [PERSONAS] Agent Definitions
  │   ├── roles_architect.md
  │   ├── roles_engineer.md
  │   ├── roles_librarian.md
  │   ├── roles_manager.md
  │   ├── roles_protocol.md
  │   ├── roles_reflector.md
  │   └── roles_validator.md
  ├── rules/                  # [POLICIES] Global Behavioral Guidelines
  │   ├── rules_boundaries.md
  │   ├── rules_stack.md
  │   ├── rules_style.md
  │   └── rules_workflow_manager.md
  ├── shards/                 # [SPEC] Model Technical Specifications
  │   ├── shards_architecture.md
  │   ├── shards_claude_haiku_4.md
  │   ├── shards_claude_opus_4.md
  │   ├── shards_claude_sonnet_4.md
  │   ├── shards_gemini_3_flash.md
  │   ├── shards_gemini_3_pro.md
  │   ├── shards_gemini_ultra.md
  │   └── shards_generic_llm.md
  └── skills/                 # [CAPABILITIES] Task-Specific Logic & Scripts (tech-specific implementations)
      ├── index.json          # [REGISTRY] Skill discovery index (SSOT)
      └── skills_<name>/      # SKILL.md + scripts/ + resources/ (×15+)
```

</directory_tree>
<filesystem_zones>

#### 1.1 Zone Access Matrix

| Zone | Path | Access |
| :--- | :--- | :----- |
| Artifact Sandbox | `.agent/artifacts/` | R/W — task.md, plans, reports |
| Workspace | `./` | R/W — code, configs, tests |
| Protocols | `.agent/protocols/` | READ ONLY |
| Forbidden | `/`, `.git` | BLOCK |

</filesystem_zones>
</topology>

<agent_roster>
<supervisor_layer>

#### 2. Agent Roster (Supervisor-Worker Pattern)

**Supervisors (Reasoning Layer):**

- **MANAGER:** Routing, Intent, Orchestration. (Active)
- **ARCHITECT:** Strategy, Design, Schemas. (Lazy)
- **REFLECTOR:** Self-Critique, Quality Review. (Lazy)
- **VALIDATOR:** QA Gate, Security Audit, Test Verification. (Lazy)

**Workers (Execution Layer):**

- **ENGINEER:** Code, Ops, Implementation. (Lazy)
- **LIBRARIAN:** Docs, History, Research. (Lazy)

**System (Guardrails):**

- **PROTOCOL:** Law Enforcement & Safety. (Active / Always On)

#### 2.1. Agent Registry (Discovery Pattern)

| Agent     | Layer      | Status | Capabilities                 |
| :-------- | :--------- | :----- | :--------------------------- |
| MANAGER   | Supervisor | Active | route, classify, orchestrate |
| ARCHITECT | Supervisor | Lazy   | design, schema, strategy     |
| REFLECTOR | Supervisor | Lazy   | critique, refine, evaluate   |
| VALIDATOR | Supervisor | Lazy   | qa, security, audit, verify  |
| ENGINEER  | Worker     | Lazy   | code, debug, test, execute   |
| LIBRARIAN | Worker     | Lazy   | docs, research, summarize    |
| PROTOCOL  | System     | Active | enforce, validate, guard     |

</supervisor_layer>
<workflow_graph>

#### 2.2. Workflow Graph (State Transitions)

STANDARD: See .agent/rules/rules_workflow_manager.md (Strict 6-Phase Cycle).
**Workflow Sequence:** Phase 1 (Task) -> Phase 2 (Context) -> Phase 3 (Plan) -> Phase 4 (Critique) -> Phase 5 (Execute) -> Phase 6 (Verify).

</workflow_graph>
<skill_registry>

#### 3. Skill Registry (Progressive Disclosure)

See `.agent/skills/` for definitions. Loaded dynamically by MANAGER via Routing JSON.

</skill_registry>
</agent_roster>

<cache_control />

</system_map>
