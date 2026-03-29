<skill_manifest name="skills_grounding">

<meta>
  <id>"skills_grounding"</id>
  <description>"Skill for fact verification using web search and grounding"</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "grounding", "search", "verification"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Ground responses in real-time web information and verify facts
**Triggers:** "verify facts", "current status", "latest", "fact check", "is this true"

</io_contract>
<state_mode>Stateless (Fact Verification)</state_mode>
<dependencies>

- Google Search Grounding API
- Web Search Tools (`search_web`, `read_url_content`)

</dependencies>
<env_vars>N/A</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. Grounding Protocol

1. **Query Analysis:** Identify claims and extract fresh search terms.
2. **Search Execution:** Generate 2-3 queries; prioritize official docs, GitHub (>1K stars).
3. **Result Processing:** Cross-reference top 2-3 results; note disagreements.

## 2. Citation Protocol

- Format: `[Title](URL)`
- Validation: NEVER cite unvisited or non-200 URLs.

</operational_steps>
<error_protocol>

If sources disagree, note conflict and recommend which to trust based on reliability hierarchy (Official docs > GitHub > Tech Blogs).

</error_protocol>
<side_effect_protocol>
<idempotency_key>N/A</idempotency_key>
<rollback_logic>N/A</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

- Grounding restricted to public web information.
- Skip grounding for math, logic, or local project-specific questions.

</permissions>
<rate_limit>

- Gemini Grounding Config: `dynamic_retrieval_threshold: 0.5`.
- Cost Awareness: Limit usage based on production quotas ($35/1k queries).

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
