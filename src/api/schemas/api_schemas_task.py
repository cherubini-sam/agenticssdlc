"""Request/response schemas for the task execution endpoint."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from src.api.api_utils import (
    API_SCHEMAS_TASK_CONTENT_BLANK_ERROR,
    API_SCHEMAS_TASK_CONTENT_CONTROL_CHAR_PATTERN,
    API_SCHEMAS_TASK_CONTENT_MAX_LENGTH,
    API_SCHEMAS_TASK_CONTEXT_MAX_BYTES,
    API_SCHEMAS_TASK_CONTEXT_TOO_LARGE_ERROR,
)


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
    AGENT_EXECUTION_REFUSED = "AGENT_004"
    RAG_RETRIEVAL_FAILED = "RAG_001"
    WORKFLOW_TIMEOUT = "WF_001"
    WORKFLOW_MAX_RETRIES = "WF_002"
    RATE_LIMIT_EXCEEDED = "RATE_001"
    INTERNAL_ERROR = "SYS_001"


class ApiSchemasTaskRequest(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(
        ...,
        min_length=1,
        max_length=API_SCHEMAS_TASK_CONTENT_MAX_LENGTH,
        description="Task description or query",
    )
    context: dict = Field(default_factory=dict)
    priority: Literal["low", "normal", "high"] = "normal"

    @field_validator("content")
    @classmethod
    def not_blank(cls, content: str) -> str:
        """Catch whitespace-only strings and strip prompt-injection-prone control characters."""

        stripped = content.strip()
        if not stripped:
            raise ValueError(API_SCHEMAS_TASK_CONTENT_BLANK_ERROR)
        # Remove ASCII control characters (except newline/tab which are valid in task content)
        sanitized = re.sub(API_SCHEMAS_TASK_CONTENT_CONTROL_CHAR_PATTERN, "", stripped)
        return sanitized

    @field_validator("context")
    @classmethod
    def context_size_limit(cls, context: dict) -> dict:
        """Reject oversized context objects that could cause DoS or log bloat."""

        serialized = json.dumps(context)
        if len(serialized) > API_SCHEMAS_TASK_CONTEXT_MAX_BYTES:
            raise ValueError(API_SCHEMAS_TASK_CONTEXT_TOO_LARGE_ERROR)
        return context


class ApiSchemasTaskResponse(BaseModel):
    task_id: str
    status: Literal["completed", "failed"]
    result: Optional[str]
    artifact_uri: Optional[str] = None
    phases_completed: list[ApiSchemasWorkflowPhase]
    confidence: float
    latency_ms: float
    agent_trace: list[dict]
    error: Optional[str] = None
    error_code: Optional[ApiSchemasErrorCode] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
