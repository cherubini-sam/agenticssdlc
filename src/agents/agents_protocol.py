"""Protocol gatekeeper: structural checks + optional probabilistic validation via LoRA."""

from __future__ import annotations

import logging

from langchain_core.runnables import RunnableLambda
from langchain_google_vertexai import ChatVertexAI

from src.agents.agents_base import AgentsBase
from src.agents.agents_utils import (
    AGENTS_ARCHITECT_REQUIRED_SECTIONS,
    AGENTS_KNOWN_PROTOCOL_SECTIONS,
    AGENTS_MANAGER_TELEMETRY_ROUTER,
    AGENTS_PROTOCOL_AGENT_NAME,
    AGENTS_PROTOCOL_BOOT_PHASE,
    AGENTS_PROTOCOL_CONTEXT_SCOPE,
    AGENTS_PROTOCOL_DECISION_ERROR,
    AGENTS_PROTOCOL_DECISION_GREEN,
    AGENTS_PROTOCOL_DOC_PATHS,
    AGENTS_PROTOCOL_FAIL_CLOSED_VIOLATION,
    AGENTS_PROTOCOL_GATEKEEPER_MODE_HEURISTIC,
    AGENTS_PROTOCOL_GATEKEEPER_MODE_LLM,
    AGENTS_PROTOCOL_LLM_MAX_OUTPUT_TOKENS,
    AGENTS_PROTOCOL_LLM_MAX_RETRIES,
    AGENTS_PROTOCOL_LLM_TEMPERATURE,
    AGENTS_PROTOCOL_LOG_BOOT_FAILED,
    AGENTS_PROTOCOL_LOG_BOOT_START,
    AGENTS_PROTOCOL_LOG_FAIL_CLOSED,
    AGENTS_PROTOCOL_LOG_FALLBACK_TRIGGERED,
    AGENTS_PROTOCOL_LOG_LLM_INVOKE,
    AGENTS_PROTOCOL_LOG_LLM_RESULT,
    AGENTS_PROTOCOL_LOG_NO_ENDPOINT,
    AGENTS_PROTOCOL_MAX_CONTENT_LENGTH,
    AGENTS_PROTOCOL_SECTION_PREAMBLE,
    AGENTS_PROTOCOL_STATUS_ERROR,
    AGENTS_PROTOCOL_STATUS_GREEN,
    AGENTS_PROTOCOL_THINKING_LEVEL,
    AGENTS_PROTOCOL_VIOLATION_EMPTY_CONTENT,
    AGENTS_PROTOCOL_VIOLATION_EMPTY_TASK,
    AGENTS_PROTOCOL_VIOLATION_EXCEEDS_LENGTH,
)
from src.api.middleware.api_middleware_observability import record_protocol_decision
from src.core.core_config import core_config_get_settings
from src.tuning.tuning_config import ProtocolDecision

logger = logging.getLogger(__name__)


class AgentsProtocol(AgentsBase):
    """Multi-layer gatekeeper: structural guard → LLM validation → deterministic fallbacks."""

    agent_name: str = AGENTS_PROTOCOL_AGENT_NAME
    role_doc_paths: list[str] = AGENTS_PROTOCOL_DOC_PATHS

    def __init__(self):
        """Initialize protocol agent with optional resilient gatekeeper chain.

        The gatekeeper LCEL chain is built only when TUNED_PROTOCOL_ENDPOINT_ID is
        configured in CoreSettings. Without an endpoint the instance falls back to
        deterministic heuristics for every validation request.
        """

        super().__init__()
        settings = core_config_get_settings()
        self._endpoint_id = settings.tuned_protocol_endpoint_id
        self._gatekeeper = (
            self._agents_protocol_build_gatekeeper(settings) if self._endpoint_id else None
        )

    def _agents_protocol_build_gatekeeper(self, settings) -> RunnableLambda:
        """Build resilient gatekeeper chain if endpoint configured.

        Args:
            settings: CoreSettings instance carrying GCP project, region, and model config.

        Returns:
            Resilient LCEL RunnableLambda chain with a structured-output LLM primary and
            two fallbacks: legacy heuristic then fail-closed.
        """

        protocol_llm = ChatVertexAI(
            model_name=settings.gemini_model,
            tuned_model_name=self._endpoint_id,
            project=settings.gcp_project_id,
            location=settings.gcp_region,
            temperature=AGENTS_PROTOCOL_LLM_TEMPERATURE,
            max_output_tokens=AGENTS_PROTOCOL_LLM_MAX_OUTPUT_TOKENS,
            max_retries=AGENTS_PROTOCOL_LLM_MAX_RETRIES,
        )

        structured = protocol_llm.with_structured_output(
            ProtocolDecision, include_raw=False, method="json_schema"  # type: ignore[arg-type]
        )

        resilient = structured.with_fallbacks(
            fallbacks=[
                RunnableLambda(self._agents_protocol_legacy_heuristic),  # type: ignore[arg-type]
                RunnableLambda(self._agents_protocol_fail_closed),  # type: ignore[arg-type]
            ],
            exceptions_to_handle=(Exception,),
        )

        return resilient  # type: ignore[return-value]

    async def agents_protocol_validate(self, task_id: str, content: str) -> dict:
        """Run structural guard then optional LLM semantic validation via the LCEL chain.

        Args:
            task_id: Unique identifier for the current workflow run.
            content: Raw user-submitted task string to validate.

        Returns:
            Dict with keys: protocol_status (str), violations (list[str]),
            boot_agent (str), boot_phase (int).
        """

        telemetry = {
            "active_agent": self.agent_name,
            "routed_by": AGENTS_MANAGER_TELEMETRY_ROUTER,
            "task_type": "boot_validation",
            "execution_mode": "readonly",
            "context_scope": AGENTS_PROTOCOL_CONTEXT_SCOPE,
            "thinking_level": AGENTS_PROTOCOL_THINKING_LEVEL,
        }
        self.logger.info(
            AGENTS_PROTOCOL_LOG_BOOT_START.format(task_id=task_id, telemetry=telemetry)
        )

        violations = self._agents_protocol_check_integrity(task_id=task_id, content=content)

        if violations:
            self.logger.error(AGENTS_PROTOCOL_LOG_BOOT_FAILED.format(violations=violations))
            record_protocol_decision(
                status=AGENTS_PROTOCOL_STATUS_ERROR,
                gatekeeper_mode=AGENTS_PROTOCOL_GATEKEEPER_MODE_HEURISTIC,
            )
            return {
                "protocol_status": AGENTS_PROTOCOL_STATUS_ERROR,
                "violations": violations,
                "boot_agent": AGENTS_PROTOCOL_AGENT_NAME,
                "boot_phase": AGENTS_PROTOCOL_BOOT_PHASE,
            }

        if self._gatekeeper:
            self.logger.info(AGENTS_PROTOCOL_LOG_LLM_INVOKE.format(task_id=task_id))
            decision = await self._agents_protocol_invoke_gatekeeper(content)
            return self._agents_protocol_map_decision(decision)

        self.logger.info(AGENTS_PROTOCOL_LOG_NO_ENDPOINT)
        return self._agents_protocol_map_legacy_result(
            self._agents_protocol_legacy_heuristic({"content": content})
        )

    async def _agents_protocol_invoke_gatekeeper(self, content: str) -> ProtocolDecision:
        """Invoke the resilient LCEL chain asynchronously. Fallbacks are built into the chain.

        Args:
            content: Task content to validate semantically via the LLM gatekeeper.

        Returns:
            ProtocolDecision with status and violations from the LLM or a fallback.
        """

        try:
            return await self._gatekeeper.ainvoke({"content": content})
        except Exception as e:
            self.logger.error(
                AGENTS_PROTOCOL_LOG_FALLBACK_TRIGGERED.format(
                    mode=AGENTS_PROTOCOL_GATEKEEPER_MODE_HEURISTIC, error=e
                )
            )
            return self._agents_protocol_legacy_heuristic({"content": content})

    def _agents_protocol_legacy_heuristic(self, input_dict: dict) -> ProtocolDecision:
        """Deterministic rule-based heuristic, wrapped as an LCEL-compatible function.

        Args:
            input_dict: Dict with key "content" (str) — the task content to check.

        Returns:
            ProtocolDecision based on structural integrity checks only.
        """

        content = input_dict.get("content", "")
        violations = self._agents_protocol_check_integrity(task_id="N/A", content=content)

        if violations:
            return ProtocolDecision(
                protocol_status=AGENTS_PROTOCOL_DECISION_ERROR,
                protocol_violations=violations,
            )

        return ProtocolDecision(
            protocol_status=AGENTS_PROTOCOL_DECISION_GREEN,
            protocol_violations=[],
        )

    def _agents_protocol_fail_closed(self, input_dict: dict) -> ProtocolDecision:
        """Ultimate safety net: always return ERROR on catastrophic failure. Never fail-open.

        Args:
            input_dict: Unused dict; kept for LCEL chain signature compatibility.

        Returns:
            ProtocolDecision with ERROR status and a fail-closed violation message.
        """

        self.logger.error(AGENTS_PROTOCOL_LOG_FAIL_CLOSED)
        return ProtocolDecision(
            protocol_status=AGENTS_PROTOCOL_DECISION_ERROR,
            protocol_violations=[AGENTS_PROTOCOL_FAIL_CLOSED_VIOLATION],
        )

    def _agents_protocol_map_decision(self, decision: ProtocolDecision) -> dict:
        """Map a ProtocolDecision to AgentsState format and record observability metrics.

        Args:
            decision: ProtocolDecision returned by the LLM gatekeeper chain.

        Returns:
            Dict in AgentsState format with keys: protocol_status, violations,
            boot_agent, boot_phase.
        """

        is_error = decision.protocol_status == AGENTS_PROTOCOL_DECISION_ERROR
        state_status = AGENTS_PROTOCOL_STATUS_ERROR if is_error else AGENTS_PROTOCOL_STATUS_GREEN

        self.logger.info(
            AGENTS_PROTOCOL_LOG_LLM_RESULT.format(
                status=state_status, mode=AGENTS_PROTOCOL_GATEKEEPER_MODE_LLM
            )
        )
        record_protocol_decision(
            status=state_status, gatekeeper_mode=AGENTS_PROTOCOL_GATEKEEPER_MODE_LLM
        )

        return {
            "protocol_status": state_status,
            "violations": decision.protocol_violations,
            "boot_agent": AGENTS_PROTOCOL_AGENT_NAME,
            "boot_phase": AGENTS_PROTOCOL_BOOT_PHASE,
        }

    def _agents_protocol_map_legacy_result(self, decision: ProtocolDecision) -> dict:
        """Map a legacy heuristic result to AgentsState format and record observability.

        Args:
            decision: ProtocolDecision produced by the deterministic heuristic path.

        Returns:
            Dict in AgentsState format with keys: protocol_status, violations,
            boot_agent, boot_phase.
        """

        is_error = decision.protocol_status == AGENTS_PROTOCOL_DECISION_ERROR
        state_status = AGENTS_PROTOCOL_STATUS_ERROR if is_error else AGENTS_PROTOCOL_STATUS_GREEN

        self.logger.info(
            AGENTS_PROTOCOL_LOG_LLM_RESULT.format(
                status=state_status, mode=AGENTS_PROTOCOL_GATEKEEPER_MODE_HEURISTIC
            )
        )
        record_protocol_decision(
            status=state_status, gatekeeper_mode=AGENTS_PROTOCOL_GATEKEEPER_MODE_HEURISTIC
        )

        return {
            "protocol_status": state_status,
            "violations": decision.protocol_violations,
            "boot_agent": AGENTS_PROTOCOL_AGENT_NAME,
            "boot_phase": AGENTS_PROTOCOL_BOOT_PHASE,
        }

    def _agents_protocol_check_integrity(self, task_id: str, content: str) -> list[str]:
        """Structural guard: check for empty inputs and length bounds.

        Args:
            task_id: Workflow run ID; checked for empty or whitespace-only value.
            content: User task string; checked for empty value and maximum length.

        Returns:
            List of violation strings. An empty list means the request passed all
            structural checks.
        """

        violations: list[str] = []

        if not task_id or not task_id.strip():
            violations.append(AGENTS_PROTOCOL_VIOLATION_EMPTY_TASK)

        if not content or not content.strip():
            violations.append(AGENTS_PROTOCOL_VIOLATION_EMPTY_CONTENT)

        if content and len(content) > AGENTS_PROTOCOL_MAX_CONTENT_LENGTH:
            violations.append(
                AGENTS_PROTOCOL_VIOLATION_EXCEEDS_LENGTH.format(
                    limit=AGENTS_PROTOCOL_MAX_CONTENT_LENGTH, actual=len(content)
                )
            )

        return violations


def agents_protocol_sections_validate_preamble() -> list[str]:
    """Return the subset of required markers NOT present in the canonical preamble.

    Fails the invariant that every section listed in
    ``AGENTS_ARCHITECT_REQUIRED_SECTIONS`` and ``AGENTS_KNOWN_PROTOCOL_SECTIONS``
    must be literally present in ``AGENTS_PROTOCOL_SECTION_PREAMBLE``. An empty
    return list means the preamble satisfies the guards; a non-empty list is a
    configuration bug and every workflow will refuse until fixed.

    Returns:
        List of marker strings expected by the guards but absent from the
        preamble. Empty when the invariant holds.
    """

    required = set(AGENTS_ARCHITECT_REQUIRED_SECTIONS) | set(AGENTS_KNOWN_PROTOCOL_SECTIONS)
    return [marker for marker in required if marker not in AGENTS_PROTOCOL_SECTION_PREAMBLE]
