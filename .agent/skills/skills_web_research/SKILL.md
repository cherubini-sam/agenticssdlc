<skill_manifest name="skills_web_research">

<meta>
  <id>"skills_web_research"</id>
  <description>"Skill for conducting multi-step deep web research"</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "research", "web"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Execute multi-step, iterative deep research on complex topics.
**Triggers:** "research this", "deep dive", "find sources for", "investigate".

</io_contract>
<state_mode>Stateless (Memory-based Synthesis)</state_mode>
<dependencies>

- `scripts/timer.py` (Benchmarking)
- `resources/source_hierarchy.md` (Source Priority)

</dependencies>
<env_vars>N/A</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. The Research Loop

DO NOT rely on a single search.

1. **Deconstruct:** Break query into 3 sub-questions.
2. **Execute:** Run 3 parallel searches.
3. **Synthesize:** Read top 2 results per query.
4. **Refine:** If answer is shallow, re-query with new specific terms.

## 2. Citation Protocol

- **Format:** `[Title](URL)`
- **Constraint:** NEVER cite a URL you haven't visited via `read_url_content`.
- **Validation:** 404s must be removed.

</operational_steps>
<error_protocol>

- **Failover:** If a link returns 403/404, YOU MUST RETRY with alternative queries/sources until valid content is retrieved. Do not stop until you have the data.

</error_protocol>
<side_effect_protocol>
<idempotency_key>N/A</idempotency_key>
<rollback_logic>N/A</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

## 3. Operational Constraints (STRICT)

- **Browser Policy:** DO NOT open external browsers. Use internal tools `search_web` and `read_url_content` ONLY.

</permissions>
<rate_limit>

Benchmarking: Use the `timer` context manager in `scripts/timer.py` to measure execution time of specific code blocks.

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
