"""Request/response schemas for the task execution endpoint."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ApiSchemasAgentType(str, Enum):
    """String enum so agents serialize cleanly in JSON responses."""

    MANAGER = "manager"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    VALIDATOR = "validator"
    LIBRARIAN = "librarian"
    REFLECTOR = "reflector"


class ApiSchemasWorkflowPhase(int, Enum):
    """The six mandatory phases, in execution order."""

    TASK = 1  # MANAGER confirms task boundary
    CONTEXT = 2  # LIBRARIAN + ARCHITECT retrieve context, draft plan
    PLAN = 3  # ARCHITECT finalizes structured plan
    CRITIQUE = 4  # REFLECTOR runs confidence audit
    EXECUTE = 5  # ENGINEER implements approved plan
    VERIFY = 6  # VALIDATOR does QA


class ApiSchemasErrorCode(str, Enum):
    """Stable codes clients can match on without parsing human-readable messages."""

    AGENT_QUOTA_EXHAUSTED = "AGENT_001"
    AGENT_EXECUTION_FAILED = "AGENT_002"
    AGENT_CONFIDENCE_LOW = "AGENT_003"
    RAG_RETRIEVAL_FAILED = "RAG_001"
    WORKFLOW_TIMEOUT = "WF_001"
    WORKFLOW_MAX_RETRIES = "WF_002"
    RATE_LIMIT_EXCEEDED = "RATE_001"
    INTERNAL_ERROR = "SYS_001"


class ApiSchemasTaskRequest(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(
        ..., min_length=1, max_length=4096, description="Task description or query"
    )
    context: dict = Field(default_factory=dict)
    priority: Literal["low", "normal", "high"] = "normal"

    @field_validator("content")
    @classmethod
    def not_blank(cls, v: str) -> str:
        """Catch whitespace-only strings that pass the min_length check."""

        stripped = v.strip()
        if not stripped:
            raise ValueError("content cannot be blank")
        return stripped


class ApiSchemasTaskResponse(BaseModel):
    task_id: str
    status: Literal["completed", "failed"]
    result: Optional[str]
    phases_completed: list[ApiSchemasWorkflowPhase]
    confidence: float
    latency_ms: float
    agent_trace: list[dict]
    error: Optional[str] = None
    error_code: Optional[ApiSchemasErrorCode] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
