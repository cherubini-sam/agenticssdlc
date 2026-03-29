<skill_manifest name="skills_database_migration">

<meta>
  <id>"skills_database_migration"</id>
  <description>"Skill for safe database schema migrations"</description>
  <globs>["**/migrations/**", "**/models/**", "**/*schema*"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "database", "migration", "schema"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Plan and execute safe database schema changes
**Triggers:** "migrate schema", "database change", "add column", "alter table", "migration"

</io_contract>
<state_mode>Stateful (Database Schema Change)</state_mode>
<dependencies>

- `scripts/visualize.sh` (Graph Visualization)
- `resources/migration_patterns.sql` (SQL Snippets)

</dependencies>
<env_vars>N/A (Database credentials usually handled via system environment)</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. Safe Migration Patterns

Refer to `resources/migration_patterns.sql` for standardized SQL snippets.

### Large Table Strategies

- **Batch Updates:** Use the batched approach to avoid table locks (documented in skill pseudo-code).
- **Online Tools:** Leverage `pg_repack`, `pt-online-schema-change`, or `gh-ost`.

## 2. Visualization Command

Use `scripts/visualize.sh` to generate a standard colorized git graph.

```bash
bash scripts/visualize.sh [count]
```

</operational_steps>
<error_protocol>

- Test migration on a copy of production data first.
- Measure migration time on production-sized datasets.
- Verify data integrity after every migration step.

</error_protocol>
<side_effect_protocol>
<idempotency_key>N/A</idempotency_key>
<rollback_logic>Every migration must have a `down()` function (documented in skill pseudo-code) for immediate reversal if regression is detected.</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

### Risk Assessment Matrix

- **Drop Column:** High Risk (Code-first removal, wait for rollback window).
- **Rename Column:** High Risk (3-phase: add new, dual-write, drop old).
- **Add NOT NULL Column:** Medium Risk (Add nullable first, backfill, then constrain).

</permissions>
<rate_limit>

- Tested on staging environment before any production run.
- Rollback plan must be documented for every change.
- Downtime estimation is required for any blocking change.

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
