"""Executes approved plans and produces the final implementation output."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.agents_base import AgentsBase
from src.agents.agents_utils import (
    AGENTS_ENGINEER_AGENT_NAME,
    AGENTS_ENGINEER_CONTEXT_MISSING_STATUS,
    AGENTS_ENGINEER_CONTEXT_MISSING_TEMPLATE,
    AGENTS_ENGINEER_CONTEXT_TRUNCATION,
    AGENTS_ENGINEER_DOC_PATHS,
    AGENTS_ENGINEER_HUMAN_TEMPLATE,
    AGENTS_ENGINEER_LOG_CONTEXT_MISSING,
    AGENTS_ENGINEER_SYSTEM_PROMPT,
    AGENTS_ENGINEER_VERBOSITY_SUFFIX,
    AGENTS_KNOWN_PROTOCOL_SECTIONS,
    AGENTS_MANAGER_VERBOSITY_DEFAULT,
)


class AgentsEngineer(AgentsBase):
    """Implements the architect's plan step-by-step. Only runs on approved plans."""

    agent_name: str = AGENTS_ENGINEER_AGENT_NAME
    role_doc_paths: list[str] = AGENTS_ENGINEER_DOC_PATHS

    async def agents_engineer_execute(
        self,
        plan: str,
        context: str,
        verbosity: str = AGENTS_MANAGER_VERBOSITY_DEFAULT,
        known_sections: list[str] | None = None,
    ) -> str:
        """Execute the plan with RAG context.

        A fail-closed contingency guard runs before the LLM is invoked: if the plan
        references a known protocol-section marker (see ``AGENTS_KNOWN_PROTOCOL_SECTIONS``)
        that is NOT literally present in the runtime context, the executor refuses with a
        ``status: context_missing`` response instead of letting the model fabricate having
        gathered the section. Pass ``known_sections=[]`` to disable.

        Args:
            plan: Approved architect plan detailing the steps to implement.
            context: RAG context truncated to stay within the token budget.
            verbosity: Controls output depth (concise/standard/detailed).
            known_sections: Protocol-section markers the system cares about. ``None``
                uses the project default (``AGENTS_KNOWN_PROTOCOL_SECTIONS``); ``[]``
                disables the guard entirely for callers that want the legacy behaviour.

        Returns:
            Final implementation output as a plain string, or a ``status: context_missing``
            refusal when the plan depends on sections absent from the context.
        """

        sections = AGENTS_KNOWN_PROTOCOL_SECTIONS if known_sections is None else known_sections
        missing = self._detect_missing_contingent_sections(plan, context, sections)
        if missing:
            self.logger.warning(AGENTS_ENGINEER_LOG_CONTEXT_MISSING.format(missing=missing))
            return AGENTS_ENGINEER_CONTEXT_MISSING_TEMPLATE.format(
                status=AGENTS_ENGINEER_CONTEXT_MISSING_STATUS,
                missing=", ".join(missing),
            )

        system = self._agents_base_build_system_prompt(
            AGENTS_ENGINEER_SYSTEM_PROMPT + AGENTS_ENGINEER_VERBOSITY_SUFFIX.get(verbosity, "")
        )
        ctx = (context or "")[:AGENTS_ENGINEER_CONTEXT_TRUNCATION]
        human = AGENTS_ENGINEER_HUMAN_TEMPLATE.format(plan=plan, context=ctx)

        return await self._agents_base_call_llm(
            [
                SystemMessage(content=system),
                HumanMessage(content=human),
            ],
            timeout=300,
        )
