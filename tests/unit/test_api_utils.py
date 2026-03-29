"""Sanity checks for api_utils constants types, values, uniqueness."""

from __future__ import annotations


class TestApiUtilsConstants:

    def test_open_paths_is_frozenset(self) -> None:
        from api.api_utils import API_MIDDLEWARE_AUTH_OPEN_PATHS

        assert isinstance(API_MIDDLEWARE_AUTH_OPEN_PATHS, frozenset)
        assert "/health" in API_MIDDLEWARE_AUTH_OPEN_PATHS

    def test_metrics_paths_is_frozenset(self) -> None:
        from api.api_utils import API_MIDDLEWARE_AUTH_METRICS_PATHS

        assert isinstance(API_MIDDLEWARE_AUTH_METRICS_PATHS, frozenset)
        assert "/metrics" in API_MIDDLEWARE_AUTH_METRICS_PATHS

    def test_ratelimit_exempt_paths_is_frozenset(self) -> None:
        from api.api_utils import API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS

        assert isinstance(API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS, frozenset)
        assert "/health" in API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS

    def test_ratelimit_window_is_positive(self) -> None:
        from api.api_utils import API_MIDDLEWARE_RATELIMIT_WINDOW

        assert isinstance(API_MIDDLEWARE_RATELIMIT_WINDOW, float)
        assert API_MIDDLEWARE_RATELIMIT_WINDOW > 0

    def test_app_title_is_string(self) -> None:
        from api.api_utils import API_APP_TITLE

        assert isinstance(API_APP_TITLE, str)
        assert len(API_APP_TITLE) > 0

    def test_app_version_is_string(self) -> None:
        from api.api_utils import API_APP_VERSION

        assert isinstance(API_APP_VERSION, str)
        assert len(API_APP_VERSION) > 0

    def test_cors_allow_methods_is_list(self) -> None:
        from api.api_utils import API_CORS_ALLOW_METHODS

        assert isinstance(API_CORS_ALLOW_METHODS, list)
        assert "GET" in API_CORS_ALLOW_METHODS
        assert "POST" in API_CORS_ALLOW_METHODS

    def test_cors_allow_headers_is_list(self) -> None:
        from api.api_utils import API_CORS_ALLOW_HEADERS

        assert isinstance(API_CORS_ALLOW_HEADERS, list)
        assert len(API_CORS_ALLOW_HEADERS) > 0

    def test_metrics_mount_path_is_string(self) -> None:
        from api.api_utils import API_METRICS_MOUNT_PATH

        assert isinstance(API_METRICS_MOUNT_PATH, str)
        assert API_METRICS_MOUNT_PATH.startswith("/")

    def test_agent_status_labels_are_strings(self) -> None:
        from api.api_utils import API_AGENT_STATUS_ACTIVE, API_AGENT_STATUS_IDLE

        assert isinstance(API_AGENT_STATUS_ACTIVE, str)
        assert isinstance(API_AGENT_STATUS_IDLE, str)
        assert API_AGENT_STATUS_ACTIVE != API_AGENT_STATUS_IDLE

    def test_ratelimit_expose_headers_is_list(self) -> None:
        from api.api_utils import API_RATELIMIT_EXPOSE_HEADERS

        assert isinstance(API_RATELIMIT_EXPOSE_HEADERS, list)
        assert len(API_RATELIMIT_EXPOSE_HEADERS) > 0

    def test_prometheus_metrics_names_are_strings(self) -> None:
        from api.api_utils import (
            API_PROMETHEUS_AGENT_CALLS_METRIC,
            API_PROMETHEUS_AGENT_CONFIDENCE_METRIC,
            API_PROMETHEUS_AGENT_LATENCY_METRIC,
        )

        for metric in [
            API_PROMETHEUS_AGENT_CALLS_METRIC,
            API_PROMETHEUS_AGENT_LATENCY_METRIC,
            API_PROMETHEUS_AGENT_CONFIDENCE_METRIC,
        ]:
            assert isinstance(metric, str)
            assert metric.startswith("agentics_sdlc_")

    def test_observability_skip_paths_is_frozenset(self) -> None:
        from api.api_utils import API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS

        assert isinstance(API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS, frozenset)
        assert "/metrics" in API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS

    def test_health_status_constants_are_distinct(self) -> None:
        from api.api_utils import (
            API_HEALTH_STATUS_ALIVE,
            API_HEALTH_STATUS_HEALTHY,
            API_HEALTH_STATUS_NOT_READY,
            API_HEALTH_STATUS_READY,
        )

        statuses = [
            API_HEALTH_STATUS_HEALTHY,
            API_HEALTH_STATUS_READY,
            API_HEALTH_STATUS_NOT_READY,
            API_HEALTH_STATUS_ALIVE,
        ]
        assert len(set(statuses)) == len(statuses)
        assert all(isinstance(s, str) for s in statuses)

    def test_router_agents_names_are_strings(self) -> None:
        from api.api_utils import (
            API_ROUTERS_AGENTS_ARCHITECT,
            API_ROUTERS_AGENTS_ENGINEER,
            API_ROUTERS_AGENTS_LIBRARIAN,
            API_ROUTERS_AGENTS_MANAGER,
            API_ROUTERS_AGENTS_REFLECTOR,
            API_ROUTERS_AGENTS_VALIDATOR,
        )

        agents = [
            API_ROUTERS_AGENTS_MANAGER,
            API_ROUTERS_AGENTS_ARCHITECT,
            API_ROUTERS_AGENTS_ENGINEER,
            API_ROUTERS_AGENTS_VALIDATOR,
            API_ROUTERS_AGENTS_LIBRARIAN,
            API_ROUTERS_AGENTS_REFLECTOR,
        ]
        assert len(set(agents)) == len(agents)
        assert all(isinstance(a, str) and len(a) > 0 for a in agents)

    def test_service_name_is_non_empty(self) -> None:
        from api.api_utils import API_SERVICE_NAME

        assert isinstance(API_SERVICE_NAME, str)
        assert len(API_SERVICE_NAME) > 0

    def test_default_ratelimit_rpm_is_positive(self) -> None:
        from api.api_utils import API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM

        assert isinstance(API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM, int)
        assert API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM > 0
