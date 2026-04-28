"""Mocked LLM-path tests for Architect, Engineer, Reflector, Validator, Librarian."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.documents import Document


def _make_base_agent(cls, role_doc: str = "") -> object:
    """Instantiate an agent without calling __init__ and wire a mock LLM."""
    agent = cls.__new__(cls)
    agent.llm = AsyncMock()
    agent.agent_name = cls.__name__.upper()
    agent.logger = MagicMock()
    agent._role_doc = role_doc
    return agent


class TestAgentsArchitectDraftPlan:
    """Cover agents_architect.py lines 50-64."""

    @pytest.mark.asyncio
    async def test_draft_plan_happy_path_calls_llm(self) -> None:
        """When required sections are present, the LLM is invoked and its text returned."""
        from agents.agents_architect import AgentsArchitect
        from agents.agents_utils import AGENTS_ARCHITECT_REQUIRED_SECTIONS

        agent = _make_base_agent(AgentsArchitect)
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="## Plan\n1. Do it."))

        ctx = "INTEGRATION & BENCHMARK AUTHORITY ... FEEDBACK LOOP ..."
        result = await agent.agents_architect_draft_plan(
            task="Build a feature",
            context=ctx,
            required_sections=AGENTS_ARCHITECT_REQUIRED_SECTIONS,
        )

        assert "Plan" in result
        agent.llm.ainvoke.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_draft_plan_missing_sections_returns_refusal(self) -> None:
        """When required sections are absent the LLM is skipped and a refusal is returned."""
        from agents.agents_architect import AgentsArchitect
        from agents.agents_utils import AGENTS_ARCHITECT_REQUIRED_SECTIONS

        agent = _make_base_agent(AgentsArchitect)
        agent.llm.ainvoke = AsyncMock()

        result = await agent.agents_architect_draft_plan(
            task="Build feature",
            context="no markers here",
            required_sections=AGENTS_ARCHITECT_REQUIRED_SECTIONS,
        )

        assert "context_missing" in result
        agent.llm.ainvoke.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_draft_plan_no_guard_skips_section_check(self) -> None:
        """Passing required_sections=[] disables the guard entirely."""
        from agents.agents_architect import AgentsArchitect

        agent = _make_base_agent(AgentsArchitect)
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="plan text"))

        result = await agent.agents_architect_draft_plan(
            task="task", context="empty context", required_sections=[]
        )

        assert result == "plan text"

    @pytest.mark.asyncio
    async def test_draft_plan_verbosity_concise(self) -> None:
        """Concise verbosity is accepted without error."""
        from agents.agents_architect import AgentsArchitect

        agent = _make_base_agent(AgentsArchitect)
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="short plan"))

        result = await agent.agents_architect_draft_plan(
            task="t", context="ctx", verbosity="concise", required_sections=[]
        )
        assert result == "short plan"


# ---------------------------------------------------------------------------
# AgentsEngineer
# ---------------------------------------------------------------------------


class TestAgentsEngineerExecute:
    """Cover agents_engineer.py lines 57-78."""

    @pytest.mark.asyncio
    async def test_execute_happy_path_calls_llm(self) -> None:
        """With no missing contingent sections the LLM is invoked."""
        from agents.agents_engineer import AgentsEngineer

        agent = _make_base_agent(AgentsEngineer)
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="def run(): pass"))

        result = await agent.agents_engineer_execute(
            plan="simple plan",
            context="INTEGRATION & BENCHMARK AUTHORITY ... FEEDBACK LOOP ...",
            known_sections=[],  # guard disabled
        )

        assert "def run" in result

    @pytest.mark.asyncio
    async def test_execute_contingency_refusal(self) -> None:
        """Plan references a section not in context → refusal, LLM skipped."""
        from agents.agents_engineer import AgentsEngineer

        agent = _make_base_agent(AgentsEngineer)
        agent.llm.ainvoke = AsyncMock()

        result = await agent.agents_engineer_execute(
            plan="Consume INTEGRATION & BENCHMARK AUTHORITY",
            context="no markers here",
            known_sections=["INTEGRATION & BENCHMARK AUTHORITY"],
        )

        assert "context_missing" in result
        agent.llm.ainvoke.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_context_truncated(self) -> None:
        """Context longer than the truncation limit is silently trimmed."""
        from agents.agents_engineer import AgentsEngineer
        from agents.agents_utils import AGENTS_ENGINEER_CONTEXT_TRUNCATION

        agent = _make_base_agent(AgentsEngineer)
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="ok"))

        long_ctx = "x" * (AGENTS_ENGINEER_CONTEXT_TRUNCATION + 500)
        result = await agent.agents_engineer_execute(
            plan="plan", context=long_ctx, known_sections=[]
        )

        assert result == "ok"

    @pytest.mark.asyncio
    async def test_execute_verbosity_detailed(self) -> None:
        """Detailed verbosity is accepted without error."""
        from agents.agents_engineer import AgentsEngineer

        agent = _make_base_agent(AgentsEngineer)
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="full code"))

        result = await agent.agents_engineer_execute(
            plan="plan", context="ctx", verbosity="detailed", known_sections=[]
        )
        assert result == "full code"


class TestAgentsReflectorCritique:
    """Cover agents_reflector.py lines 43-96."""

    @pytest.mark.asyncio
    async def test_critique_high_confidence_skips_second_pass(self) -> None:
        """Confidence >= 0.9 → fast path, single LLM call, refined_plan = original."""
        from agents.agents_reflector import AgentsReflector

        agent = _make_base_agent(AgentsReflector)
        fast_response = json.dumps(
            {
                "confidence": 0.95,
                "errors": [],
                "severity": "NONE",
                "suggestions": [],
                "refined_plan": "SKIP",
                "improvements": [],
                "reuse_pattern": "",
                "knowledge_atom": "",
            }
        )
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content=fast_response))

        result = await agent.agents_reflector_critique(
            plan="## Plan\n1. Step.", context="ctx", task="task"
        )

        assert result["confidence"] >= 0.9
        assert result["refined_plan"] == "## Plan\n1. Step."
        assert agent.llm.ainvoke.call_count == 1

    @pytest.mark.asyncio
    async def test_critique_low_confidence_uses_refined_plan(self) -> None:
        """Confidence < 0.9 → low-confidence path, refined_plan taken from LLM output."""
        from agents.agents_reflector import AgentsReflector

        agent = _make_base_agent(AgentsReflector)
        low_conf = json.dumps(
            {
                "confidence": 0.5,
                "errors": ["step 2 is vague"],
                "severity": "MEDIUM",
                "suggestions": ["clarify step 2"],
                "refined_plan": "## Improved Plan\n1. Step.\n2. Clarified step.",
                "improvements": ["added detail"],
                "reuse_pattern": "",
                "knowledge_atom": "be specific",
            }
        )
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content=low_conf))

        result = await agent.agents_reflector_critique(
            plan="## Plan\n1. Step.\n2. Vague.", context="ctx", task="task"
        )

        assert result["confidence"] == 0.5
        assert "Improved" in result["refined_plan"]
        assert "step 2 is vague" in result["errors"]

    @pytest.mark.asyncio
    async def test_critique_parse_failure_falls_back_gracefully(self) -> None:
        """Garbled LLM output returns a dict with the original plan intact."""
        from agents.agents_reflector import AgentsReflector

        agent = _make_base_agent(AgentsReflector)
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="not json at all"))

        result = await agent.agents_reflector_critique(
            plan="original plan", context="ctx", task="task"
        )

        # parse fails → empty dict returned → falls into low-conf path with defaults
        assert isinstance(result, dict)
        assert "confidence" in result

    def test_parse_static_method_valid_json(self) -> None:
        """_agents_reflector_parse extracts JSON from raw text."""
        from agents.agents_reflector import AgentsReflector

        raw = 'prefix {"confidence": 0.9, "errors": []} suffix'
        result = AgentsReflector._agents_reflector_parse(raw, {})
        assert result["confidence"] == 0.9

    def test_parse_static_method_no_json_returns_default(self) -> None:
        """_agents_reflector_parse returns default when JSON is absent."""
        from agents.agents_reflector import AgentsReflector

        result = AgentsReflector._agents_reflector_parse("no json here", {"key": "val"})
        assert result == {"key": "val"}


class TestAgentsValidatorVerify:
    """Cover agents_validator.py lines 67-102."""

    @pytest.mark.asyncio
    async def test_verify_normal_result_calls_llm(self) -> None:
        """Normal (non-refusal) result invokes the LLM and returns parsed verdict."""
        from agents.agents_validator import AgentsValidator

        agent = _make_base_agent(AgentsValidator)
        verdict_json = json.dumps({"verdict": "passed", "score": 0.92, "issues": [], "error": None})
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content=verdict_json))

        result = await agent.agents_validator_verify(
            result="def run(): return 42", plan="## Plan", task="Implement run"
        )

        assert result["verdict"] == "passed"
        assert result["score"] == 0.92
        agent.llm.ainvoke.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_verify_garbled_json_returns_safe_default(self) -> None:
        """When LLM returns non-JSON, the safe fallback dict is returned."""
        from agents.agents_validator import AgentsValidator

        agent = _make_base_agent(AgentsValidator)
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content="not json"))

        result = await agent.agents_validator_verify(
            result="some output", plan="## Plan", task="task"
        )

        assert result["verdict"] == "passed"
        assert result["issues"] == []

    @pytest.mark.asyncio
    async def test_verify_invalid_score_type_returns_safe_default(self) -> None:
        """A non-numeric score field triggers the ValueError branch → safe default."""
        from agents.agents_validator import AgentsValidator

        agent = _make_base_agent(AgentsValidator)
        bad_json = json.dumps({"verdict": "passed", "score": "not-a-float", "issues": []})
        agent.llm.ainvoke = AsyncMock(return_value=MagicMock(content=bad_json))

        result = await agent.agents_validator_verify(result="output", plan="plan", task="task")

        assert result["verdict"] == "passed"
        assert isinstance(result["score"], float)


class TestAgentsLibrarianRetrieve:
    """Cover agents_librarian.py lines 37-81."""

    @pytest.mark.asyncio
    async def test_retrieve_initialises_retriever_once(self) -> None:
        """_agents_librarian_get_retriever is lazy; subsequent calls reuse the same instance."""
        from agents.agents_librarian import AgentsLibrarian

        mock_store = MagicMock()
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.rag_retriever_retrieve = AsyncMock(return_value=[])

        with (
            patch(
                "agents.agents_librarian.rag_vector_store_get_instance", new_callable=AsyncMock
            ) as mock_vs,
            patch("agents.agents_librarian.RagRetriever", return_value=mock_retriever_instance),
        ):
            mock_vs.return_value = mock_store

            librarian = AgentsLibrarian.__new__(AgentsLibrarian)
            librarian.llm = AsyncMock()
            librarian.llm.ainvoke = AsyncMock(return_value=MagicMock(content="synth"))
            librarian.agent_name = "LIBRARIAN"
            librarian.logger = MagicMock()
            librarian._role_doc = ""
            librarian._k = 4
            librarian._retriever = None

            r1 = await librarian._agents_librarian_get_retriever()
            r2 = await librarian._agents_librarian_get_retriever()

        assert r1 is r2
        mock_vs.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_retrieve_synthesises_docs(self) -> None:
        """Retrieved docs are joined and synthesized via LLM."""
        from agents.agents_librarian import AgentsLibrarian

        docs = [Document(page_content="doc A"), Document(page_content="doc B")]
        mock_retriever = MagicMock()
        mock_retriever.rag_retriever_retrieve = AsyncMock(return_value=docs)

        librarian = AgentsLibrarian.__new__(AgentsLibrarian)
        librarian.llm = AsyncMock()
        librarian.llm.ainvoke = AsyncMock(return_value=MagicMock(content="synthesised"))
        librarian.agent_name = "LIBRARIAN"
        librarian.logger = MagicMock()
        librarian._role_doc = ""
        librarian._k = 4
        librarian._retriever = mock_retriever

        result = await librarian.agents_librarian_retrieve("build a REST API")

        assert result == "synthesised"

    @pytest.mark.asyncio
    async def test_retrieve_llm_failure_falls_back_to_raw_text(self) -> None:
        """When LLM raises, the raw concatenated text is returned instead."""
        from agents.agents_librarian import AgentsLibrarian

        docs = [Document(page_content="fallback content")]
        mock_retriever = MagicMock()
        mock_retriever.rag_retriever_retrieve = AsyncMock(return_value=docs)

        librarian = AgentsLibrarian.__new__(AgentsLibrarian)
        librarian.llm = AsyncMock()
        librarian.llm.ainvoke = AsyncMock(side_effect=Exception("LLM down"))
        librarian.agent_name = "LIBRARIAN"
        librarian.logger = MagicMock()
        librarian._role_doc = ""
        librarian._k = 4
        librarian._retriever = mock_retriever

        result = await librarian.agents_librarian_retrieve("query")

        assert result == "fallback content"

    @pytest.mark.asyncio
    async def test_retrieve_no_docs_uses_query_as_prompt(self) -> None:
        """Empty retrieval passes the original query to the LLM."""
        from agents.agents_librarian import AgentsLibrarian

        mock_retriever = MagicMock()
        mock_retriever.rag_retriever_retrieve = AsyncMock(return_value=[])

        librarian = AgentsLibrarian.__new__(AgentsLibrarian)
        librarian.llm = AsyncMock()
        librarian.llm.ainvoke = AsyncMock(return_value=MagicMock(content="no docs synth"))
        librarian.agent_name = "LIBRARIAN"
        librarian.logger = MagicMock()
        librarian._role_doc = ""
        librarian._k = 4
        librarian._retriever = mock_retriever

        result = await librarian.agents_librarian_retrieve("my query")

        assert result == "no docs synth"
