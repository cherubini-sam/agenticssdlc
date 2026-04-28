"""Centralized constants for all agents: names, prompts, thresholds, and log templates."""

from __future__ import annotations

import json
import re
from typing import Literal


def agents_utils_extract_json(raw: str, pattern: str) -> dict | None:
    """Extract the first JSON object matching pattern from raw LLM output."""

    try:
        match: re.Match[str] | None = re.search(pattern, raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    return None


# Agent Names

AGENTS_ARCHITECT_AGENT_NAME: str = "ARCHITECT"
AGENTS_ENGINEER_AGENT_NAME: str = "ENGINEER"
AGENTS_MANAGER_AGENT_NAME: str = "MANAGER"
AGENTS_LIBRARIAN_AGENT_NAME: str = "LIBRARIAN"
AGENTS_REFLECTOR_AGENT_NAME: str = "REFLECTOR"
AGENTS_VALIDATOR_AGENT_NAME: str = "VALIDATOR"
AGENTS_PROTOCOL_AGENT_NAME: str = "PROTOCOL"

# Base LLM retry config

AGENTS_BASE_DEFAULT_MAX_RETRIES: int = 2
AGENTS_BASE_BACKOFF_BASE: int = 2
AGENTS_BASE_JITTER_MIN: float = 0.0
AGENTS_BASE_JITTER_MAX: float = 1.0
AGENTS_BASE_RATE_LIMIT_ERROR: str = (
    "Gemini API quota exhausted for {agent}. " "Daily limit (250 RPD) reached — try again tomorrow."
)
AGENTS_BASE_LOG_QUOTA_EXHAUSTED: str = (
    "[{agent}] Gemini quota exhausted after {retries} retries: {error}"
)
AGENTS_BASE_LLM_TIMEOUT_SECONDS: int = 120
AGENTS_BASE_LOGGER_PREFIX: str = "agents."

AGENTS_BASE_LOG_TIMEOUT: str = "[{agent}] LLM call timed out after {timeout}s (attempt {attempt})"
AGENTS_BASE_LOG_RETRY_429: str = (
    "[{agent}] 429 rate limit (attempt {attempt}). Retrying in {wait}s..."
)
AGENTS_BASE_LOG_LLM_FAIL: str = "[{agent}] LLM call failed: {error}"

AGENTS_BASE_ERR_TIMEOUT: str = "[{agent}] LLM call timed out after {total_attempts} attempts"
AGENTS_BASE_ERR_RETRY_EXIT: str = "Unexpected retry loop exit"

# Doc loader

AGENTS_DOC_LOADER_BASE_PATH: str = ".agent"
AGENTS_DOC_LOADER_CACHE_MAX_SIZE: int = 32

# Static doc bundles (relative to .agent/) — loaded at agent init via the doc loader.
# Every agent baselines on its own role doc plus protocols_core_laws; the bundle
# inflates from there with the governance the agent applies on every call.

AGENTS_BASE_ROLE_DOC_SEPARATOR: str = "\n\n---\n## GOVERNANCE REFERENCE\n"
AGENTS_BASE_DOC_BUNDLE_SEPARATOR: str = "\n\n---\n\n"

AGENTS_PROTOCOL_DOC_PATHS: list[str] = [
    "static/roles/roles_protocol.md",
    "static/protocols/protocols_core_laws.md",
    "static/protocols/protocols_workflow.md",
]
AGENTS_MANAGER_DOC_PATHS: list[str] = [
    "static/roles/roles_manager.md",
    "static/protocols/protocols_core_laws.md",
    "static/protocols/protocols_workflow.md",
]
AGENTS_LIBRARIAN_DOC_PATHS: list[str] = [
    "static/roles/roles_librarian.md",
    "static/protocols/protocols_core_laws.md",
]
AGENTS_ARCHITECT_DOC_PATHS: list[str] = [
    "static/roles/roles_architect.md",
    "static/protocols/protocols_core_laws.md",
    "static/protocols/protocols_quality_standards.md",
    "static/rules/rules_style.md",
    "static/rules/rules_stack.md",
]
AGENTS_REFLECTOR_DOC_PATHS: list[str] = [
    "static/roles/roles_reflector.md",
    "static/protocols/protocols_core_laws.md",
    "static/protocols/protocols_quality_standards.md",
]
AGENTS_ENGINEER_DOC_PATHS: list[str] = [
    "static/roles/roles_engineer.md",
    "static/protocols/protocols_core_laws.md",
    "static/rules/rules_style.md",
    "static/rules/rules_stack.md",
]
AGENTS_VALIDATOR_DOC_PATHS: list[str] = [
    "static/roles/roles_validator.md",
    "static/protocols/protocols_core_laws.md",
    "static/protocols/protocols_quality_standards.md",
]

# Manager Phases (Phase 0 = MANAGER internal, Phase 1 = PROTOCOL gateway, Phase 2–6 = pipeline)
AGENTS_MANAGER_PHASE_0: int = 1
AGENTS_MANAGER_PHASE_1: int = 0
AGENTS_MANAGER_PHASE_2: int = 2
AGENTS_MANAGER_PHASE_3: int = 3
AGENTS_MANAGER_PHASE_4: int = 4
AGENTS_MANAGER_PHASE_5: int = 5
AGENTS_MANAGER_PHASE_6: int = 6

# Manager thresholds and limits

AGENTS_MANAGER_CONFIDENCE_THRESHOLD: float = 0.85
AGENTS_MANAGER_MAX_RETRIES: int = 3
AGENTS_MANAGER_WORKFLOW_TIMEOUT_SECONDS: int = 300
# 6 phases + up to 3 retries * 5 nodes per retry + routing overhead
AGENTS_MANAGER_GRAPH_RECURSION_LIMIT: int = 50
AGENTS_MANAGER_STREAM_VERSION: str = "v2"
AGENTS_MANAGER_PHASE_MIN: int = 1
AGENTS_MANAGER_PHASE_MAX: int = 6

# Manager graph node names

AGENTS_MANAGER_NODE_PROTOCOL: str = "protocol"
AGENTS_MANAGER_NODE_TASK: str = "task"
AGENTS_MANAGER_NODE_LIBRARIAN: str = "librarian"
AGENTS_MANAGER_NODE_ARCHITECT: str = "architect"
AGENTS_MANAGER_NODE_REVIEW: str = "review"
AGENTS_MANAGER_NODE_EXECUTE: str = "execute"
AGENTS_MANAGER_NODE_VERIFY: str = "verify"
AGENTS_MANAGER_NODE_RETRY: str = "retry_increment"
AGENTS_MANAGER_NODE_END_FAILED: str = "end_failed"
AGENTS_MANAGER_NODE_END_SUCCESS: str = "end_success"

AGENTS_MANAGER_TELEMETRY_ROUTER: str = "MANAGER"
AGENTS_MANAGER_VALIDATOR_THRESHOLD_DEFAULT: float = 0.70

# Manager phase descriptions (used in log messages)

AGENTS_MANAGER_DESC_PHASE_0: str = "PROTOCOL boot validation"
AGENTS_MANAGER_DESC_PHASE_1: str = "orchestration"
AGENTS_MANAGER_DESC_PHASE_2: str = "retrieving context"
AGENTS_MANAGER_DESC_PHASE_3: str = "drafting plan"
AGENTS_MANAGER_DESC_PHASE_4: str = "auditing plan"
AGENTS_MANAGER_DESC_PHASE_5: str = "executing"
AGENTS_MANAGER_DESC_PHASE_6: str = "verifying"

AGENTS_MANAGER_VERBOSITY_DEFAULT: str = "standard"
AGENTS_MANAGER_SCORE_FALLBACK: str = "n/a"
AGENTS_MANAGER_SEVERITY_FALLBACK: str = "LOW"

# Error keyword fragments for error-code classification

AGENTS_MANAGER_ERR_KEYWORD_QUOTA: str = "quota"
AGENTS_MANAGER_ERR_KEYWORD_RESOURCE_EXHAUSTED: str = "ResourceExhausted"
AGENTS_MANAGER_ERR_KEYWORD_VECTOR: str = "vector"
AGENTS_MANAGER_ERR_KEYWORD_QDRANT: str = "qdrant"
AGENTS_MANAGER_ERR_KEYWORD_CHROMA: str = "chroma"
AGENTS_MANAGER_STATUS_FAILED: Literal["failed"] = "failed"
AGENTS_MANAGER_STATUS_COMPLETED: Literal["completed"] = "completed"

# Manager log templates

AGENTS_MANAGER_LOG_PHASE_START: str = "[MANAGER] Phase {phase} — {description}, task_id: {task_id}"
AGENTS_MANAGER_LOG_PHASE_GENERIC: str = "[MANAGER] Phase {phase} — {description}"
AGENTS_MANAGER_LOG_TASK_CONTENT: str = "[MANAGER] Task: {content}"
AGENTS_MANAGER_LOG_RETRIEVE_REUSE: str = "[MANAGER] Retry — reusing cached context"
AGENTS_MANAGER_LOG_RETRIEVE_DONE: str = "[MANAGER] Retrieved {count} context doc(s)"
AGENTS_MANAGER_LOG_DRAFT_RETRY: str = "[MANAGER] Using REFLECTOR refined_plan for retry"
AGENTS_MANAGER_LOG_DRAFT_START: str = "[MANAGER] ARCHITECT drafting plan…"
AGENTS_MANAGER_LOG_DRAFT_DONE: str = "[MANAGER] Plan drafted ({count} chars)"
AGENTS_MANAGER_LOG_CRITIQUE_START: str = "[MANAGER] REFLECTOR auditing plan…"
AGENTS_MANAGER_LOG_CRITIQUE_DONE: str = (
    "[MANAGER] REFLECTOR — confidence: {confidence:.2f} | severity: {severity}"
)
AGENTS_MANAGER_LOG_CRITIQUE_ERRORS: str = "[MANAGER] Errors: {errors}"
AGENTS_MANAGER_LOG_EXECUTE_START: str = "[MANAGER] ENGINEER executing…"
AGENTS_MANAGER_LOG_EXECUTE_DONE: str = "[MANAGER] Result ready ({count} chars): {preview}…"
AGENTS_MANAGER_LOG_VERIFY_START: str = "[MANAGER] VALIDATOR running QA…"
AGENTS_MANAGER_LOG_VERIFY_DONE: str = "[MANAGER] VALIDATOR — score: {score}"
AGENTS_MANAGER_LOG_WORKFLOW_FAILED: str = "Workflow failed for task {task_id}: {error}"
AGENTS_MANAGER_LOG_FORCE_EXECUTE: str = (
    "[MANAGER] Retries exhausted ({retries}/{max_retries}). "
    "Forcing execution with best available plan (confidence: {confidence:.2f})."
)
AGENTS_MANAGER_LOG_FORCE_ACCEPT: str = (
    "[MANAGER] Verification retries exhausted ({retries}/{max_retries}). "
    "Accepting result as-is for user delivery."
)

# Manager error messages

AGENTS_MANAGER_ERROR_PROTOCOL_BOOT: str = (
    "SESSION INVALID — PROTOCOL boot failed. Violations: {violations}"
)
AGENTS_MANAGER_ERROR_VALIDATION_FAILED: str = "Validation failed: {issues}"
AGENTS_MANAGER_ERR_TIMEOUT: str = "Workflow exceeded {timeout}s timeout"
AGENTS_MANAGER_ERROR_EXECUTION_REFUSED: str = (
    "Execution refused by {agent}: required protocol sections absent from context "
    "({missing}). The workflow was halted before VALIDATOR to avoid a contradictory "
    "completed-with-refusal response."
)
AGENTS_MANAGER_LOG_EXECUTION_REFUSED: str = (
    "[MANAGER] {agent} refused: missing sections {missing}. Short-circuiting to END_FAILED."
)
AGENTS_REFUSAL_STATUS_PREFIX: str = "status: context_missing"

AGENTS_MANAGER_EVENT_ON_CHAIN_ERROR: str = "on_chain_error"

# Architect verbosity and templates

AGENTS_ARCHITECT_VERBOSITY_CONCISE: str = (
    " Be concise: use short bullet points, minimal prose, and aim for brevity."
)
AGENTS_ARCHITECT_VERBOSITY_STANDARD: str = ""
AGENTS_ARCHITECT_VERBOSITY_DETAILED: str = (
    " Be thorough: include comprehensive explanations, edge cases, rationale, " "and examples."
)
AGENTS_ARCHITECT_VERBOSITY_SUFFIX: dict[str, str] = {
    "concise": AGENTS_ARCHITECT_VERBOSITY_CONCISE,
    "standard": AGENTS_ARCHITECT_VERBOSITY_STANDARD,
    "detailed": AGENTS_ARCHITECT_VERBOSITY_DETAILED,
}
AGENTS_ARCHITECT_HUMAN_TEMPLATE: str = "Task: {task}\n\nContext:\n{context}"
AGENTS_ARCHITECT_SYSTEM_PROMPT: str = (
    "Produce a structured implementation plan from the task and available context. "
    "Cover risks, edge cases, and success criteria per step. "
    "Prefer a best-effort plan with the context you have — the deterministic context-"
    "assembly layer refuses upstream when a section is truly missing, so plan, do not "
    "police. Never fabricate having 'consumed' or 'verified' named sections absent from "
    "your input — omit dependent steps or flag them in a 'Risk' bullet. Emit "
    "'status: context_missing' only when no coherent plan is possible without the "
    "missing sections (rare)."
)
AGENTS_ARCHITECT_REQUIRED_SECTIONS: list[str] = [
    "INTEGRATION & BENCHMARK AUTHORITY",
    "FEEDBACK LOOP",
]
AGENTS_ARCHITECT_CONTEXT_MISSING_STATUS: str = "context_missing"
AGENTS_ARCHITECT_CONTEXT_MISSING_TEMPLATE: str = (
    "status: {status}\nmissing_sections: {missing}\n"
    "The ARCHITECT refused to draft a plan because the required protocol sections "
    "above were not present in the context. Supply them and retry."
)
AGENTS_ARCHITECT_LOG_CONTEXT_MISSING: str = (
    "[ARCHITECT] Refusing to draft: missing required context sections {missing}"
)
AGENTS_ENGINEER_CONTEXT_TRUNCATION: int = 4000
AGENTS_ENGINEER_VERBOSITY_CONCISE: str = (
    " Be concise: provide essential code and key notes only, minimal prose."
)
AGENTS_ENGINEER_VERBOSITY_DETAILED: str = (
    " Be thorough: include full implementations, inline comments, "
    "edge-case handling, and explanations."
)
AGENTS_ENGINEER_VERBOSITY_SUFFIX: dict[str, str] = {
    "concise": AGENTS_ENGINEER_VERBOSITY_CONCISE,
    "standard": "",
    "detailed": AGENTS_ENGINEER_VERBOSITY_DETAILED,
}
AGENTS_ENGINEER_HUMAN_TEMPLATE: str = "Plan:\n{plan}\n\nContext:\n{context}"
AGENTS_ENGINEER_SYSTEM_PROMPT: str = (
    "Implement the plan with concrete, production-ready outputs. The upstream context-"
    "assembly layer runs a deterministic refusal guard before you — when invoked you "
    "may assume context is sufficient. Never simulate or fabricate command output, "
    "logs, or query plans — provide only real code, commands, and explanations. "
    "Code must be syntactically complete and executable (balanced braces, closed "
    "strings, no trailing ellipsis, no 'TODO' placeholders). For a named operation "
    "(Parquet/CSV export, S3 upload, API call), include the concrete library call "
    "that performs it. If a step cannot complete without missing input, document the "
    "gap in 'Notes' and proceed with the rest. Reserve 'status: context_missing' for "
    "the rare case where the plan cannot execute at all without a specific absent "
    "section."
)
AGENTS_ENGINEER_CONTEXT_MISSING_STATUS: str = "context_missing"
AGENTS_ENGINEER_CONTEXT_MISSING_TEMPLATE: str = (
    "status: {status}\nmissing_sections: {missing}\n"
    "The ENGINEER refused to execute because the plan depends on the sections above "
    "but the runtime context does not contain them. Supply the missing sections and "
    "retry — do not let the model fabricate having gathered them."
)
AGENTS_ENGINEER_LOG_CONTEXT_MISSING: str = (
    "[ENGINEER] Refusing to execute: plan references {missing} but context does not"
)
# Protocol-section markers the system treats as fail-closed when referenced by a plan.
AGENTS_KNOWN_PROTOCOL_SECTIONS: list[str] = [
    "INTEGRATION & BENCHMARK AUTHORITY",
    "FEEDBACK LOOP",
]

# Validator

AGENTS_VALIDATOR_PLAN_TRUNCATION: int = 2000
AGENTS_VALIDATOR_RESULT_TRUNCATION: int = 3000
AGENTS_VALIDATOR_FALLBACK_SCORE: float = 0.85
AGENTS_VALIDATOR_DEFAULT_SCORE: float = 0.80
AGENTS_VALIDATOR_SYSTEM_PROMPT: str = (
    "Default stance: PASS. Reserve FAILED for blank, off-topic, or critically broken "
    "output. Partial implementations, minor omissions, and stylistic imperfections are "
    "NOT grounds for a low score.\n"
    "Plan-contingency check (MANDATORY): if the result claims to have consumed named "
    "sections (e.g. 'INTEGRATION & BENCHMARK AUTHORITY', 'FEEDBACK LOOP', or any "
    "section the plan marks 'contingent on the availability of'), verify those strings "
    "appear literally in the inputs you were given. If not, emit a "
    "'plan_contingency_violation' issue per missing section and set verdict to 'failed'.\n"
    "Generated-code completeness check (MANDATORY): for source code in the result, "
    "verify syntactic completeness — balanced parens/brackets/braces, closed strings "
    "and f-strings, no trailing ellipsis. For a named export (Parquet, CSV, JSON, "
    "upload), verify the concrete library call is present (e.g. `df.to_parquet(`, "
    "`df.to_csv(`). If a required call is absent or a string/paren is unclosed, set "
    "verdict to 'failed' and emit an 'incomplete_implementation' issue with the exact "
    "gap.\n"
    "Respond ONLY in JSON: "
    '{"verdict": "passed" or "failed", "score": 0.0-1.0, '
    '"issues": ["issue1", ...], "error": null}'
)
AGENTS_VALIDATOR_ISSUE_PLAN_CONTINGENCY_VIOLATION: str = "plan_contingency_violation"
AGENTS_VALIDATOR_ISSUE_INCOMPLETE_IMPLEMENTATION: str = "incomplete_implementation"
AGENTS_VALIDATOR_VERDICT_PASSED: str = "passed"
AGENTS_VALIDATOR_VERDICT_FAILED: str = "failed"
AGENTS_VALIDATOR_LOG_PARSE_FAILED: str = (
    "[VALIDATOR] JSON parse failed: {error}. Using safe default."
)
AGENTS_VALIDATOR_HUMAN_TEMPLATE: str = "Task: {task}\n\nPlan:\n{plan}\n\nResult:\n{result}"

# Protocol

AGENTS_PROTOCOL_MAX_CONTENT_LENGTH: int = 4096
AGENTS_PROTOCOL_STATUS_GREEN: str = "system_green"
AGENTS_PROTOCOL_STATUS_ERROR: str = "system_error"
AGENTS_PROTOCOL_BOOT_PHASE: int = 0
AGENTS_PROTOCOL_EXECUTION_MODE: str = "readonly"
AGENTS_PROTOCOL_CONTEXT_SCOPE: str = "narrow"
AGENTS_PROTOCOL_THINKING_LEVEL: str = "NONE"

AGENTS_PROTOCOL_VIOLATION_EMPTY_TASK: str = "VIOLATION:BOOT — task_id is empty or missing."
AGENTS_PROTOCOL_VIOLATION_EMPTY_CONTENT: str = "VIOLATION:BOOT — content is empty or missing."
AGENTS_PROTOCOL_VIOLATION_EXCEEDS_LENGTH: str = (
    "VIOLATION:BOOT — content exceeds {limit}-character bound (got {actual})."
)
AGENTS_PROTOCOL_LOG_BOOT_START: str = "[PROTOCOL] Phase 1 — task_id: {task_id}"
AGENTS_PROTOCOL_LOG_BOOT_PASSED: str = "[PROTOCOL] Boot integrity PASSED — status: {status}"
AGENTS_PROTOCOL_LOG_BOOT_FAILED: str = "[PROTOCOL] Boot integrity FAILED. Violations: {violations}"

# Protocol LLM Configuration
AGENTS_PROTOCOL_LLM_TEMPERATURE: float = 0.0
AGENTS_PROTOCOL_LLM_MAX_OUTPUT_TOKENS: int = 1024
AGENTS_PROTOCOL_LLM_MAX_RETRIES: int = 5

# Protocol Gatekeeper Modes (for observability labels)
AGENTS_PROTOCOL_GATEKEEPER_MODE_LLM: str = "tuned_model"
AGENTS_PROTOCOL_GATEKEEPER_MODE_HEURISTIC: str = "legacy_heuristic"
AGENTS_PROTOCOL_GATEKEEPER_MODE_FAIL_CLOSED: str = "fail_closed"

# Protocol Decision Values (from ProtocolDecision schema — "GREEN"/"ERROR")
AGENTS_PROTOCOL_DECISION_GREEN: str = "GREEN"
AGENTS_PROTOCOL_DECISION_ERROR: str = "ERROR"

# Protocol LLM Log Messages
AGENTS_PROTOCOL_LOG_LLM_INVOKE: str = "[PROTOCOL] Invoking tuned gatekeeper for task_id={task_id}"
AGENTS_PROTOCOL_LOG_LLM_RESULT: str = "[PROTOCOL] Tuned model decision: {status} (mode={mode})"
AGENTS_PROTOCOL_LOG_FALLBACK_TRIGGERED: str = "[PROTOCOL] Fallback triggered ({mode}): {error}"
AGENTS_PROTOCOL_LOG_FAIL_CLOSED: str = "[PROTOCOL] Fail-closed triggered — returning ERROR"
AGENTS_PROTOCOL_LOG_NO_ENDPOINT: str = (
    "[PROTOCOL] No tuned endpoint configured — using legacy heuristic"
)
AGENTS_PROTOCOL_FAIL_CLOSED_VIOLATION: str = "VIOLATION:PROTOCOL — LLM gatekeeper unavailable"

AGENTS_PROTOCOL_SECTION_PREAMBLE: str = (
    "## INTEGRATION & BENCHMARK AUTHORITY\n"
    "\n"
    "Integration contracts and benchmark acceptance criteria for ARCHITECT/ENGINEER reference.\n"
    "\n"
    "## FEEDBACK LOOP\n"
    "\n"
    "Validator-to-architect refinement channel; REFLECTOR critique and VALIDATOR verdict "
    "propagate to the next retry via ``critique.refined_plan``.\n"
)

# Reflector

AGENTS_REFLECTOR_CONTEXT_TRUNCATION: int = 2000
AGENTS_REFLECTOR_DEFAULT_CONFIDENCE: float = 0.7
AGENTS_REFLECTOR_SEVERITY_CRITICAL: str = "CRITICAL"
AGENTS_REFLECTOR_SEVERITY_MEDIUM: str = "MEDIUM"
AGENTS_REFLECTOR_JSON_PATTERN: str = r"\{.*\}"
AGENTS_REFLECTOR_SKIP_LABEL: str = "SKIP"
AGENTS_REFLECTOR_FAST_PATH_KNOWLEDGE: str = "Optimal plan detected. Skipping refinement pass."
AGENTS_REFLECTOR_FAST_CONFIDENCE_THRESHOLD: float = 0.9
AGENTS_REFLECTOR_HUMAN_TEMPLATE: str = (
    "Perform a FAST assessment of this plan. If it's perfect (confidence >= {threshold}), "
    "set 'refined_plan' to '{skip_label}' to save time.\n\n"
    "Task: {task}\n\nContext: {context}\n\nPlan:\n{plan}"
)

# Shares the same JSON extraction regex as Reflector
AGENTS_VALIDATOR_JSON_PATTERN: str = AGENTS_REFLECTOR_JSON_PATTERN

# Librarian

AGENTS_LIBRARIAN_DEFAULT_K: int = 4
AGENTS_LIBRARIAN_QUERY_LOG_TRUNCATION: int = 50

# Trace action labels (used in agent_trace messages)

AGENTS_TRACE_ACTION_BOOT_VALIDATION: str = "boot_validation"
AGENTS_TRACE_ACTION_TASK_CONFIRMED: str = "task_confirmed"
AGENTS_TRACE_ACTION_PLAN_DRAFTED: str = "plan_drafted"
AGENTS_TRACE_ACTION_PLAN_CRITIQUED: str = "plan_critiqued"
AGENTS_TRACE_ACTION_EXECUTION_COMPLETE: str = "execution_complete"
AGENTS_TRACE_ACTION_EXECUTION_REFUSED: str = "execution_refused"
AGENTS_TRACE_ACTION_PLAN_REFUSED: str = "plan_refused"
AGENTS_LIBRARIAN_ACTION_RETRIEVED: str = "context_retrieved"
AGENTS_LIBRARIAN_LOG_RETRIEVED: str = "[LIBRARIAN] Retrieved {count} docs for query: '{query}'"
AGENTS_LIBRARIAN_SYSTEM_PROMPT: str = (
    "Synthesize the retrieved context documents below into a concise, coherent context "
    "for downstream agents. Focus on relevant patterns, applicable rules, and "
    "constraints. Return only the synthesized context as plain text."
)
AGENTS_MANAGER_TASK_SYSTEM_PROMPT: str = (
    "Classify the incoming task and confirm it is ready for pipeline processing. "
    "Return a single JSON object: "
    '{"classification": "<type>", "preview": "<one-sentence summary>", "confidence": <0.0-1.0>}'
)

# Reflector system prompt

AGENTS_REFLECTOR_SYSTEM_PROMPT: str = (
    "Evaluate the plan as JUDGE (find errors), CRITIC (suggest fixes), "
    "REFINER (rewrite the plan), and CURATOR (extract reusable insight).\n"
    "Default stance: APPROVE — a plan does not need to be perfect to be actionable. "
    "Only lower confidence below 0.85 when a GENUINE structural flaw would cause the "
    "ENGINEER to produce broken output. Stylistic preferences, missing edge-case notes, "
    "or minor omissions are NOT grounds for a low score.\n"
    "Respond ONLY with a single JSON object (no markdown fences):\n"
    "{\n"
    '  "errors": ["..."],\n'
    '  "severity": "CRITICAL|HIGH|MEDIUM|LOW|NONE",\n'
    '  "suggestions": ["fix1", ...],\n'
    '  "confidence": 0.0-1.0,\n'
    '  "refined_plan": "full improved plan text",\n'
    '  "improvements": ["change1", ...],\n'
    '  "reuse_pattern": "template text",\n'
    '  "knowledge_atom": "one-sentence lesson"\n'
    "}\n"
    "confidence = technical completeness score (0.0-1.0)\n"
    "Use 0.9-1.0 when the plan is technically sound; use 0.85-0.9 for minor concerns. "
    "Reserve <0.85 only for genuine structural flaws that will break execution."
)
