"""Turns a task description and RAG context into a structured implementation plan."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.agents_base import AgentsBase
from src.agents.agents_utils import (
    AGENTS_ARCHITECT_AGENT_NAME,
    AGENTS_ARCHITECT_HUMAN_TEMPLATE,
    AGENTS_ARCHITECT_SYSTEM_PROMPT,
    AGENTS_ARCHITECT_VERBOSITY_SUFFIX,
    AGENTS_MANAGER_VERBOSITY_DEFAULT,
)


class AgentsArchitect(AgentsBase):
    """Produces numbered implementation plans with steps, success criteria, and risks."""

    agent_name: str = AGENTS_ARCHITECT_AGENT_NAME

    async def agents_architect_draft_plan(
        self, task: str, context: str, verbosity: str = AGENTS_MANAGER_VERBOSITY_DEFAULT
    ) -> str:
        """Draft a markdown plan grounded in RAG context.
        Verbosity tweaks the system prompt suffix.
        """

        system = AGENTS_ARCHITECT_SYSTEM_PROMPT + AGENTS_ARCHITECT_VERBOSITY_SUFFIX.get(
            verbosity, ""
        )
        human = AGENTS_ARCHITECT_HUMAN_TEMPLATE.format(task=task, context=context)

        return await self._agents_base_call_llm(
            [
                SystemMessage(content=system),
                HumanMessage(content=human),
            ]
        )
