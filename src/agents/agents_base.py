"""Shared base class for all agents, handling LLM calls with exponential backoff on rate limits."""

import asyncio
import logging
import random

from google.api_core.exceptions import ResourceExhausted
from langchain_core.messages import BaseMessage

from src.agents.agents_utils import (
    AGENTS_BASE_BACKOFF_BASE,
    AGENTS_BASE_DEFAULT_MAX_RETRIES,
    AGENTS_BASE_ERR_RETRY_EXIT,
    AGENTS_BASE_ERR_TIMEOUT,
    AGENTS_BASE_JITTER_MAX,
    AGENTS_BASE_JITTER_MIN,
    AGENTS_BASE_LLM_TIMEOUT_SECONDS,
    AGENTS_BASE_LOG_LLM_FAIL,
    AGENTS_BASE_LOG_QUOTA_EXHAUSTED,
    AGENTS_BASE_LOG_RETRY_429,
    AGENTS_BASE_LOG_TIMEOUT,
    AGENTS_BASE_LOGGER_PREFIX,
    AGENTS_BASE_RATE_LIMIT_ERROR,
)
from src.core.core_llm import core_llm_get_llm as get_llm


class AgentsBase:
    """Subclasses set agent_name and get LLM access with built-in retry logic for free."""

    agent_name: str

    def __init__(self) -> None:
        self.llm = get_llm()
        self.logger = logging.getLogger(f"{AGENTS_BASE_LOGGER_PREFIX}{self.agent_name.lower()}")

    @staticmethod
    def _require_context_sections(context: str, required: list[str]) -> list[str]:
        """Return the subset of ``required`` section markers missing from ``context``.

        Fail-closed guard used by agents whose prompts assume specific protocol sections
        (e.g. ``INTEGRATION & BENCHMARK AUTHORITY``, ``FEEDBACK LOOP``) are present. When
        the caller finds the returned list non-empty, it MUST short-circuit instead of
        invoking the LLM — otherwise the model is free to fabricate having consumed the
        missing context.

        Args:
            context: The full context string the agent is about to pass to the LLM.
            required: Literal section markers that MUST be present verbatim.

        Returns:
            List of markers that were NOT found in ``context`` (empty = all present).
        """

        haystack = context or ""
        return [marker for marker in required if marker not in haystack]

    @staticmethod
    def _detect_missing_contingent_sections(
        plan: str, context: str, known_sections: list[str]
    ) -> list[str]:
        """Return the subset of ``known_sections`` that the plan depends on but the context lacks.

        A section is considered "plan-depended" when either (a) the plan contains its literal
        marker, or (b) the plan contains a contingency phrase (``contingent on``, ``requires``,
        ``depends on``, ``assumes``, ``gather from``) near a marker-like reference. The returned
        list is the subset that appears in the plan but NOT literally in the context — i.e. the
        markers a downstream agent would be tempted to hallucinate having consumed.

        Args:
            plan: The approved plan text that the executor is about to act on.
            context: The runtime context string that will actually be passed to the LLM.
            known_sections: Literal section markers the system treats as protocol-critical.

        Returns:
            List of markers that the plan references but the context does not contain.
        """

        plan_text = plan or ""
        ctx_text = context or ""
        return [
            marker for marker in known_sections if marker in plan_text and marker not in ctx_text
        ]

    async def _agents_base_call_llm(
        self,
        messages: list[BaseMessage],
        max_retries: int = AGENTS_BASE_DEFAULT_MAX_RETRIES,
        timeout: int | None = None,
    ) -> str:
        """Invoke the LLM with exponential backoff on 429s and a hard timeout per attempt.

        Args:
            messages: List of LangChain BaseMessage objects forming the prompt conversation.
            max_retries: Max number of retry attempts on 429/timeout before giving up.
            timeout: Per-attempt timeout in seconds. None uses a 300 s default.

        Returns:
            LLM response content as a plain string.

        Raises:
            RuntimeError: If the timeout is exceeded after all retries.
            RuntimeError: If the quota is exhausted after all retries.
        """

        _timeout = timeout or 300
        for attempt in range(max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.llm.ainvoke(messages),
                    timeout=_timeout,
                )
                return response.content
            except asyncio.TimeoutError:
                self.logger.error(
                    AGENTS_BASE_LOG_TIMEOUT.format(
                        agent=self.agent_name,
                        timeout=AGENTS_BASE_LLM_TIMEOUT_SECONDS,
                        attempt=attempt + 1,
                    )
                )
                if attempt == max_retries:
                    raise RuntimeError(
                        AGENTS_BASE_ERR_TIMEOUT.format(
                            agent=self.agent_name, total_attempts=max_retries + 1
                        )
                    )
                continue
            except ResourceExhausted as e:
                if attempt == max_retries:
                    self.logger.error(
                        AGENTS_BASE_LOG_QUOTA_EXHAUSTED.format(
                            agent=self.agent_name, retries=max_retries, error=e
                        )
                    )
                    raise RuntimeError(
                        AGENTS_BASE_RATE_LIMIT_ERROR.format(agent=self.agent_name)
                    ) from e

                # Jitter prevents thundering herd when multiple agents hit the quota wall
                wait = (AGENTS_BASE_BACKOFF_BASE**attempt) + random.uniform(
                    AGENTS_BASE_JITTER_MIN, AGENTS_BASE_JITTER_MAX
                )
                self.logger.warning(
                    AGENTS_BASE_LOG_RETRY_429.format(
                        agent=self.agent_name, attempt=attempt + 1, wait=wait
                    )
                )
                await asyncio.sleep(wait)
            except Exception as e:
                self.logger.error(
                    AGENTS_BASE_LOG_LLM_FAIL.format(agent=self.agent_name, error=e), exc_info=True
                )
                raise
        raise RuntimeError(AGENTS_BASE_ERR_RETRY_EXIT)
