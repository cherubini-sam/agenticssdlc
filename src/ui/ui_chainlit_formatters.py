"""Turns agent state deltas into formatted Markdown for the Chainlit UI."""

from __future__ import annotations

from src.agents.agents_utils import AGENTS_PROTOCOL_STATUS_GREEN
from src.ui.ui_chainlit_utils import (
    UI_CHAINLIT_UTILS_BADGE_FAIL,
    UI_CHAINLIT_UTILS_BADGE_HIGH,
    UI_CHAINLIT_UTILS_BADGE_HIGH_THRESHOLD,
    UI_CHAINLIT_UTILS_BADGE_LOW,
    UI_CHAINLIT_UTILS_BADGE_LOW_THRESHOLD,
    UI_CHAINLIT_UTILS_BADGE_PASS,
    UI_CHAINLIT_UTILS_BADGE_PASS_THRESHOLD,
    UI_CHAINLIT_UTILS_MSG_ARCHITECT_NO_PLAN,
    UI_CHAINLIT_UTILS_MSG_ARCHITECT_PLAN,
    UI_CHAINLIT_UTILS_MSG_DISPATCH_NO_OUTPUT,
    UI_CHAINLIT_UTILS_MSG_DISPATCH_RETRY,
    UI_CHAINLIT_UTILS_MSG_DISPATCH_TASK_CONFIRMED,
    UI_CHAINLIT_UTILS_MSG_LIBRARIAN_RETRIEVED,
    UI_CHAINLIT_UTILS_MSG_PROTOCOL_ERROR,
    UI_CHAINLIT_UTILS_MSG_PROTOCOL_GREEN,
    UI_CHAINLIT_UTILS_MSG_PROTOCOL_VIOLATION_UNKNOWN,
    UI_CHAINLIT_UTILS_MSG_REFLECTOR_CONFIDENCE_SEVERITY,
    UI_CHAINLIT_UTILS_MSG_REFLECTOR_CRITIC_SUGGESTIONS,
    UI_CHAINLIT_UTILS_MSG_REFLECTOR_CRITIQUE_HEADER,
    UI_CHAINLIT_UTILS_MSG_REFLECTOR_CURATOR_PATTERN,
    UI_CHAINLIT_UTILS_MSG_REFLECTOR_GATE_APPROVED,
    UI_CHAINLIT_UTILS_MSG_REFLECTOR_GATE_REJECTED,
    UI_CHAINLIT_UTILS_MSG_REFLECTOR_JUDGE_ISSUES,
    UI_CHAINLIT_UTILS_MSG_REFLECTOR_PATTERN_WRAP,
    UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_APPROVED,
    UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_CONFIDENCE,
    UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_DOCS,
    UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_SCORE,
    UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_STATUS,
    UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_VERDICT,
    UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_VIOLATIONS,
    UI_CHAINLIT_UTILS_MSG_TRACE_EMPTY,
    UI_CHAINLIT_UTILS_MSG_TRACE_HEADER,
    UI_CHAINLIT_UTILS_MSG_TRACE_TABLE_DIVIDER,
    UI_CHAINLIT_UTILS_MSG_TRACE_TABLE_HEAD,
    UI_CHAINLIT_UTILS_MSG_TRUNCATE_OVERFLOW,
    UI_CHAINLIT_UTILS_MSG_VALIDATOR_FAIL,
    UI_CHAINLIT_UTILS_MSG_VALIDATOR_PASS,
    UI_CHAINLIT_UTILS_TRUNCATE_DEFAULT,
    UI_CHAINLIT_UTILS_TRUNCATE_RESULT,
)


def ui_chainlit_utils_confidence_badge(confidence: float) -> str:
    """Map a 0-1 confidence score to a tier label (HIGH/PASS/LOW/FAIL)."""

    if confidence >= UI_CHAINLIT_UTILS_BADGE_HIGH_THRESHOLD:
        return UI_CHAINLIT_UTILS_BADGE_HIGH
    if confidence >= UI_CHAINLIT_UTILS_BADGE_PASS_THRESHOLD:
        return UI_CHAINLIT_UTILS_BADGE_PASS
    if confidence >= UI_CHAINLIT_UTILS_BADGE_LOW_THRESHOLD:
        return UI_CHAINLIT_UTILS_BADGE_LOW
    return UI_CHAINLIT_UTILS_BADGE_FAIL


def ui_chainlit_utils_format_protocol_result(output: dict) -> str:
    """Format the Phase 1 (PROTOCOL) boot validation output as Markdown."""

    status: str = output.get("protocol_status", "unknown")
    violations: list = output.get("protocol_violations") or []

    if status == AGENTS_PROTOCOL_STATUS_GREEN:
        return UI_CHAINLIT_UTILS_MSG_PROTOCOL_GREEN

    violation_lines = (
        "\n".join(f"- `{v}`" for v in violations)
        if violations
        else UI_CHAINLIT_UTILS_MSG_PROTOCOL_VIOLATION_UNKNOWN
    )
    return UI_CHAINLIT_UTILS_MSG_PROTOCOL_ERROR.format(violations=violation_lines)


def ui_chainlit_utils_format_librarian_result(output: dict) -> str:
    """Format the Phase 2 (LIBRARIAN) retrieval summary."""

    context: str = output.get("context") or ""
    # Each doc chunk is separated by double newline in the context string
    doc_count = len([c for c in context.split("\n\n") if c.strip()]) if context else 0
    return UI_CHAINLIT_UTILS_MSG_LIBRARIAN_RETRIEVED.format(count=doc_count)


def ui_chainlit_utils_format_plan(output: dict) -> str:
    """Format the Phase 3 (ARCHITECT) plan output."""

    plan: str = output.get("plan") or ""
    if plan:
        return UI_CHAINLIT_UTILS_MSG_ARCHITECT_PLAN.format(plan=plan)
    return UI_CHAINLIT_UTILS_MSG_ARCHITECT_NO_PLAN


def ui_chainlit_utils_format_critique(output: dict) -> str:
    """Format Phase 4 (REFLECTOR): confidence gate, severity, issues,
    suggestions, and curator pattern.
    """

    critique: dict = output.get("critique") or {}
    confidence: float = float(output.get("confidence", 0.0))
    approved_raw = output.get("approved")
    # Fall back to threshold check if the graph didn't set an explicit approval flag
    approved: bool = (
        bool(approved_raw)
        if approved_raw is not None
        else (confidence >= UI_CHAINLIT_UTILS_BADGE_PASS_THRESHOLD)
    )

    badge = ui_chainlit_utils_confidence_badge(confidence)
    gate = (
        UI_CHAINLIT_UTILS_MSG_REFLECTOR_GATE_APPROVED
        if approved
        else UI_CHAINLIT_UTILS_MSG_REFLECTOR_GATE_REJECTED
    )
    severity: str = critique.get("severity", "UNKNOWN")
    errors: list = critique.get("errors") or []
    suggestions: list = critique.get("suggestions") or []
    reuse_pattern: str = critique.get("reuse_pattern") or ""

    lines: list[str] = [
        UI_CHAINLIT_UTILS_MSG_REFLECTOR_CRITIQUE_HEADER.format(gate=gate),
        UI_CHAINLIT_UTILS_MSG_REFLECTOR_CONFIDENCE_SEVERITY.format(
            badge=badge, confidence=confidence, severity=severity
        ),
        "",
    ]

    # Cap at 3 items each to keep the step output scannable
    if errors:
        lines += [UI_CHAINLIT_UTILS_MSG_REFLECTOR_JUDGE_ISSUES]
        for e in errors[:3]:
            lines.append(f"- {e}")
        lines.append("")

    if suggestions:
        lines += [UI_CHAINLIT_UTILS_MSG_REFLECTOR_CRITIC_SUGGESTIONS]
        for s in suggestions[:3]:
            lines.append(f"- {s}")
        lines.append("")

    if reuse_pattern:
        lines += [
            UI_CHAINLIT_UTILS_MSG_REFLECTOR_CURATOR_PATTERN,
            UI_CHAINLIT_UTILS_MSG_REFLECTOR_PATTERN_WRAP.format(pattern=reuse_pattern),
            "",
        ]

    return "\n".join(lines)


def ui_chainlit_utils_format_validator_result(output: dict) -> str:
    """Format Phase 6 (VALIDATOR) pass/fail with confidence badge."""

    confidence: float = float(output.get("confidence", 0.0))
    error: str | None = output.get("error")

    badge = ui_chainlit_utils_confidence_badge(confidence)
    if error:
        return UI_CHAINLIT_UTILS_MSG_VALIDATOR_FAIL.format(
            badge=badge, confidence=confidence, error=error
        )
    return UI_CHAINLIT_UTILS_MSG_VALIDATOR_PASS.format(badge=badge, confidence=confidence)


def ui_chainlit_utils_format_phase_output(
    node_name: str,
    output: dict,
) -> str:
    """Dispatch to the right formatter based on which graph node just finished."""

    if node_name == "protocol":
        return ui_chainlit_utils_format_protocol_result(output)

    if node_name == "task":
        return UI_CHAINLIT_UTILS_MSG_DISPATCH_TASK_CONFIRMED

    if node_name == "librarian":
        return ui_chainlit_utils_format_librarian_result(output)

    if node_name == "architect":
        return ui_chainlit_utils_format_plan(output)

    if node_name == "review":
        return ui_chainlit_utils_format_critique(output)

    if node_name == "execute":
        result: str = output.get("result") or ""
        if not result:
            return UI_CHAINLIT_UTILS_MSG_DISPATCH_NO_OUTPUT
        return ui_chainlit_utils_truncate(result, UI_CHAINLIT_UTILS_TRUNCATE_RESULT)

    if node_name == "verify":
        return ui_chainlit_utils_format_validator_result(output)

    if node_name == "retry_increment":
        retry = output.get("retry_count", "?")
        return UI_CHAINLIT_UTILS_MSG_DISPATCH_RETRY.format(retry=retry)

    return ""


def ui_chainlit_utils_format_agent_trace(messages: list) -> str:
    """Render the accumulated agent trace as a Markdown table for the side panel."""

    if not messages:
        return UI_CHAINLIT_UTILS_MSG_TRACE_EMPTY

    lines = [
        UI_CHAINLIT_UTILS_MSG_TRACE_HEADER,
        "",
        UI_CHAINLIT_UTILS_MSG_TRACE_TABLE_HEAD,
        UI_CHAINLIT_UTILS_MSG_TRACE_TABLE_DIVIDER,
    ]

    for msg in messages:
        phase = msg.get("phase", "--")
        agent = msg.get("agent", "--")
        action = msg.get("action", "--")

        details_parts: list[str] = []
        if "status" in msg:
            details_parts.append(
                UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_STATUS.format(status=msg["status"])
            )
        if "confidence" in msg and msg["confidence"] is not None:
            details_parts.append(
                UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_CONFIDENCE.format(
                    confidence=float(msg["confidence"])
                )
            )
        if "approved" in msg:
            details_parts.append(
                UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_APPROVED.format(approved=msg["approved"])
            )
        if "verdict" in msg:
            details_parts.append(
                UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_VERDICT.format(verdict=msg["verdict"])
            )
        if "score" in msg and msg["score"] is not None:
            details_parts.append(
                UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_SCORE.format(score=float(msg["score"]))
            )
        if "docs_retrieved" in msg:
            details_parts.append(
                UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_DOCS.format(count=msg["docs_retrieved"])
            )
        if msg.get("violations"):
            details_parts.append(
                UI_CHAINLIT_UTILS_MSG_TRACE_DETAIL_VIOLATIONS.format(violations=msg["violations"])
            )

        details = " | ".join(details_parts) if details_parts else "--"
        lines.append(f"| {phase} | **{agent}** | `{action}` | {details} |")

    return "\n".join(lines)


def ui_chainlit_utils_truncate(
    text: str, max_chars: int = UI_CHAINLIT_UTILS_TRUNCATE_DEFAULT
) -> str:
    """Chop text at max_chars and append an overflow indicator if needed."""

    if len(text) <= max_chars:
        return text
    overflow = len(text) - max_chars
    return text[:max_chars] + UI_CHAINLIT_UTILS_MSG_TRUNCATE_OVERFLOW.format(overflow=overflow)
