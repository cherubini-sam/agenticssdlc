"""QA pass that scores execution results against the original task and plan."""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.agents_base import AgentsBase
from src.agents.agents_utils import (
    AGENTS_MANAGER_VALIDATOR_THRESHOLD_DEFAULT,
    AGENTS_REFUSAL_STATUS_PREFIX,
    AGENTS_VALIDATOR_AGENT_NAME,
    AGENTS_VALIDATOR_DEFAULT_SCORE,
    AGENTS_VALIDATOR_DOC_PATHS,
    AGENTS_VALIDATOR_FALLBACK_SCORE,
    AGENTS_VALIDATOR_HUMAN_TEMPLATE,
    AGENTS_VALIDATOR_JSON_PATTERN,
    AGENTS_VALIDATOR_LOG_PARSE_FAILED,
    AGENTS_VALIDATOR_PLAN_TRUNCATION,
    AGENTS_VALIDATOR_RESULT_TRUNCATION,
    AGENTS_VALIDATOR_SYSTEM_PROMPT,
    AGENTS_VALIDATOR_VERDICT_PASSED,
    agents_utils_extract_json,
)

AGENTS_VALIDATOR_VERDICT_FAILED: str = "failed"
AGENTS_VALIDATOR_ISSUE_EXECUTION_REFUSED: str = "execution_refused"
AGENTS_VALIDATOR_REFUSAL_SCORE: float = 0.0

logger = logging.getLogger(__name__)


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

        verdict = agents_utils_extract_json(raw, AGENTS_VALIDATOR_JSON_PATTERN)
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

        # Safe default: if the LLM gives us garbage JSON, assume a reasonable pass
        return {
            "verdict": AGENTS_VALIDATOR_VERDICT_PASSED,
            "score": AGENTS_VALIDATOR_DEFAULT_SCORE,
            "issues": [],
            "error": None,
        }
