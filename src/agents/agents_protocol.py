"""Boot validation gate that runs deterministic input checks before any LLM work starts."""

from __future__ import annotations

import logging

from src.agents.agents_utils import (
    AGENTS_MANAGER_TELEMETRY_ROUTER,
    AGENTS_PROTOCOL_AGENT_NAME,
    AGENTS_PROTOCOL_BOOT_PHASE,
    AGENTS_PROTOCOL_CONTEXT_SCOPE,
    AGENTS_PROTOCOL_LOG_BOOT_FAILED,
    AGENTS_PROTOCOL_LOG_BOOT_PASSED,
    AGENTS_PROTOCOL_LOG_BOOT_START,
    AGENTS_PROTOCOL_MAX_CONTENT_LENGTH,
    AGENTS_PROTOCOL_STATUS_ERROR,
    AGENTS_PROTOCOL_STATUS_GREEN,
    AGENTS_PROTOCOL_THINKING_LEVEL,
    AGENTS_PROTOCOL_VIOLATION_EMPTY_CONTENT,
    AGENTS_PROTOCOL_VIOLATION_EMPTY_TASK,
    AGENTS_PROTOCOL_VIOLATION_EXCEEDS_LENGTH,
)

logger = logging.getLogger(__name__)


class AgentsProtocol:
    """Fail-closed input validator. No LLM calls, just deterministic integrity checks."""

    agent_name: str = AGENTS_PROTOCOL_AGENT_NAME

    def __init__(self):
        self.logger = logging.getLogger(self.agent_name)

    async def agents_protocol_validate(self, task_id: str, content: str) -> dict:
        """Run pre-flight checks on task_id and content. Returns status + any violations."""
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
            return {
                "protocol_status": AGENTS_PROTOCOL_STATUS_ERROR,
                "violations": violations,
                "boot_agent": AGENTS_PROTOCOL_AGENT_NAME,
                "boot_phase": AGENTS_PROTOCOL_BOOT_PHASE,
            }

        self.logger.info(
            AGENTS_PROTOCOL_LOG_BOOT_PASSED.format(status=AGENTS_PROTOCOL_STATUS_GREEN)
        )
        return {
            "protocol_status": AGENTS_PROTOCOL_STATUS_GREEN,
            "violations": [],
            "boot_agent": AGENTS_PROTOCOL_AGENT_NAME,
            "boot_phase": AGENTS_PROTOCOL_BOOT_PHASE,
        }

    def _agents_protocol_check_integrity(self, task_id: str, content: str) -> list[str]:
        """Check for empty inputs and length bounds. Returns list of violation strings."""

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
