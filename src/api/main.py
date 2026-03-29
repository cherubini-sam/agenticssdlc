"""FastAPI application factory and startup lifecycle."""

from __future__ import annotations

import logging
import time
import warnings
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from src.agents.agents_manager import AgentsManager
from src.analytics.analytics_bigquery_ingest import AnalyticsBigqueryIngest
from src.analytics.analytics_supabase_ingest import AnalyticsSupabaseIngest
from src.api.api_utils import (
    API_APP_DESCRIPTION,
    API_APP_TITLE,
    API_APP_VERSION,
    API_CORS_ALLOW_HEADERS,
    API_CORS_ALLOW_METHODS,
    API_GCP_PROJECT_DEV_SENTINEL,
    API_MAIN_LOG_BQ_ERROR,
    API_MAIN_LOG_BQ_START,
    API_MAIN_LOG_READY,
    API_MAIN_LOG_SHUTDOWN,
    API_MAIN_LOG_SUPABASE_ERROR,
    API_MAIN_LOG_SUPABASE_START,
    API_MAIN_STATUS_DISABLED,
    API_MAIN_STATUS_ENABLED,
    API_METRICS_MOUNT_PATH,
    API_RATELIMIT_EXPOSE_HEADERS,
    API_WARNINGS_LANGCHAIN_IGNORE,
)
from src.api.middleware.api_middleware_auth import ApiMiddlewareApiKey
from src.api.middleware.api_middleware_observability import ApiMiddlewareObservability
from src.api.middleware.api_middleware_ratelimit import ApiMiddlewareRateLimit
from src.api.routers import api_routers_agents, api_routers_health, api_routers_tasks
from src.core.core_config import core_config_get_settings as get_settings
from src.core.core_config import core_config_validate_settings as validate_settings
from src.core.core_logging import core_logging_setup_logging as configure_logging
from src.rag.rag_vector_store import RagVectorStore

# langchain emits noisy deprecation warnings on import
warnings.filterwarnings("ignore", message=API_WARNINGS_LANGCHAIN_IGNORE)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Boot everything we need before the first request, tear down on shutdown."""

    settings = get_settings()
    configure_logging(settings.log_level)
    validate_settings(settings)

    # BigQuery audit logging: skip for the dev sentinel project
    if settings.gcp_project_id and settings.gcp_project_id != API_GCP_PROJECT_DEV_SENTINEL:
        try:
            logger.info(API_MAIN_LOG_BQ_START)
            bq = AnalyticsBigqueryIngest()
            await bq.analytics_bigquery_validate_schema()
            app.state.audit_logger = bq
        except Exception as bq_exc:
            logger.warning(API_MAIN_LOG_BQ_ERROR.format(error=bq_exc))
            app.state.audit_logger = None
    else:
        app.state.audit_logger = None

    # Supabase audit logging: always attempt, degrades gracefully if creds are missing
    logger.info(API_MAIN_LOG_SUPABASE_START)
    supabase = AnalyticsSupabaseIngest()
    if supabase.is_enabled:
        try:
            await supabase.analytics_supabase_validate_connection()
        except Exception as sb_exc:
            logger.warning(API_MAIN_LOG_SUPABASE_ERROR.format(error=sb_exc))
    app.state.supabase_logger = supabase

    app.state.manager = await AgentsManager.agents_manager_create()
    app.state.vector_store = await RagVectorStore.rag_vector_store_create()
    app.state.start_time = time.time()

    auth_status = (
        API_MAIN_STATUS_ENABLED if settings.agentics_sdlc_api_key else API_MAIN_STATUS_DISABLED
    )
    logger.info(
        API_MAIN_LOG_READY.format(
            model=settings.gemini_model,
            vector=app.state.vector_store.primary,
            auth=auth_status,
        )
    )
    yield
    logger.info(API_MAIN_LOG_SHUTDOWN)


def create_app() -> FastAPI:
    """Wire up middleware, mount Prometheus, register routers."""

    app = FastAPI(
        title=API_APP_TITLE,
        description=API_APP_DESCRIPTION,
        version=API_APP_VERSION,
        lifespan=lifespan,
    )

    _origins = [o.strip() for o in get_settings().allowed_origins.split(",") if o.strip()]

    # Middleware order matters: outermost runs first on the request path.
    # Observability wraps everything so we get timing even for auth rejections.
    app.add_middleware(ApiMiddlewareObservability)
    app.add_middleware(ApiMiddlewareApiKey)
    app.add_middleware(ApiMiddlewareRateLimit, rpm=get_settings().rate_limit_rpm)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_methods=API_CORS_ALLOW_METHODS,
        allow_headers=API_CORS_ALLOW_HEADERS,
        expose_headers=API_RATELIMIT_EXPOSE_HEADERS,
        # Only send cookies when origins are explicitly listed
        allow_credentials=_origins != ["*"],
    )

    metrics_app = make_asgi_app()
    app.mount(API_METRICS_MOUNT_PATH, metrics_app)

    app.include_router(api_routers_health.router)
    app.include_router(api_routers_tasks.router)
    app.include_router(api_routers_agents.router)

    return app


app = create_app()
