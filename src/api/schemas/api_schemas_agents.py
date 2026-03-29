"""Response models for the /agents/status endpoint."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApiSchemasAgentStatus(BaseModel):
    name: str
    model: str
    status: str  # "active" | "idle"
    last_invoked: Optional[datetime] = None


class ApiSchemasSystemStatus(BaseModel):
    version: str
    uptime_s: float
    vector_store: str  # "qdrant" | "chroma"
    agents: list[ApiSchemasAgentStatus]
