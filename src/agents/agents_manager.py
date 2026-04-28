"""LangGraph orchestrator driving the full Phase 0–6 SDLC workflow."""

from __future__ import annotations

import asyncio
import logging
import operator
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.agents_architect import AgentsArchitect
from src.agents.agents_base import AgentsBase
from src.agents.agents_engineer import AgentsEngineer
from src.agents.agents_librarian import AgentsLibrarian
from src.agents.agents_protocol import AgentsProtocol
from src.agents.agents_reflector import AgentsReflector
from src.agents.agents_utils import (
    AGENTS_ARCHITECT_AGENT_NAME,
    AGENTS_ARCHITECT_REQUIRED_SECTIONS,
    AGENTS_ENGINEER_AGENT_NAME,
    AGENTS_LIBRARIAN_ACTION_RETRIEVED,
    AGENTS_LIBRARIAN_AGENT_NAME,
    AGENTS_MANAGER_AGENT_NAME,
    AGENTS_MANAGER_CONFIDENCE_THRESHOLD,
    AGENTS_MANAGER_DESC_PHASE_0,
    AGENTS_MANAGER_DESC_PHASE_1,
    AGENTS_MANAGER_DESC_PHASE_2,
    AGENTS_MANAGER_DESC_PHASE_3,
    AGENTS_MANAGER_DESC_PHASE_4,
    AGENTS_MANAGER_DESC_PHASE_5,
    AGENTS_MANAGER_DESC_PHASE_6,
    AGENTS_MANAGER_DOC_PATHS,
    AGENTS_MANAGER_ERR_KEYWORD_CHROMA,
    AGENTS_MANAGER_ERR_KEYWORD_QDRANT,
    AGENTS_MANAGER_ERR_KEYWORD_QUOTA,
    AGENTS_MANAGER_ERR_KEYWORD_RESOURCE_EXHAUSTED,
    AGENTS_MANAGER_ERR_KEYWORD_VECTOR,
    AGENTS_MANAGER_ERR_TIMEOUT,
    AGENTS_MANAGER_ERROR_EXECUTION_REFUSED,
    AGENTS_MANAGER_ERROR_PROTOCOL_BOOT,
    AGENTS_MANAGER_ERROR_VALIDATION_FAILED,
    AGENTS_MANAGER_EVENT_ON_CHAIN_ERROR,
    AGENTS_MANAGER_GRAPH_RECURSION_LIMIT,
    AGENTS_MANAGER_LOG_CRITIQUE_DONE,
    AGENTS_MANAGER_LOG_CRITIQUE_ERRORS,
    AGENTS_MANAGER_LOG_CRITIQUE_START,
    AGENTS_MANAGER_LOG_DRAFT_DONE,
    AGENTS_MANAGER_LOG_DRAFT_RETRY,
    AGENTS_MANAGER_LOG_DRAFT_START,
    AGENTS_MANAGER_LOG_EXECUTE_DONE,
    AGENTS_MANAGER_LOG_EXECUTE_START,
    AGENTS_MANAGER_LOG_EXECUTION_REFUSED,
    AGENTS_MANAGER_LOG_FORCE_ACCEPT,
    AGENTS_MANAGER_LOG_FORCE_EXECUTE,
    AGENTS_MANAGER_LOG_PHASE_GENERIC,
    AGENTS_MANAGER_LOG_PHASE_START,
    AGENTS_MANAGER_LOG_RETRIEVE_DONE,
    AGENTS_MANAGER_LOG_RETRIEVE_REUSE,
    AGENTS_MANAGER_LOG_TASK_CONTENT,
    AGENTS_MANAGER_LOG_VERIFY_DONE,
    AGENTS_MANAGER_LOG_VERIFY_START,
    AGENTS_MANAGER_LOG_WORKFLOW_FAILED,
    AGENTS_MANAGER_MAX_RETRIES,
    AGENTS_MANAGER_NODE_ARCHITECT,
    AGENTS_MANAGER_NODE_END_FAILED,
    AGENTS_MANAGER_NODE_END_SUCCESS,
    AGENTS_MANAGER_NODE_EXECUTE,
    AGENTS_MANAGER_NODE_LIBRARIAN,
    AGENTS_MANAGER_NODE_PROTOCOL,
    AGENTS_MANAGER_NODE_RETRY,
    AGENTS_MANAGER_NODE_REVIEW,
    AGENTS_MANAGER_NODE_TASK,
    AGENTS_MANAGER_NODE_VERIFY,
    AGENTS_MANAGER_PHASE_0,
    AGENTS_MANAGER_PHASE_1,
    AGENTS_MANAGER_PHASE_2,
    AGENTS_MANAGER_PHASE_3,
    AGENTS_MANAGER_PHASE_4,
    AGENTS_MANAGER_PHASE_5,
    AGENTS_MANAGER_PHASE_6,
    AGENTS_MANAGER_PHASE_MAX,
    AGENTS_MANAGER_PHASE_MIN,
    AGENTS_MANAGER_SCORE_FALLBACK,
    AGENTS_MANAGER_SEVERITY_FALLBACK,
    AGENTS_MANAGER_STATUS_COMPLETED,
    AGENTS_MANAGER_STATUS_FAILED,
    AGENTS_MANAGER_STREAM_VERSION,
    AGENTS_MANAGER_TASK_SYSTEM_PROMPT,
    AGENTS_MANAGER_VALIDATOR_THRESHOLD_DEFAULT,
    AGENTS_MANAGER_VERBOSITY_DEFAULT,
    AGENTS_MANAGER_WORKFLOW_TIMEOUT_SECONDS,
    AGENTS_PROTOCOL_AGENT_NAME,
    AGENTS_PROTOCOL_BOOT_PHASE,
    AGENTS_PROTOCOL_SECTION_PREAMBLE,
    AGENTS_PROTOCOL_STATUS_GREEN,
    AGENTS_REFLECTOR_AGENT_NAME,
    AGENTS_REFUSAL_STATUS_PREFIX,
    AGENTS_TRACE_ACTION_BOOT_VALIDATION,
    AGENTS_TRACE_ACTION_EXECUTION_COMPLETE,
    AGENTS_TRACE_ACTION_EXECUTION_REFUSED,
    AGENTS_TRACE_ACTION_PLAN_CRITIQUED,
    AGENTS_TRACE_ACTION_PLAN_DRAFTED,
    AGENTS_TRACE_ACTION_PLAN_REFUSED,
    AGENTS_TRACE_ACTION_TASK_CONFIRMED,
    AGENTS_VALIDATOR_AGENT_NAME,
)
from src.agents.agents_validator import AgentsValidator
from src.api.schemas.api_schemas_task import (
    ApiSchemasErrorCode,
    ApiSchemasTaskRequest,
    ApiSchemasTaskResponse,
    ApiSchemasWorkflowPhase,
)
from src.storage.storage_gcs import StorageGcs
from src.storage.storage_utils import STORAGE_GCS_PHASE_RESULT, STORAGE_GCS_PHASE_VERDICT

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD: float = AGENTS_MANAGER_CONFIDENCE_THRESHOLD


class AgentsManagerClassifier(AgentsBase):
    """LLM-backed task classifier used in Phase 1 to confirm routing and produce a preview."""

    agent_name: str = AGENTS_MANAGER_AGENT_NAME
    role_doc_paths: list[str] = AGENTS_MANAGER_DOC_PATHS


def _agents_manager_is_refusal(text: str | None) -> bool:
    """Return True when an agent output is a fail-closed refusal, not a real result.

    The ARCHITECT and ENGINEER guards emit a deterministic preamble beginning with
    ``status: context_missing`` when required protocol sections are absent from the
    runtime context. The MANAGER must treat those outputs as workflow failures
    rather than passing them to VALIDATOR as if they were normal results — doing so
    produces the ``completed + passed`` contradiction that commit 18eeb89's guard was
    meant to prevent.

    Args:
        text: Raw agent output to classify.

    Returns:
        True when the output's leading non-whitespace characters start with the
        canonical refusal prefix, False otherwise (including ``None`` / empty).
    """

    if not text:
        return False
    return text.lstrip().startswith(AGENTS_REFUSAL_STATUS_PREFIX)


def _agents_manager_extract_missing_sections(refusal: str) -> str:
    """Parse the ``missing_sections: ...`` line from a refusal preamble.

    Args:
        refusal: Refusal string produced by the ARCHITECT or ENGINEER guard.

    Returns:
        Comma-separated section markers, or ``"<unknown>"`` when the line is absent
        or malformed (defensive — the guard always emits this line today).
    """

    for line in refusal.splitlines():
        stripped = line.strip()
        if stripped.startswith("missing_sections:"):
            return stripped[len("missing_sections:") :].strip() or "<unknown>"
    return "<unknown>"


def _agents_manager_is_plan_approved(critique: dict | None, threshold: float) -> bool:
    """Return True if the reflector approved the plan or confidence meets the threshold.

    Args:
        critique: Reflector output dict containing ``approved``, ``confidence``, and optional
            ``refined_plan`` keys. May be ``None`` when no critique has been produced yet.
        threshold: Minimum confidence score required to treat the plan as approved when the
            explicit ``approved`` flag is absent or False.

    Returns:
        True if the reflector set ``approved=True`` or the recorded confidence score is greater
        than or equal to ``threshold``; False in all other cases including when ``critique`` is
        ``None``.
    """

    if not critique:
        return False
    confidence: float = float(critique.get("confidence", 0.0))
    return critique.get("approved") is True or confidence >= threshold


class AgentsState(TypedDict):
    """Shared state dict passed through every LangGraph node."""

    task_id: str
    content: str
    phase: int
    messages: Annotated[list, operator.add]
    active_agent: str
    context: str | None
    plan: str | None
    critique: dict | None
    result: str | None
    confidence: float
    approved: bool
    retry_count: int
    error: str | None
    protocol_status: str | None
    protocol_violations: list | None
    task_preview: str | None
    confidence_threshold: float | None
    validator_confidence_threshold: float | None
    max_retries_override: int | None
    verbosity: str | None
    artifact_uri: str | None


async def _agents_manager_protocol_phase(state: AgentsState) -> dict:
    """Phase 0: boot validation. Halts the session on any integrity breach.

    Args:
        state: Current LangGraph AgentsState dict carrying task_id, content, context, plan,
            critique, result, and all retry/config fields.

    Returns:
        Partial state dict merged by LangGraph into the running state.
    """

    logger.info(
        AGENTS_MANAGER_LOG_PHASE_START.format(
            phase=AGENTS_MANAGER_PHASE_0,
            description=AGENTS_MANAGER_DESC_PHASE_0,
            task_id=state["task_id"],
        )
    )
    protocol = AgentsProtocol()
    result = await protocol.agents_protocol_validate(
        task_id=state["task_id"],
        content=state["content"],
    )

    error = None
    if result["protocol_status"] != AGENTS_PROTOCOL_STATUS_GREEN:
        violations = result.get("violations", [])
        error = AGENTS_MANAGER_ERROR_PROTOCOL_BOOT.format(violations=violations)
        logger.error(f"[MANAGER] {error}")

    return {
        "phase": AGENTS_PROTOCOL_BOOT_PHASE,
        "protocol_status": result["protocol_status"],
        "protocol_violations": result.get("violations", []),
        "active_agent": AGENTS_PROTOCOL_AGENT_NAME,
        "error": error,
        "messages": [
            {
                "phase": AGENTS_PROTOCOL_BOOT_PHASE,
                "agent": AGENTS_PROTOCOL_AGENT_NAME,
                "action": AGENTS_TRACE_ACTION_BOOT_VALIDATION,
                "status": result["protocol_status"],
                "violations": result.get("violations", []),
            }
        ],
    }


async def _agents_manager_task_phase(state: AgentsState) -> dict:
    """Phase 1: confirm the task is ready for processing. No LLM needed.

    Args:
        state: Current LangGraph AgentsState dict carrying task_id, content, context, plan,
            critique, result, and all retry/config fields.

    Returns:
        Partial state dict merged by LangGraph into the running state.
    """

    logger.info(
        AGENTS_MANAGER_LOG_PHASE_START.format(
            phase=AGENTS_MANAGER_PHASE_1,
            description=AGENTS_MANAGER_DESC_PHASE_1,
            task_id=state["task_id"],
        )
    )

    import json as _json

    task_preview: str = state["content"][:120]
    try:
        mgr = AgentsManagerClassifier()
        system_prompt: str = mgr._agents_base_build_system_prompt(AGENTS_MANAGER_TASK_SYSTEM_PROMPT)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["content"]),
        ]
        raw_response: str = await mgr._agents_base_call_llm(messages)
        parsed: dict = _json.loads(raw_response)
        task_preview = str(parsed.get("preview", state["content"][:120]))
    except Exception:
        task_preview = state["content"][:120]

    logger.info(AGENTS_MANAGER_LOG_TASK_CONTENT.format(content=task_preview))
    return {
        "phase": AGENTS_MANAGER_PHASE_1,
        "task_preview": task_preview,
        "active_agent": AGENTS_MANAGER_AGENT_NAME,
        "messages": [
            {
                "phase": AGENTS_MANAGER_PHASE_1,
                "agent": AGENTS_MANAGER_AGENT_NAME,
                "action": AGENTS_TRACE_ACTION_TASK_CONFIRMED,
            }
        ],
    }


async def _agents_manager_librarian_phase(state: AgentsState) -> dict:
    """Phase 2: RAG retrieval. Skips the vector store call on retries when context is cached.

    Args:
        state: Current LangGraph AgentsState dict carrying task_id, content, context, plan,
            critique, result, and all retry/config fields.

    Returns:
        Partial state dict merged by LangGraph into the running state.
    """

    logger.info(
        AGENTS_MANAGER_LOG_PHASE_GENERIC.format(
            phase=AGENTS_MANAGER_PHASE_2, description=AGENTS_MANAGER_DESC_PHASE_2
        )
    )

    if state.get("context") is not None:
        ctx = state["context"]
        has_retrieved = True
        logger.info(AGENTS_MANAGER_LOG_RETRIEVE_REUSE)
    else:
        librarian = AgentsLibrarian()
        synthesized: str = await librarian.agents_librarian_retrieve(state["content"])
        # Prepend the canonical protocol-section preamble so the ARCHITECT/ENGINEER
        # fail-closed guards see the literal section markers. Without this injection
        # every run refuses because LIBRARIAN never retrieves system-level markers.
        ctx = (
            AGENTS_PROTOCOL_SECTION_PREAMBLE + "\n\n" + synthesized
            if synthesized
            else AGENTS_PROTOCOL_SECTION_PREAMBLE
        )
        has_retrieved = bool(synthesized)
        logger.info(AGENTS_MANAGER_LOG_RETRIEVE_DONE.format(count=int(has_retrieved)))

    return {
        "phase": AGENTS_MANAGER_PHASE_2,
        "context": ctx,
        "active_agent": AGENTS_LIBRARIAN_AGENT_NAME,
        "messages": [
            {
                "phase": AGENTS_MANAGER_PHASE_2,
                "agent": AGENTS_LIBRARIAN_AGENT_NAME,
                "action": AGENTS_LIBRARIAN_ACTION_RETRIEVED,
                "docs_retrieved": int(has_retrieved),
            }
        ],
    }


async def _agents_manager_architect_phase(state: AgentsState) -> dict:
    """Phase 3: plan drafting. On retries, uses the reflector's refined plan instead.

    Args:
        state: Current LangGraph AgentsState dict carrying task_id, content, context, plan,
            critique, result, and all retry/config fields.

    Returns:
        Partial state dict merged by LangGraph into the running state.
    """
    logger.info(
        AGENTS_MANAGER_LOG_PHASE_GENERIC.format(
            phase=AGENTS_MANAGER_PHASE_3, description=AGENTS_MANAGER_DESC_PHASE_3
        )
    )

    critique = state.get("critique")
    if critique and critique.get("refined_plan"):
        plan = critique["refined_plan"]
        logger.info(AGENTS_MANAGER_LOG_DRAFT_RETRY)
    else:
        logger.info(AGENTS_MANAGER_LOG_DRAFT_START)
        architect = AgentsArchitect()
        plan = await architect.agents_architect_draft_plan(
            state["content"],
            state.get("context") or "",
            verbosity=state.get("verbosity") or AGENTS_MANAGER_VERBOSITY_DEFAULT,
            required_sections=AGENTS_ARCHITECT_REQUIRED_SECTIONS,
        )
        logger.info(AGENTS_MANAGER_LOG_DRAFT_DONE.format(count=len(plan)))

    # Fail-closed short-circuit: the ARCHITECT refused to draft because required
    # protocol sections were absent from the context. Propagate the refusal as a
    # workflow error instead of handing a refusal string to the REFLECTOR/ENGINEER.
    if _agents_manager_is_refusal(plan):
        missing = _agents_manager_extract_missing_sections(plan)
        logger.warning(
            AGENTS_MANAGER_LOG_EXECUTION_REFUSED.format(
                agent=AGENTS_ARCHITECT_AGENT_NAME, missing=missing
            )
        )
        return {
            "phase": AGENTS_MANAGER_PHASE_3,
            "plan": plan,
            "error": AGENTS_MANAGER_ERROR_EXECUTION_REFUSED.format(
                agent=AGENTS_ARCHITECT_AGENT_NAME, missing=missing
            ),
            "active_agent": AGENTS_ARCHITECT_AGENT_NAME,
            "messages": [
                {
                    "phase": AGENTS_MANAGER_PHASE_3,
                    "agent": AGENTS_ARCHITECT_AGENT_NAME,
                    "action": AGENTS_TRACE_ACTION_PLAN_REFUSED,
                    "missing_sections": missing,
                }
            ],
        }

    return {
        "phase": AGENTS_MANAGER_PHASE_3,
        "plan": plan,
        "active_agent": AGENTS_ARCHITECT_AGENT_NAME,
        "messages": [
            {
                "phase": AGENTS_MANAGER_PHASE_3,
                "agent": AGENTS_ARCHITECT_AGENT_NAME,
                "action": AGENTS_TRACE_ACTION_PLAN_DRAFTED,
            }
        ],
    }


async def _agents_manager_critique_phase(state: AgentsState) -> dict:
    """Phase 4: reflector confidence audit.

    Args:
        state: Current LangGraph AgentsState dict carrying task_id, content, context, plan,
            critique, result, and all retry/config fields.

    Returns:
        Partial state dict merged by LangGraph into the running state.
    """

    logger.info(
        AGENTS_MANAGER_LOG_PHASE_GENERIC.format(
            phase=AGENTS_MANAGER_PHASE_4, description=AGENTS_MANAGER_DESC_PHASE_4
        )
    )
    logger.info(AGENTS_MANAGER_LOG_CRITIQUE_START)

    reflector = AgentsReflector()
    critique = await reflector.agents_reflector_critique(
        plan=state["plan"] or "",
        context=state.get("context") or "",
        task=state["content"],
    )

    logger.info(
        AGENTS_MANAGER_LOG_CRITIQUE_DONE.format(
            confidence=critique.get("confidence", 0.0),
            severity=critique.get("severity", AGENTS_MANAGER_SEVERITY_FALLBACK),
        )
    )

    if critique.get("errors"):
        logger.info(AGENTS_MANAGER_LOG_CRITIQUE_ERRORS.format(errors=critique["errors"]))

    threshold = state.get("confidence_threshold") or CONFIDENCE_THRESHOLD
    confidence_val = float(critique.get("confidence", 0.0))
    approved_val = _agents_manager_is_plan_approved(critique, threshold)

    return {
        "phase": AGENTS_MANAGER_PHASE_4,
        "critique": critique,
        "confidence": confidence_val,
        "approved": approved_val,
        "active_agent": AGENTS_REFLECTOR_AGENT_NAME,
        "messages": [
            {
                "phase": AGENTS_MANAGER_PHASE_4,
                "agent": AGENTS_REFLECTOR_AGENT_NAME,
                "action": AGENTS_TRACE_ACTION_PLAN_CRITIQUED,
                "approved": approved_val,
            }
        ],
    }


async def _agents_manager_execute_phase(state: AgentsState) -> dict:
    """Phase 5: engineer executes the approved plan.

    Args:
        state: Current LangGraph AgentsState dict carrying task_id, content, context, plan,
            critique, result, and all retry/config fields.

    Returns:
        Partial state dict merged by LangGraph into the running state.
    """

    logger.info(
        AGENTS_MANAGER_LOG_PHASE_GENERIC.format(
            phase=AGENTS_MANAGER_PHASE_5, description=AGENTS_MANAGER_DESC_PHASE_5
        )
    )
    logger.info(AGENTS_MANAGER_LOG_EXECUTE_START)

    engineer = AgentsEngineer()
    result = await engineer.agents_engineer_execute(
        state["plan"] or "",
        state.get("context") or "",
        verbosity=state.get("verbosity") or AGENTS_MANAGER_VERBOSITY_DEFAULT,
    )

    result_preview = result[:60].replace("\n", " ")
    logger.info(
        AGENTS_MANAGER_LOG_EXECUTE_DONE.format(
            count=len(result),
            preview=result_preview,
        )
    )

    # Fail-closed short-circuit: the ENGINEER refused to execute because the plan
    # references protocol sections absent from context. Record the refusal as a
    # workflow error, emit the execution_refused trace (NOT execution_complete),
    # skip VALIDATOR, and let the post-graph status mapping surface status=failed.
    if _agents_manager_is_refusal(result):
        missing = _agents_manager_extract_missing_sections(result)
        logger.warning(
            AGENTS_MANAGER_LOG_EXECUTION_REFUSED.format(
                agent=AGENTS_ENGINEER_AGENT_NAME, missing=missing
            )
        )
        artifact_uri = StorageGcs().storage_gcs_upload_artifact(
            task_id=state["task_id"],
            phase=STORAGE_GCS_PHASE_RESULT,
            content=result,
        )
        return {
            "phase": AGENTS_MANAGER_PHASE_5,
            "result": result,
            "artifact_uri": artifact_uri,
            "error": AGENTS_MANAGER_ERROR_EXECUTION_REFUSED.format(
                agent=AGENTS_ENGINEER_AGENT_NAME, missing=missing
            ),
            "active_agent": AGENTS_ENGINEER_AGENT_NAME,
            "messages": [
                {
                    "phase": AGENTS_MANAGER_PHASE_5,
                    "agent": AGENTS_ENGINEER_AGENT_NAME,
                    "action": AGENTS_TRACE_ACTION_EXECUTION_REFUSED,
                    "missing_sections": missing,
                }
            ],
        }

    artifact_uri = StorageGcs().storage_gcs_upload_artifact(
        task_id=state["task_id"],
        phase=STORAGE_GCS_PHASE_RESULT,
        content=result,
    )

    return {
        "phase": AGENTS_MANAGER_PHASE_5,
        "result": result,
        "artifact_uri": artifact_uri,
        "active_agent": AGENTS_ENGINEER_AGENT_NAME,
        "messages": [
            {
                "phase": AGENTS_MANAGER_PHASE_5,
                "agent": AGENTS_ENGINEER_AGENT_NAME,
                "action": AGENTS_TRACE_ACTION_EXECUTION_COMPLETE,
            }
        ],
    }


async def _agents_manager_verify_phase(state: AgentsState) -> dict:
    """Phase 6: QA verification of the execution result.

    Args:
        state: Current LangGraph AgentsState dict carrying task_id, content, context, plan,
            critique, result, and all retry/config fields.

    Returns:
        Partial state dict merged by LangGraph into the running state.
    """

    logger.info(
        AGENTS_MANAGER_LOG_PHASE_GENERIC.format(
            phase=AGENTS_MANAGER_PHASE_6, description=AGENTS_MANAGER_DESC_PHASE_6
        )
    )
    logger.info(AGENTS_MANAGER_LOG_VERIFY_START)

    validator = AgentsValidator()
    verdict = await validator.agents_validator_verify(
        result=state["result"] or "",
        plan=state["plan"] or "",
        task=state["content"],
    )

    # Same gating logic as the reflector: score >= threshold = pass
    validator_threshold = float(
        state.get("validator_confidence_threshold") or AGENTS_MANAGER_VALIDATOR_THRESHOLD_DEFAULT
    )
    score = float(verdict.get("score", 1.0))
    error = None
    if score < validator_threshold:
        error = AGENTS_MANAGER_ERROR_VALIDATION_FAILED.format(issues=verdict.get("issues", []))

    logger.info(
        AGENTS_MANAGER_LOG_VERIFY_DONE.format(
            score=verdict.get("score", AGENTS_MANAGER_SCORE_FALLBACK),
        )
    )

    StorageGcs().storage_gcs_upload_artifact(
        task_id=state["task_id"],
        phase=STORAGE_GCS_PHASE_VERDICT,
        content=verdict,
    )

    return {
        "phase": AGENTS_MANAGER_PHASE_6,
        "confidence": float(verdict.get("score", state["confidence"])),
        "error": error,
        "active_agent": AGENTS_VALIDATOR_AGENT_NAME,
        "messages": [
            {
                "phase": AGENTS_MANAGER_PHASE_6,
                "agent": AGENTS_VALIDATOR_AGENT_NAME,
                "verdict": verdict.get("verdict"),
                "score": verdict.get("score"),
            }
        ],
    }


async def _agents_manager_increment_retry(state: AgentsState) -> dict:
    """Bump retry counter before looping back to librarian.

    Args:
        state: Current LangGraph AgentsState dict carrying task_id, content, context, plan,
            critique, result, and all retry/config fields.

    Returns:
        Partial state dict merged by LangGraph into the running state.
    """

    return {"retry_count": state["retry_count"] + 1}


def _agents_manager_route_after_architect(state: AgentsState) -> str:
    """Short-circuit to END_FAILED when the ARCHITECT refused; otherwise proceed to REVIEW.

    Args:
        state: Current AgentsState.

    Returns:
        LangGraph node name string indicating which node to visit next.
    """

    if _agents_manager_is_refusal(state.get("plan")):
        return AGENTS_MANAGER_NODE_END_FAILED
    return AGENTS_MANAGER_NODE_REVIEW


def _agents_manager_route_after_execute(state: AgentsState) -> str:
    """Short-circuit to END_FAILED when the ENGINEER refused; otherwise proceed to VERIFY.

    Args:
        state: Current AgentsState.

    Returns:
        LangGraph node name string indicating which node to visit next.
    """

    if _agents_manager_is_refusal(state.get("result")):
        return AGENTS_MANAGER_NODE_END_FAILED
    return AGENTS_MANAGER_NODE_VERIFY


def _agents_manager_route_after_protocol(state: AgentsState) -> str:
    """Green means proceed; anything else kills the session.

    Args:
        state: Current AgentsState.

    Returns:
        LangGraph node name string indicating which node to visit next.
    """

    return (
        AGENTS_MANAGER_NODE_TASK
        if state.get("protocol_status") == AGENTS_PROTOCOL_STATUS_GREEN
        else AGENTS_MANAGER_NODE_END_FAILED
    )


def _agents_manager_route_after_critique(state: AgentsState) -> str:
    """Approve on high confidence or explicit approval. Force-execute after max retries.

    Args:
        state: Current AgentsState.

    Returns:
        LangGraph node name string indicating which node to visit next.
    """

    critique = state.get("critique")
    if not critique:
        return AGENTS_MANAGER_NODE_EXECUTE

    threshold = state.get("confidence_threshold") or CONFIDENCE_THRESHOLD
    confidence = float(critique.get("confidence", 0.0))
    if _agents_manager_is_plan_approved(critique, threshold):
        return AGENTS_MANAGER_NODE_EXECUTE

    retries = state.get("retry_count", 0)
    max_retries = state.get("max_retries_override") or AGENTS_MANAGER_MAX_RETRIES
    if retries >= max_retries:
        logger.warning(
            AGENTS_MANAGER_LOG_FORCE_EXECUTE.format(
                retries=retries,
                max_retries=max_retries,
                confidence=confidence,
            )
        )
        return AGENTS_MANAGER_NODE_EXECUTE

    return AGENTS_MANAGER_NODE_RETRY


def _agents_manager_route_after_verify(state: AgentsState) -> str:
    """Pass through on success. On failure, retry or accept as-is if budget is blown.

    Args:
        state: Current AgentsState.

    Returns:
        LangGraph node name string indicating which node to visit next.
    """

    if not state.get("error"):
        return AGENTS_MANAGER_NODE_END_SUCCESS

    retries = state.get("retry_count", 0)
    max_retries = state.get("max_retries_override") or AGENTS_MANAGER_MAX_RETRIES
    if retries >= max_retries:
        logger.warning(
            AGENTS_MANAGER_LOG_FORCE_ACCEPT.format(
                retries=retries,
                max_retries=max_retries,
            )
        )
        return AGENTS_MANAGER_NODE_END_SUCCESS

    return AGENTS_MANAGER_NODE_RETRY


class AgentsManager:
    """Builds and runs the LangGraph state machine for the full agent pipeline."""

    def __init__(self, graph) -> None:
        """Store the compiled graph instance.

        Args:
            graph: Compiled LangGraph StateGraph instance produced by
                ``StateGraph.compile(checkpointer=...)``.
        """
        self._graph = graph

    @classmethod
    async def agents_manager_create(cls) -> "AgentsManager":
        """Build the graph.

        Returns:
            Fully compiled AgentsManager with a MemorySaver checkpointer wired into the
            LangGraph StateGraph, ready to invoke or stream events.
        """

        builder = StateGraph(AgentsState)

        builder.add_node(AGENTS_MANAGER_NODE_PROTOCOL, _agents_manager_protocol_phase)
        builder.add_node(AGENTS_MANAGER_NODE_TASK, _agents_manager_task_phase)
        builder.add_node(AGENTS_MANAGER_NODE_LIBRARIAN, _agents_manager_librarian_phase)
        builder.add_node(AGENTS_MANAGER_NODE_ARCHITECT, _agents_manager_architect_phase)
        builder.add_node(AGENTS_MANAGER_NODE_REVIEW, _agents_manager_critique_phase)
        builder.add_node(AGENTS_MANAGER_NODE_EXECUTE, _agents_manager_execute_phase)
        builder.add_node(AGENTS_MANAGER_NODE_VERIFY, _agents_manager_verify_phase)
        builder.add_node(AGENTS_MANAGER_NODE_RETRY, _agents_manager_increment_retry)

        builder.set_entry_point(AGENTS_MANAGER_NODE_PROTOCOL)

        builder.add_conditional_edges(
            AGENTS_MANAGER_NODE_PROTOCOL,
            _agents_manager_route_after_protocol,
            {
                AGENTS_MANAGER_NODE_TASK: AGENTS_MANAGER_NODE_TASK,
                AGENTS_MANAGER_NODE_END_FAILED: END,
            },
        )

        builder.add_edge(AGENTS_MANAGER_NODE_TASK, AGENTS_MANAGER_NODE_LIBRARIAN)
        builder.add_edge(AGENTS_MANAGER_NODE_LIBRARIAN, AGENTS_MANAGER_NODE_ARCHITECT)

        # After architect: short-circuit to END on a fail-closed refusal so REFLECTOR
        # and downstream phases never see a refusal string as a real plan.
        builder.add_conditional_edges(
            AGENTS_MANAGER_NODE_ARCHITECT,
            _agents_manager_route_after_architect,
            {
                AGENTS_MANAGER_NODE_REVIEW: AGENTS_MANAGER_NODE_REVIEW,
                AGENTS_MANAGER_NODE_END_FAILED: END,
            },
        )

        # After review: execute if approved, otherwise retry (force-execute after max retries)
        builder.add_conditional_edges(
            AGENTS_MANAGER_NODE_REVIEW,
            _agents_manager_route_after_critique,
            {
                AGENTS_MANAGER_NODE_EXECUTE: AGENTS_MANAGER_NODE_EXECUTE,
                AGENTS_MANAGER_NODE_RETRY: AGENTS_MANAGER_NODE_RETRY,
            },
        )

        # After execute: short-circuit to END on a fail-closed ENGINEER refusal so
        # VALIDATOR never rubber-stamps a refusal string with a passed verdict.
        builder.add_conditional_edges(
            AGENTS_MANAGER_NODE_EXECUTE,
            _agents_manager_route_after_execute,
            {
                AGENTS_MANAGER_NODE_VERIFY: AGENTS_MANAGER_NODE_VERIFY,
                AGENTS_MANAGER_NODE_END_FAILED: END,
            },
        )

        # After verify: done if passing, retry or accept-as-is if budget exhausted
        builder.add_conditional_edges(
            AGENTS_MANAGER_NODE_VERIFY,
            _agents_manager_route_after_verify,
            {
                AGENTS_MANAGER_NODE_END_SUCCESS: END,
                AGENTS_MANAGER_NODE_RETRY: AGENTS_MANAGER_NODE_RETRY,
            },
        )

        # Retry loops back to librarian (context stays cached so retrieval is skipped)
        builder.add_edge(AGENTS_MANAGER_NODE_RETRY, AGENTS_MANAGER_NODE_LIBRARIAN)

        checkpointer = MemorySaver()
        graph = builder.compile(checkpointer=checkpointer)
        return cls(graph)

    async def agents_manager_run(self, request: ApiSchemasTaskRequest) -> ApiSchemasTaskResponse:
        """Run the full pipeline synchronously and return a completed response.

        Args:
            request: ApiSchemasTaskRequest carrying the ``task_id`` (unique identifier used as
                the LangGraph thread ID and GCS artifact key) and ``content`` (raw task
                description passed to every agent phase).

        Returns:
            ApiSchemasTaskResponse populated with ``status``, ``result``, ``confidence``,
            ``agent_trace`` (the full message log), ``artifact_uri`` (GCS URI of the uploaded
            result), and an optional ``error`` / ``error_code`` on failure.
        """

        initial_state: AgentsState = {
            "task_id": request.task_id,
            "content": request.content,
            "phase": AGENTS_PROTOCOL_BOOT_PHASE,
            "messages": [],
            "active_agent": AGENTS_MANAGER_AGENT_NAME,
            "context": None,
            "plan": None,
            "critique": None,
            "result": None,
            "confidence": 0.0,
            "approved": False,
            "retry_count": 0,
            "error": None,
            "protocol_status": None,
            "protocol_violations": None,
            "task_preview": None,
            "confidence_threshold": None,
            "validator_confidence_threshold": None,
            "max_retries_override": None,
            "verbosity": None,
            "artifact_uri": None,
        }

        config = {
            "configurable": {"thread_id": request.task_id},
            "recursion_limit": AGENTS_MANAGER_GRAPH_RECURSION_LIMIT,
        }

        try:
            final_state = await asyncio.wait_for(
                self._graph.ainvoke(initial_state, config=config),
                timeout=AGENTS_MANAGER_WORKFLOW_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.error(
                "Workflow timeout (%ds) for task %s",
                AGENTS_MANAGER_WORKFLOW_TIMEOUT_SECONDS,
                request.task_id,
            )
            return ApiSchemasTaskResponse(
                task_id=request.task_id,
                status="failed",
                result=None,
                phases_completed=[],
                confidence=0.0,
                latency_ms=0.0,
                agent_trace=[],
                error=AGENTS_MANAGER_ERR_TIMEOUT.format(
                    timeout=AGENTS_MANAGER_WORKFLOW_TIMEOUT_SECONDS
                ),
                error_code=ApiSchemasErrorCode.WORKFLOW_TIMEOUT,
            )
        except Exception as exc:
            logger.error(f"Workflow failed for task {request.task_id}: {exc}", exc_info=True)
            return ApiSchemasTaskResponse(
                task_id=request.task_id,
                status="failed",
                result=None,
                phases_completed=[],
                confidence=0.0,
                latency_ms=0.0,
                agent_trace=[],
                error=str(exc),
                error_code=ApiSchemasErrorCode.INTERNAL_ERROR,
            )

        # Deduplicate completed phases from the message trace
        phases_completed = list(
            {
                ApiSchemasWorkflowPhase(msg["phase"])
                for msg in final_state.get("messages", [])
                if "phase" in msg
                and AGENTS_MANAGER_PHASE_MIN <= msg["phase"] <= AGENTS_MANAGER_PHASE_MAX
            }
        )

        has_error = final_state.get("error") is not None
        has_result = final_state.get("result") is not None
        is_refusal = _agents_manager_is_refusal(
            final_state.get("result")
        ) or _agents_manager_is_refusal(final_state.get("plan"))
        # Refusals carry a result string (the refusal preamble) but MUST surface as
        # "failed" — otherwise the dashboard shows the contradictory
        # completed+execution_refused combination.
        status = (
            AGENTS_MANAGER_STATUS_FAILED
            if (has_error and not has_result) or is_refusal
            else AGENTS_MANAGER_STATUS_COMPLETED
        )

        # Classify the error for the API response
        error_code = None
        if has_error:
            err_msg = final_state.get("error", "")
            retry_count = final_state.get("retry_count", 0)
            confidence = final_state.get("confidence", 0.0)
            if is_refusal:
                error_code = ApiSchemasErrorCode.AGENT_EXECUTION_REFUSED
            elif (
                AGENTS_MANAGER_ERR_KEYWORD_QUOTA in err_msg.lower()
                or AGENTS_MANAGER_ERR_KEYWORD_RESOURCE_EXHAUSTED in err_msg
            ):
                error_code = ApiSchemasErrorCode.AGENT_QUOTA_EXHAUSTED
            elif retry_count >= AGENTS_MANAGER_MAX_RETRIES and confidence < CONFIDENCE_THRESHOLD:
                error_code = ApiSchemasErrorCode.AGENT_CONFIDENCE_LOW
            elif retry_count >= AGENTS_MANAGER_MAX_RETRIES:
                error_code = ApiSchemasErrorCode.WORKFLOW_MAX_RETRIES
            elif (
                AGENTS_MANAGER_ERR_KEYWORD_VECTOR in err_msg.lower()
                or AGENTS_MANAGER_ERR_KEYWORD_QDRANT in err_msg.lower()
                or AGENTS_MANAGER_ERR_KEYWORD_CHROMA in err_msg.lower()
            ):
                error_code = ApiSchemasErrorCode.RAG_RETRIEVAL_FAILED
            else:
                error_code = ApiSchemasErrorCode.AGENT_EXECUTION_FAILED

        return ApiSchemasTaskResponse(
            task_id=request.task_id,
            status=status,
            result=final_state.get("result"),
            artifact_uri=final_state.get("artifact_uri"),
            phases_completed=sorted(phases_completed),
            confidence=final_state.get("confidence", 0.0),
            latency_ms=0.0,  # filled in by the router
            agent_trace=final_state.get("messages", []),
            error=final_state.get("error"),
            error_code=error_code,
        )

    async def agents_manager_stream_events(
        self,
        request: ApiSchemasTaskRequest,
        confidence_threshold: float | None = None,
        validator_confidence_threshold: float | None = None,
        max_retries: int | None = None,
        verbosity: str | None = None,
        resume: bool = False,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream LangGraph events in real time for the Chainlit UI.

        Args:
            request: ApiSchemasTaskRequest carrying ``task_id`` and ``content``.
            confidence_threshold: Override the reflector gate confidence floor. When ``None``
                the module-level ``CONFIDENCE_THRESHOLD`` constant is used.
            validator_confidence_threshold: Override the validator gate score floor. When
                ``None`` the ``AGENTS_MANAGER_VALIDATOR_THRESHOLD_DEFAULT`` constant is used.
            max_retries: Override the maximum number of architect/reflector retry iterations.
                When ``None`` the ``AGENTS_MANAGER_MAX_RETRIES`` constant is used.
            verbosity: Output detail level forwarded to the architect and engineer agents
                (e.g. ``"standard"``, ``"verbose"``). Defaults to
                ``AGENTS_MANAGER_VERBOSITY_DEFAULT`` when ``None``.
            resume: When ``True`` the graph is invoked with ``None`` as input so LangGraph
                restores execution from the MemorySaver checkpoint for the given ``task_id``
                instead of reinitialising state from scratch.

        Returns:
            Async generator of LangGraph event dicts as produced by
            ``StateGraph.astream_events``. On unhandled exceptions a terminal error event
            dict is yielded before the generator closes.
        """

        initial_state: AgentsState = {
            "task_id": request.task_id,
            "content": request.content,
            "phase": AGENTS_PROTOCOL_BOOT_PHASE,
            "messages": [],
            "active_agent": AGENTS_MANAGER_AGENT_NAME,
            "context": None,
            "plan": None,
            "critique": None,
            "result": None,
            "confidence": 0.0,
            "approved": False,
            "retry_count": 0,
            "error": None,
            "protocol_status": None,
            "protocol_violations": None,
            "task_preview": None,
            "confidence_threshold": confidence_threshold,
            "validator_confidence_threshold": validator_confidence_threshold,
            "max_retries_override": max_retries,
            "verbosity": verbosity or "standard",
            "artifact_uri": None,
        }
        config = {
            "configurable": {"thread_id": request.task_id},
            "recursion_limit": AGENTS_MANAGER_GRAPH_RECURSION_LIMIT,
        }
        task_id = request.task_id
        # On resume, pass None so LangGraph restores from the MemorySaver checkpoint
        stream_input = None if resume else initial_state

        try:
            async for event in self._graph.astream_events(
                stream_input,
                config=config,
                version=AGENTS_MANAGER_STREAM_VERSION,
            ):
                yield event
        except Exception as e:
            logger.error(AGENTS_MANAGER_LOG_WORKFLOW_FAILED.format(task_id=task_id, error=str(e)))
            yield {
                "event": AGENTS_MANAGER_EVENT_ON_CHAIN_ERROR,
                "data": {"error": str(e), "status": AGENTS_MANAGER_STATUS_FAILED},
            }
