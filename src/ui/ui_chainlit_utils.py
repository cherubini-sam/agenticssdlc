"""Shared constants for the Chainlit UI layer."""

from __future__ import annotations

# Confidence badge thresholds and labels

UI_CHAINLIT_UTILS_BADGE_HIGH_THRESHOLD: float = 0.90
UI_CHAINLIT_UTILS_BADGE_PASS_THRESHOLD: float = 0.85
UI_CHAINLIT_UTILS_BADGE_LOW_THRESHOLD: float = 0.70

UI_CHAINLIT_UTILS_BADGE_HIGH: str = "HIGH"
UI_CHAINLIT_UTILS_BADGE_PASS: str = "PASS"
UI_CHAINLIT_UTILS_BADGE_LOW: str = "LOW"
UI_CHAINLIT_UTILS_BADGE_FAIL: str = "FAIL"

# 15 min; generous because retried workflows can take a while
UI_CHAINLIT_APP_STREAM_TIMEOUT: int = 900

# Defaults for user-tunable ChatSettings sliders
UI_CHAINLIT_APP_DEFAULT_REFLECTOR_THRESHOLD: float = 0.85
UI_CHAINLIT_APP_DEFAULT_VALIDATOR_THRESHOLD: float = 0.70
UI_CHAINLIT_APP_DEFAULT_MAX_RETRIES: int = 3
UI_CHAINLIT_APP_DEFAULT_VERBOSITY: str = "standard"

# Truncation limits (chars)
UI_CHAINLIT_UTILS_TRUNCATE_DEFAULT: int = 500
UI_CHAINLIT_UTILS_TRUNCATE_REUSE_PATTERN: int = 220
UI_CHAINLIT_UTILS_TRUNCATE_ERROR: int = 300
UI_CHAINLIT_UTILS_TRUNCATE_RESULT: int = 2_000

# Streamed into every non-LLM step immediately after __aenter__ so the
# accordion body is never empty. An empty body makes the React expand
# button a no-op; "…" forces it into an expandable state from the first
# render. Replaced by step.output at __aexit__ — never persists to the
# final closed view. LLM steps use their first model token instead.
UI_CHAINLIT_UTILS_STEP_INIT_TOKEN: str = "…"

# Chainlit step type identifier for LLM-streaming steps. Used to gate
# init-token streaming so the "…" prefix is not prepended to model output.
UI_CHAINLIT_UTILS_STEP_TYPE_LLM: str = "llm"

# Phase metadata: node_key -> (phase_number, display_label, step_type, avatar_file)
UI_CHAINLIT_UTILS_PHASE_META: dict[str, tuple[str, str, str, str]] = {
    "protocol": ("1", "PROTOCOL — Boot Validation", "tool", "validator.svg"),
    "task": ("--", "MANAGER — Task Confirmation", "run", "agentics_sdlc.png"),
    "librarian": ("2", "LIBRARIAN — Context Retrieval", "tool", "architect.svg"),
    "architect": ("3", "ARCHITECT — Blueprint Design", "llm", "architect.svg"),
    "review": ("4", "REFLECTOR — Confidence Audit", "llm", "reflector.svg"),
    "execute": ("5", "ENGINEER — Plan Execution", "llm", "engineer.svg"),
    "verify": ("6", "VALIDATOR — Quality Assurance", "tool", "validator.svg"),
    "retry_increment": ("--", "MANAGER — Retry Loop", "run", "agentics_sdlc.png"),
}

UI_CHAINLIT_UTILS_GRAPH_NODES: frozenset[str] = frozenset(UI_CHAINLIT_UTILS_PHASE_META.keys())

# Ordered list for the TaskList sidebar widget
UI_CHAINLIT_UTILS_TASK_PHASES: list[tuple[str, str]] = [
    ("protocol", "Phase 1 — PROTOCOL Boot Validation"),
    ("librarian", "Phase 2 — LIBRARIAN Context Retrieval"),
    ("architect", "Phase 3 — ARCHITECT Blueprint Design"),
    ("review", "Phase 4 — REFLECTOR Confidence Audit"),
    ("execute", "Phase 5 — ENGINEER Plan Execution"),
    ("verify", "Phase 6 — VALIDATOR Quality Assurance"),
]


# Example prompts shown on empty chat
UI_CHAINLIT_UTILS_STARTERS: list[dict[str, str]] = [
    {
        "label": "Database & Query",
        "message": (
            "The orders table has 2M rows. Filtering by customer_id and status is slow. "
            "No indexes exist beyond the primary key. "
            "Identify why a full table scan occurs on this query pattern, "
            "assess the performance impact at scale, and provide the recommended "
            "CREATE INDEX statement with justification for the chosen index type "
            "and column order."
        ),
        "icon": "/public/assets/avatars/architect.svg",
    },
    {
        "label": "Security Audit",
        "message": (
            "This Python snippet concatenates user input directly into a query: "
            "query = 'SELECT * FROM users WHERE id = ' + user_input. "
            "Identify all security flaws present, explain the attack vector for each, "
            "assess the severity level, and provide the hardened parameterized equivalent "
            "with justification for why the fix eliminates the risk."
        ),
        "icon": "/public/assets/avatars/validator.svg",
    },
    {
        "label": "Data Engineering",
        "message": (
            "A JSON file contains records with duplicate id values and inconsistent "
            "updated_at timestamps. Write a Python function that ingests the file, "
            "deduplicates records keeping the latest updated_at, and exports the result "
            "to Parquet, with a summary of edge cases handled and assumptions made."
        ),
        "icon": "/public/assets/avatars/engineer.svg",
    },
    {
        "label": "MLOps & Monitoring",
        "message": (
            "A classification model logs predicted labels to a database daily. "
            "Write a Python function that reads a list of predicted labels, "
            "computes the class distribution as percentages, and flags classes deviating "
            "significantly from an expected reference distribution, with an explanation "
            "of what a skewed prediction distribution indicates in a production environment."
        ),
        "icon": "/public/assets/avatars/reflector.svg",
    },
]

# UI display messages

# Protocol (Phase 1)
UI_CHAINLIT_UTILS_MSG_PROTOCOL_GREEN: str = "**System green** | All boot checks passed."
UI_CHAINLIT_UTILS_MSG_PROTOCOL_ERROR: str = (
    "**System error** | Boot failed.\n\n**Violations:**\n{violations}"
)
UI_CHAINLIT_UTILS_MSG_PROTOCOL_VIOLATION_UNKNOWN: str = "- _Unknown violation_"

# Librarian (Phase 2)
UI_CHAINLIT_UTILS_MSG_LIBRARIAN_RETRIEVED: str = (
    "**{count} document(s) retrieved** from knowledge base"
)

# Architect (Phase 3)
UI_CHAINLIT_UTILS_MSG_ARCHITECT_PLAN: str = "### Implementation Plan\n\n{plan}"
UI_CHAINLIT_UTILS_MSG_ARCHITECT_NO_PLAN: str = "_No plan generated_"

# Reflector (Phase 4)
UI_CHAINLIT_UTILS_MSG_REFLECTOR_GATE_APPROVED: str = "**Approved**"
UI_CHAINLIT_UTILS_MSG_REFLECTOR_GATE_REJECTED: str = "**Rejected**"
UI_CHAINLIT_UTILS_MSG_REFLECTOR_CRITIQUE_HEADER: str = "### {gate}"
UI_CHAINLIT_UTILS_MSG_REFLECTOR_CONFIDENCE_SEVERITY: str = (
    "**Confidence:** `{badge}` `{confidence:.2f}` &nbsp; **Severity:** `{severity}`"
)
UI_CHAINLIT_UTILS_MSG_REFLECTOR_JUDGE_ISSUES: str = "**Judge | Issues found:**"
UI_CHAINLIT_UTILS_MSG_REFLECTOR_CRITIC_SUGGESTIONS: str = "**Critic | Suggestions:**"
UI_CHAINLIT_UTILS_MSG_REFLECTOR_CURATOR_PATTERN: str = "**Curator | Reusable pattern:**"
UI_CHAINLIT_UTILS_MSG_REFLECTOR_PATTERN_WRAP: str = "> {pattern}"

# Validator (Phase 6)
UI_CHAINLIT_UTILS_MSG_VALIDATOR_FAIL: str = (
    "**Validation failed** | Score: `{badge}` `{confidence:.2f}`\n\n```\n{error}\n```"
)
UI_CHAINLIT_UTILS_MSG_VALIDATOR_PASS: str = (
    "**Validation passed** | Score: `{badge}` `{confidence:.2f}`"
)

# Dispatcher (Main loop/Retries)
UI_CHAINLIT_UTILS_MSG_DISPATCH_TASK_CONFIRMED: str = (
    "**Task boundary confirmed** | Pipeline starting."
)
UI_CHAINLIT_UTILS_MSG_DISPATCH_NO_OUTPUT: str = "_No output_"
UI_CHAINLIT_UTILS_MSG_DISPATCH_RETRY: str = "**Retry {retry}** | Looping back to context retrieval."

# Agent Trace Table
UI_CHAINLIT_UTILS_MSG_TRACE_EMPTY: str = "_No agent trace available._"
UI_CHAINLIT_UTILS_MSG_TRACE_HEADER: str = "# Agent Trace"
UI_CHAINLIT_UTILS_MSG_TRACE_TABLE_HEAD: str = "| Phase | Agent | Action | Details |"
UI_CHAINLIT_UTILS_MSG_TRACE_TABLE_DIVIDER: str = "|:---|:---|:---|:---|"
UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_STATUS: str = "status: `{status}`"
UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_CONFIDENCE: str = "conf: `{confidence:.2f}`"
UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_APPROVED: str = "approved: `{approved}`"
UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_VERDICT: str = "verdict: `{verdict}`"
UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_SCORE: str = "score: `{score:.2f}`"
UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_DOCS: str = "docs: `{count}`"
UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_VIOLATIONS: str = "violations: `{violations}`"

# Truncation
UI_CHAINLIT_UTILS_MSG_TRUNCATE_OVERFLOW: str = "... *(+{overflow} chars)*"
