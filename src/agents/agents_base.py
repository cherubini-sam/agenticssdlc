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

    async def _agents_base_call_llm(
        self,
        messages: list[BaseMessage],
        max_retries: int = AGENTS_BASE_DEFAULT_MAX_RETRIES,
        timeout: int | None = None,
    ) -> str:
        """Invoke the LLM with exponential backoff on 429s and a hard timeout per attempt."""

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
