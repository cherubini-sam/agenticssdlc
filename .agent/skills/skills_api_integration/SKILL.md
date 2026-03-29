<skill_manifest name="skills_api_integration">

<meta>
  <id>"skills_api_integration"</id>
  <description>"Skill for integrating external APIs and services"</description>
  <globs>["**/*api*", "**/*client*", "**/*service*"]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:skill", "api", "integration", "external-services"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<interface_definition>
<io_contract>

**Purpose:** Connect and integrate external APIs safely and efficiently
**Triggers:** "integrate API", "connect service", "API client", "external service"

</io_contract>
<state_mode>Stateful (External Integration)</state_mode>
<dependencies>

- `scripts/api_client.py` (Standard Request Handler)
- `scripts/rate_limit.py` (Throttling)

</dependencies>
<env_vars>

- `API_KEY` (Required for authentication)
- secrets management (AWS Secrets Manager, HashiCorp Vault)

</env_vars>
</interface_definition>
<execution_logic>
<operational_steps>

## 1. Integration Checklist

- [ ] API documentation reviewed
- [ ] Authentication method identified (API key, OAuth, JWT, etc.)
- [ ] Rate limits documented
- [ ] Error responses mapped
- [ ] Retry strategy defined
- [ ] Timeout values set
- [ ] Request/response schemas validated

## 2. Client Pattern

Use `api_client.py` in the `scripts/` directory for standard request handling with built-in retry logic and exponential backoff.

</operational_steps>

<error_protocol>

- Map error responses according to API documentation.
- Use standard retry strategy with exponential backoff.
- Test error handling (4xx, 5xx responses).

</error_protocol>
<side_effect_protocol>
<idempotency_key>N/A (API Specific)</idempotency_key>
<rollback_logic>N/A (External State)</rollback_logic>
</side_effect_protocol>
</execution_logic>
<safety_bounds>
<permissions>

## 3. Security Rules

- **NEVER** hardcode API keys in source code
- Use environment variables: `os.getenv("API_KEY")`
- Validate all external input before sending
- Sanitize all responses before using
- Log requests (redact sensitive data)

</permissions>
<rate_limit>

Use the `rate_limit` decorator in `scripts/rate_limit.py` to enforce caller-side throttling.

</rate_limit>
</safety_bounds>

<cache_control />

</skill_manifest>
