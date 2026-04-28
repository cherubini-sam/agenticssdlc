"""Turns a task description and RAG context into a structured implementation plan."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.agents_base import AgentsBase
from src.agents.agents_utils import (
    AGENTS_ARCHITECT_AGENT_NAME,
    AGENTS_ARCHITECT_CONTEXT_MISSING_STATUS,
    AGENTS_ARCHITECT_CONTEXT_MISSING_TEMPLATE,
    AGENTS_ARCHITECT_DOC_PATHS,
    AGENTS_ARCHITECT_HUMAN_TEMPLATE,
    AGENTS_ARCHITECT_LOG_CONTEXT_MISSING,
    AGENTS_ARCHITECT_SYSTEM_PROMPT,
    AGENTS_ARCHITECT_VERBOSITY_SUFFIX,
    AGENTS_MANAGER_VERBOSITY_DEFAULT,
)


class AgentsArchitect(AgentsBase):
    """Produces numbered implementation plans with steps, success criteria, and risks."""

    agent_name: str = AGENTS_ARCHITECT_AGENT_NAME
    role_doc_paths: list[str] = AGENTS_ARCHITECT_DOC_PATHS

    async def agents_architect_draft_plan(
        self,
        task: str,
        context: str,
        verbosity: str = AGENTS_MANAGER_VERBOSITY_DEFAULT,
        required_sections: list[str] | None = None,
    ) -> str:
        """Draft a markdown plan grounded in RAG context.

        Args:
            task: Raw task description from the user.
            context: RAG-retrieved context injected into the prompt.
            verbosity: Controls system prompt verbosity suffix (concise/standard/detailed).
            required_sections: Protocol section markers that MUST be present in ``context``
                before the LLM is invoked. Defaults to ``[]`` (no guard). Callers that need
                the fail-closed guard pass ``AGENTS_ARCHITECT_REQUIRED_SECTIONS`` explicitly
                so existing flows keep working.

        Returns:
            Markdown implementation plan, or a ``status: context_missing`` refusal string
            when required sections are absent from ``context``.
        """

        required = required_sections if required_sections is not None else []
        missing = self._require_context_sections(context, required)
        if missing:
            self.logger.warning(AGENTS_ARCHITECT_LOG_CONTEXT_MISSING.format(missing=missing))
            return AGENTS_ARCHITECT_CONTEXT_MISSING_TEMPLATE.format(
                status=AGENTS_ARCHITECT_CONTEXT_MISSING_STATUS,
                missing=", ".join(missing),
            )

        system = self._agents_base_build_system_prompt(
            AGENTS_ARCHITECT_SYSTEM_PROMPT + AGENTS_ARCHITECT_VERBOSITY_SUFFIX.get(verbosity, "")
        )
        human = AGENTS_ARCHITECT_HUMAN_TEMPLATE.format(task=task, context=context)

        return await self._agents_base_call_llm(
            [
                SystemMessage(content=system),
                HumanMessage(content=human),
            ]
        )
