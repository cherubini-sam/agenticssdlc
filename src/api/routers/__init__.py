"""FastAPI routers: tasks, agents, and health endpoints."""

from src.api.routers.api_routers_agents import router as agents_router
from src.api.routers.api_routers_health import router as health_router
from src.api.routers.api_routers_tasks import router as tasks_router

__all__ = [
    "agents_router",
    "health_router",
    "tasks_router",
]
