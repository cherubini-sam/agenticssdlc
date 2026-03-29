"""LangGraph orchestrator driving the full Phase 0–6 SDLC workflow."""

from __future__ import annotations

import asyncio
import logging
import operator
from collections.abc import AsyncGenerator
from typing import Annotated, Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from src.agents.agents_architect import AgentsArchitect
from src.agents.agents_engineer import AgentsEngineer
from src.agents.agents_librarian import AgentsLibrarian
from src.agents.agents_protocol import AgentsProtocol
from src.agents.agents_reflector import AgentsReflector
from src.agents.agents_utils import (
    AGENTS_ARCHITECT_AGENT_NAME,
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
    AGENTS_MANAGER_ERR_KEYWORD_CHROMA,
    AGENTS_MANAGER_ERR_KEYWORD_QDRANT,
    AGENTS_MANAGER_ERR_KEYWORD_QUOTA,
    AGENTS_MANAGER_ERR_KEYWORD_RESOURCE_EXHAUSTED,
    AGENTS_MANAGER_ERR_KEYWORD_VECTOR,
    AGENTS_MANAGER_ERR_TIMEOUT,
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
    AGENTS_MANAGER_VALIDATOR_THRESHOLD_DEFAULT,
    AGENTS_MANAGER_VERBOSITY_DEFAULT,
    AGENTS_MANAGER_WORKFLOW_TIMEOUT_SECONDS,
    AGENTS_PROTOCOL_AGENT_NAME,
    AGENTS_PROTOCOL_BOOT_PHASE,
    AGENTS_PROTOCOL_STATUS_GREEN,
    AGENTS_REFLECTOR_AGENT_NAME,
    AGENTS_TRACE_ACTION_BOOT_VALIDATION,
    AGENTS_TRACE_ACTION_EXECUTION_COMPLETE,
    AGENTS_TRACE_ACTION_PLAN_CRITIQUED,
    AGENTS_TRACE_ACTION_PLAN_DRAFTED,
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

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD: float = AGENTS_MANAGER_CONFIDENCE_THRESHOLD


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
    # User-configurable overrides from the UI session
    confidence_threshold: float | None
    validator_confidence_threshold: float | None
    max_retries_override: int | None
    verbosity: str | None


async def _agents_manager_protocol_phase(state: AgentsState) -> dict:
    """Phase 0: boot validation. Halts the session on any integrity breach."""

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
    """Phase 1: confirm the task is ready for processing. No LLM needed."""

    logger.info(
        AGENTS_MANAGER_LOG_PHASE_START.format(
            phase=AGENTS_MANAGER_PHASE_1,
            description=AGENTS_MANAGER_DESC_PHASE_1,
            task_id=state["task_id"],
        )
    )
    logger.info(AGENTS_MANAGER_LOG_TASK_CONTENT.format(content=state["content"][:120]))
    return {
        "phase": AGENTS_MANAGER_PHASE_1,
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
    """Phase 2: RAG retrieval. Skips the vector store call on retries when context is cached."""

    logger.info(
        AGENTS_MANAGER_LOG_PHASE_GENERIC.format(
            phase=AGENTS_MANAGER_PHASE_2, description=AGENTS_MANAGER_DESC_PHASE_2
        )
    )

    if state.get("context") is not None:
        ctx = state["context"]
        docs_retrieved = 0
        logger.info(AGENTS_MANAGER_LOG_RETRIEVE_REUSE)
    else:
        librarian = AgentsLibrarian()
        docs = await librarian.agents_librarian_retrieve(state["content"])
        ctx = "\n\n".join(d.page_content for d in docs) if docs else ""
        docs_retrieved = len(docs)
        logger.info(AGENTS_MANAGER_LOG_RETRIEVE_DONE.format(count=docs_retrieved))

    return {
        "phase": AGENTS_MANAGER_PHASE_2,
        "context": ctx,
        "active_agent": AGENTS_LIBRARIAN_AGENT_NAME,
        "messages": [
            {
                "phase": AGENTS_MANAGER_PHASE_2,
                "agent": AGENTS_LIBRARIAN_AGENT_NAME,
                "action": AGENTS_LIBRARIAN_ACTION_RETRIEVED,
                "docs_retrieved": docs_retrieved,
            }
        ],
    }


async def _agents_manager_architect_phase(state: AgentsState) -> dict:
    """Phase 3: plan drafting. On retries, uses the reflector's refined plan instead."""
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
        )
        logger.info(AGENTS_MANAGER_LOG_DRAFT_DONE.format(count=len(plan)))

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
    """Phase 4: reflector confidence audit."""

    logger.info(
        AGENTS_MANAGER_LOG_PHASE_GENERIC.format(
            phase=AGENTS_MANAGER_PHASE_4, description=AGENTS_MANAGER_DESC_PHASE_4
        )
    )
    logger.info(AGENTS_MANAGER_LOG_CRITIQUE_START)

    reflector = AgentsReflector()
    critique = await reflector.agents_reflector_critique(
        plan=state["plan"],
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

    confidence_val = float(critique.get("confidence", 0.0))
    # Reflector doesn't always set "approved" explicitly, so we also gate on confidence
    threshold = state.get("confidence_threshold") or CONFIDENCE_THRESHOLD
    approved_val = critique.get("approved") is True or confidence_val >= threshold

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
    """Phase 5: engineer executes the approved plan."""

    logger.info(
        AGENTS_MANAGER_LOG_PHASE_GENERIC.format(
            phase=AGENTS_MANAGER_PHASE_5, description=AGENTS_MANAGER_DESC_PHASE_5
        )
    )
    logger.info(AGENTS_MANAGER_LOG_EXECUTE_START)

    engineer = AgentsEngineer()
    result = await engineer.agents_engineer_execute(
        state["plan"],
        state.get("context") or "",
        verbosity=state.get("verbosity") or AGENTS_MANAGER_VERBOSITY_DEFAULT,
    )

    logger.info(
        AGENTS_MANAGER_LOG_EXECUTE_DONE.format(
            count=len(result),
            preview=result[:60].replace("\n", " "),
        )
    )

    return {
        "phase": AGENTS_MANAGER_PHASE_5,
        "result": result,
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
    """Phase 6: QA verification of the execution result."""

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
    """Bump retry counter before looping back to librarian."""

    return {"retry_count": state["retry_count"] + 1}


def _agents_manager_route_after_protocol(state: AgentsState) -> str:
    """Green means proceed; anything else kills the session."""

    return (
        AGENTS_MANAGER_NODE_TASK
        if state.get("protocol_status") == AGENTS_PROTOCOL_STATUS_GREEN
        else AGENTS_MANAGER_NODE_END_FAILED
    )


def _agents_manager_route_after_critique(state: AgentsState) -> str:
    """Approve on high confidence or explicit approval. Force-execute after max retries."""

    critique = state.get("critique")
    if not critique:
        return AGENTS_MANAGER_NODE_EXECUTE

    confidence = float(critique.get("confidence", 0.0))
    threshold = state.get("confidence_threshold") or CONFIDENCE_THRESHOLD
    approved = critique.get("approved") is True or confidence >= threshold
    if approved:
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
    """Pass through on success. On failure, retry or accept as-is if budget is blown."""

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
        self._graph = graph

    @classmethod
    async def agents_manager_create(cls) -> "AgentsManager":
        """Build the graph."""

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
        builder.add_edge(AGENTS_MANAGER_NODE_ARCHITECT, AGENTS_MANAGER_NODE_REVIEW)

        # After review: execute if approved, otherwise retry (force-execute after max retries)
        builder.add_conditional_edges(
            AGENTS_MANAGER_NODE_REVIEW,
            _agents_manager_route_after_critique,
            {
                AGENTS_MANAGER_NODE_EXECUTE: AGENTS_MANAGER_NODE_EXECUTE,
                AGENTS_MANAGER_NODE_RETRY: AGENTS_MANAGER_NODE_RETRY,
            },
        )

        builder.add_edge(AGENTS_MANAGER_NODE_EXECUTE, AGENTS_MANAGER_NODE_VERIFY)

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
        """Run the full pipeline synchronously and return a completed response."""

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
        status = (
            AGENTS_MANAGER_STATUS_FAILED
            if has_error and not has_result
            else AGENTS_MANAGER_STATUS_COMPLETED
        )

        # Classify the error for the API response
        error_code = None
        if has_error:
            err_msg = final_state.get("error", "")
            retry_count = final_state.get("retry_count", 0)
            confidence = final_state.get("confidence", 0.0)
            if (
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
        """Stream LangGraph events in real time for the Chainlit UI."""

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
            "confidence_threshold": confidence_threshold,
            "validator_confidence_threshold": validator_confidence_threshold,
            "max_retries_override": max_retries,
            "verbosity": verbosity or "standard",
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
