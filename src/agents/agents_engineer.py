"""Executes approved plans and produces the final implementation output."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.agents_base import AgentsBase
from src.agents.agents_utils import (
    AGENTS_ENGINEER_AGENT_NAME,
    AGENTS_ENGINEER_CONTEXT_TRUNCATION,
    AGENTS_ENGINEER_HUMAN_TEMPLATE,
    AGENTS_ENGINEER_SYSTEM_PROMPT,
    AGENTS_ENGINEER_VERBOSITY_SUFFIX,
    AGENTS_MANAGER_VERBOSITY_DEFAULT,
)


class AgentsEngineer(AgentsBase):
    """Implements the architect's plan step-by-step. Only runs on approved plans."""

    agent_name: str = AGENTS_ENGINEER_AGENT_NAME

    async def agents_engineer_execute(
        self, plan: str, context: str, verbosity: str = AGENTS_MANAGER_VERBOSITY_DEFAULT
    ) -> str:
        """Execute the plan with RAG context. Context is truncated to stay within token budget."""

        system = AGENTS_ENGINEER_SYSTEM_PROMPT + AGENTS_ENGINEER_VERBOSITY_SUFFIX.get(verbosity, "")
        ctx = (context or "")[:AGENTS_ENGINEER_CONTEXT_TRUNCATION]
        human = AGENTS_ENGINEER_HUMAN_TEMPLATE.format(plan=plan, context=ctx)

        return await self._agents_base_call_llm(
            [
                SystemMessage(content=system),
                HumanMessage(content=human),
            ],
            timeout=300,
        )
