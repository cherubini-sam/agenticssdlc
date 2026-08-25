"""QA pass that scores execution results against the original task and plan."""

from __future__ import annotations

import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.agents_base import AgentsBase
from src.agents.agents_reflector import agents_reflector_extract_json
from src.agents.agents_utils import (
    AGENTS_MANAGER_VALIDATOR_THRESHOLD_DEFAULT,
    AGENTS_REFUSAL_STATUS_PREFIX,
    AGENTS_UTILS_CLOSING_HASH_WHITESPACE_CHARS,
    AGENTS_UTILS_FENCE_PATTERN,
    AGENTS_VALIDATOR_AGENT_NAME,
    AGENTS_VALIDATOR_DEFAULT_SCORE,
    AGENTS_VALIDATOR_DOC_PATHS,
    AGENTS_VALIDATOR_EMPTY_SECTION_SCORE,
    AGENTS_VALIDATOR_FALLBACK_SCORE,
    AGENTS_VALIDATOR_HUMAN_TEMPLATE,
    AGENTS_VALIDATOR_ISSUE_EMPTY_SECTION,
    AGENTS_VALIDATOR_ISSUE_UNPARSEABLE_OUTPUT,
    AGENTS_VALIDATOR_JSON_PATTERN,
    AGENTS_VALIDATOR_LOG_PARSE_FAILED,
    AGENTS_VALIDATOR_PLAN_TRUNCATION,
    AGENTS_VALIDATOR_RESULT_TRUNCATION,
    AGENTS_VALIDATOR_SYSTEM_PROMPT,
    AGENTS_VALIDATOR_VERDICT_PASSED,
)

AGENTS_VALIDATOR_VERDICT_FAILED: str = "failed"
AGENTS_VALIDATOR_ISSUE_EXECUTION_REFUSED: str = "execution_refused"
AGENTS_VALIDATOR_REFUSAL_SCORE: float = 0.0

logger = logging.getLogger(__name__)


def agents_validator_strip_closing_hash_sequence(text: str) -> str:
    """Strip a trailing ``[ \\t]+#+[ \\t]*`` closing-hash run from heading text.

    Equivalent in behavior to ``re.sub(r"[ \\t]+#+[ \\t]*$", "", text)`` but
    implemented as a bounded, single-pass scan from the end of the string so
    it cannot exhibit catastrophic regex backtracking regardless of input
    size or shape.

    Args:
        text: Heading text extracted from an ATX heading line.

    Returns:
        ``text`` with any trailing closing-hash sequence removed, unchanged
        otherwise.
    """

    end = len(text)
    ws_boundary = end
    while ws_boundary > 0 and text[ws_boundary - 1] in AGENTS_UTILS_CLOSING_HASH_WHITESPACE_CHARS:
        ws_boundary -= 1

    hash_boundary = ws_boundary
    while hash_boundary > 0 and text[hash_boundary - 1] == "#":
        hash_boundary -= 1

    if hash_boundary == ws_boundary:
        return text

    lead_ws_boundary = hash_boundary
    while (
        lead_ws_boundary > 0
        and text[lead_ws_boundary - 1] in AGENTS_UTILS_CLOSING_HASH_WHITESPACE_CHARS
    ):
        lead_ws_boundary -= 1

    if lead_ws_boundary == hash_boundary:
        return text

    return text[:lead_ws_boundary]


def agents_validator_find_empty_sections(markdown: str) -> list[str]:
    """Return the heading texts whose body holds zero non-whitespace characters.

    A section body spans from the end of its ATX heading line to the start of
    the next heading of any level, or to EOF. A heading immediately followed
    by a deeper heading is a container and is NOT considered empty. Fenced
    code spans (both backtick and tilde, per CommonMark same-character /
    at-least-opening-length close semantics, with an unclosed fence running
    to EOF) are skipped entirely, so a hash-prefixed line inside a fence is
    never mistaken for a heading. Only ATX headings (``^ {0,3}#{1,6}\\s``) are
    recognized; Setext headings are deliberately out of scope.

    Args:
        markdown: Full artifact text, untruncated.

    Returns:
        Heading texts (leading hashes, surrounding whitespace, and any
        trailing closing-hash run stripped), in document order. An empty
        list means every heading has a non-empty body, or no heading exists.
    """

    if not markdown:
        return []

    lines = markdown.split("\n")

    # Pass 1: classify each line as "in-fence" (never a heading candidate) by
    # tracking fenced code spans per CommonMark open/close rules.
    in_fence = [False] * len(lines)
    fence_char: str | None = None
    fence_len = 0
    inside = False
    for i, line in enumerate(lines):
        if inside:
            in_fence[i] = True
            close_match = re.match(r"^ {0,3}(`+|~+)\s*$", line)
            if (
                close_match
                and close_match.group(1)[0] == fence_char
                and len(close_match.group(1)) >= fence_len
            ):
                inside = False
                fence_char = None
                fence_len = 0
            continue
        open_match = re.match(AGENTS_UTILS_FENCE_PATTERN, line)
        if open_match:
            in_fence[i] = True
            run = open_match.group(1)
            fence_char = run[0]
            fence_len = len(run)
            inside = True

    # Pass 2: locate ATX headings outside fenced spans.
    heading_re = re.compile(r"^ {0,3}(#{1,6})\s+(.*)$")
    headings: list[tuple[int, int, str]] = []  # (line_index, level, text)
    for i, line in enumerate(lines):
        if in_fence[i]:
            continue
        match = heading_re.match(line)
        if not match:
            continue
        level = len(match.group(1))
        text = match.group(2).strip()
        text = agents_validator_strip_closing_hash_sequence(text).strip()
        headings.append((i, level, text))

    if not headings:
        return []

    empty: list[str] = []
    for idx, (line_index, level, text) in enumerate(headings):
        next_line = headings[idx + 1][0] if idx + 1 < len(headings) else len(lines)
        next_level = headings[idx + 1][1] if idx + 1 < len(headings) else None
        body_lines = lines[line_index + 1 : next_line]
        body = "\n".join(body_lines)
        if next_level is not None and next_level > level and not body.strip():
            continue
        if not body.strip():
            empty.append(text)

    return empty


class AgentsValidator(AgentsBase):
    """Scores the engineer's output. Default stance is PASS; only hard-fails on critical issues."""

    agent_name: str = AGENTS_VALIDATOR_AGENT_NAME
    role_doc_paths: list[str] = AGENTS_VALIDATOR_DOC_PATHS

    async def agents_validator_verify(self, result: str, plan: str, task: str) -> dict:
        """Compare result against plan and task to produce a QA verdict.

        A deterministic pre-LLM short-circuit runs first: if ``result`` begins with
        the canonical refusal preamble ``status: context_missing``, the LLM call is
        skipped and the verdict is forced to ``failed`` with score 0.0. This
        prevents the default-PASS rubric from rubber-stamping fail-closed refusals
        as valid output — the exact failure mode that produced the UI's
        ``completed + passed 1.00`` contradiction on refused executions.

        Args:
            result: Engineer execution output to evaluate.
            plan: Approved plan used to derive scoring criteria.
            task: Original user task string that defines the acceptance bar.

        Returns:
            Dict with keys: verdict (str), score (float 0–1), issues (list),
            error (str or None).
        """
        if result and result.lstrip().startswith(AGENTS_REFUSAL_STATUS_PREFIX):
            return {
                "verdict": AGENTS_VALIDATOR_VERDICT_FAILED,
                "score": AGENTS_VALIDATOR_REFUSAL_SCORE,
                "issues": [AGENTS_VALIDATOR_ISSUE_EXECUTION_REFUSED],
                "error": None,
            }

        empty_sections = agents_validator_find_empty_sections(result)
        if empty_sections:
            # score (not verdict) is what routes at agents_manager.py — a
            # verdict-only failure is a silent no-op, so the score below the
            # validator threshold is what forces the retry/reject path.
            return {
                "verdict": AGENTS_VALIDATOR_VERDICT_FAILED,
                "score": AGENTS_VALIDATOR_EMPTY_SECTION_SCORE,
                "issues": [
                    f"{AGENTS_VALIDATOR_ISSUE_EMPTY_SECTION}: {section}"
                    for section in empty_sections
                ],
                "error": None,
            }

        system = self._agents_base_build_system_prompt(
            AGENTS_VALIDATOR_SYSTEM_PROMPT,
            score_threshold=str(AGENTS_MANAGER_VALIDATOR_THRESHOLD_DEFAULT),
        )
        human = AGENTS_VALIDATOR_HUMAN_TEMPLATE.format(
            task=task,
            plan=plan[:AGENTS_VALIDATOR_PLAN_TRUNCATION],
            result=result[:AGENTS_VALIDATOR_RESULT_TRUNCATION],
        )

        raw = await self._agents_base_call_llm(
            [
                SystemMessage(content=system),
                HumanMessage(content=human),
            ]
        )

        verdict = agents_reflector_extract_json(raw, AGENTS_VALIDATOR_JSON_PATTERN)
        if verdict is not None:
            try:
                return {
                    "verdict": verdict.get("verdict", AGENTS_VALIDATOR_VERDICT_PASSED),
                    "score": float(verdict.get("score", AGENTS_VALIDATOR_FALLBACK_SCORE)),
                    "issues": verdict.get("issues", []),
                    "error": verdict.get("error"),
                }
            except (ValueError, TypeError) as e:
                logger.warning(AGENTS_VALIDATOR_LOG_PARSE_FAILED.format(error=e))

        # Fail closed: an unparseable verdict is not evidence of a passing result.
        return {
            "verdict": AGENTS_VALIDATOR_VERDICT_FAILED,
            "score": AGENTS_VALIDATOR_DEFAULT_SCORE,
            "issues": [AGENTS_VALIDATOR_ISSUE_UNPARSEABLE_OUTPUT],
            "error": None,
        }
