"""Optional LangSmith workspace scoping for trace ingest.

Free Personal-org LangSmith API keys are org-scoped and reject trace ingest
(HTTP 403) unless the request carries the workspace as an X-Tenant-Id header.
This module injects that header into the LangSmith client at startup, gated so
it is a complete no-op unless tracing is enabled and a workspace id is set.
"""

from __future__ import annotations

import logging

from src.core.core_config import CoreSettings

logger = logging.getLogger(__name__)

_PATCHED: bool = False

CORE_TRACING_HEADER: str = "X-Tenant-Id"
CORE_TRACING_LOG_ENABLED: str = "LangSmith workspace scoping enabled"
CORE_TRACING_LOG_UNAVAILABLE: str = "LangSmith not installed; workspace scoping skipped"


def core_tracing_configure(settings: CoreSettings) -> None:
    """Inject the LangSmith workspace header into the langsmith client.

    No-op unless tracing is enabled and a workspace id is configured. Applies a
    single idempotent monkeypatch to ``langsmith.Client.__init__`` that adds the
    ``X-Tenant-Id`` header so an org-scoped key can ingest traces.

    Args:
        settings: Active CoreSettings; the gate reads ``langsmith_enabled`` and
            ``langchain_workspace_id``.
    """

    global _PATCHED
    if _PATCHED:
        return
    if not (settings.langsmith_enabled and settings.langchain_workspace_id):
        return

    try:
        import langsmith
    except ImportError:
        logger.warning(CORE_TRACING_LOG_UNAVAILABLE)
        return

    workspace_id = settings.langchain_workspace_id
    _orig_init = langsmith.Client.__init__

    def _patched_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        _orig_init(self, *args, **kwargs)
        if hasattr(self, "session"):
            self.session.headers[CORE_TRACING_HEADER] = workspace_id

    langsmith.Client.__init__ = _patched_init  # type: ignore[method-assign]
    _PATCHED = True
    logger.info(CORE_TRACING_LOG_ENABLED)
