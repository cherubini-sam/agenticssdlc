"""Sanity checks for api_utils constants types, values, uniqueness."""

from __future__ import annotations

from api.api_utils import (
    API_AGENT_STATUS_ACTIVE,
    API_AGENT_STATUS_IDLE,
    API_APP_TITLE,
    API_APP_VERSION,
    API_CORS_ALLOW_HEADERS,
    API_CORS_ALLOW_METHODS,
    API_HEALTH_STATUS_ALIVE,
    API_HEALTH_STATUS_HEALTHY,
    API_HEALTH_STATUS_NOT_READY,
    API_HEALTH_STATUS_READY,
    API_METRICS_MOUNT_PATH,
    API_MIDDLEWARE_AUTH_METRICS_PATHS,
    API_MIDDLEWARE_AUTH_OPEN_PATHS,
    API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS,
    API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM,
    API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS,
    API_MIDDLEWARE_RATELIMIT_WINDOW,
    API_PROMETHEUS_AGENT_CALLS_METRIC,
    API_PROMETHEUS_AGENT_CONFIDENCE_METRIC,
    API_PROMETHEUS_AGENT_LATENCY_METRIC,
    API_RATELIMIT_EXPOSE_HEADERS,
    API_ROUTERS_AGENTS_ARCHITECT,
    API_ROUTERS_AGENTS_ENGINEER,
    API_ROUTERS_AGENTS_LIBRARIAN,
    API_ROUTERS_AGENTS_MANAGER,
    API_ROUTERS_AGENTS_REFLECTOR,
    API_ROUTERS_AGENTS_VALIDATOR,
    API_SERVICE_NAME,
)


class TestApiUtilsConstants:
    """Smoke tests for api_utils constants — types, values, and uniqueness."""

    def test_open_paths_is_frozenset(self) -> None:
        """AUTH_OPEN_PATHS is a frozenset containing /health."""

        assert isinstance(API_MIDDLEWARE_AUTH_OPEN_PATHS, frozenset)
        assert "/health" in API_MIDDLEWARE_AUTH_OPEN_PATHS

    def test_metrics_paths_is_frozenset(self) -> None:
        """AUTH_METRICS_PATHS is a frozenset containing /metrics."""

        assert isinstance(API_MIDDLEWARE_AUTH_METRICS_PATHS, frozenset)
        assert "/metrics" in API_MIDDLEWARE_AUTH_METRICS_PATHS

    def test_ratelimit_exempt_paths_is_frozenset(self) -> None:
        """RATELIMIT_EXEMPT_PATHS is a frozenset containing /health."""

        assert isinstance(API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS, frozenset)
        assert "/health" in API_MIDDLEWARE_RATELIMIT_EXEMPT_PATHS

    def test_ratelimit_window_is_positive(self) -> None:
        """Rate-limit window is a positive float."""

        assert isinstance(API_MIDDLEWARE_RATELIMIT_WINDOW, float)
        assert API_MIDDLEWARE_RATELIMIT_WINDOW > 0

    def test_app_title_is_string(self) -> None:
        """App title is a non-empty string."""

        assert isinstance(API_APP_TITLE, str)
        assert len(API_APP_TITLE) > 0

    def test_app_version_is_string(self) -> None:
        """App version is a non-empty string."""

        assert isinstance(API_APP_VERSION, str)
        assert len(API_APP_VERSION) > 0

    def test_cors_allow_methods_is_list(self) -> None:
        """CORS allowed methods list includes GET and POST."""

        assert isinstance(API_CORS_ALLOW_METHODS, list)
        assert "GET" in API_CORS_ALLOW_METHODS
        assert "POST" in API_CORS_ALLOW_METHODS

    def test_cors_allow_headers_is_list(self) -> None:
        """CORS allowed headers list is non-empty."""

        assert isinstance(API_CORS_ALLOW_HEADERS, list)
        assert len(API_CORS_ALLOW_HEADERS) > 0

    def test_metrics_mount_path_is_string(self) -> None:
        """Metrics mount path is a string starting with '/'."""

        assert isinstance(API_METRICS_MOUNT_PATH, str)
        assert API_METRICS_MOUNT_PATH.startswith("/")

    def test_agent_status_labels_are_strings(self) -> None:
        """Active and idle status labels are distinct non-empty strings."""

        assert isinstance(API_AGENT_STATUS_ACTIVE, str)
        assert isinstance(API_AGENT_STATUS_IDLE, str)
        assert API_AGENT_STATUS_ACTIVE != API_AGENT_STATUS_IDLE

    def test_ratelimit_expose_headers_is_list(self) -> None:
        """Rate-limit expose headers list is non-empty."""

        assert isinstance(API_RATELIMIT_EXPOSE_HEADERS, list)
        assert len(API_RATELIMIT_EXPOSE_HEADERS) > 0

    def test_prometheus_metrics_names_are_strings(self) -> None:
        """All Prometheus metric name constants are strings prefixed with 'agentics_sdlc_'."""

        for metric in [
            API_PROMETHEUS_AGENT_CALLS_METRIC,
            API_PROMETHEUS_AGENT_LATENCY_METRIC,
            API_PROMETHEUS_AGENT_CONFIDENCE_METRIC,
        ]:
            assert isinstance(metric, str)
            assert metric.startswith("agentics_sdlc_")

    def test_observability_skip_paths_is_frozenset(self) -> None:
        """Observability skip-paths frozenset includes /metrics."""

        assert isinstance(API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS, frozenset)
        assert "/metrics" in API_MIDDLEWARE_OBSERVABILITY_SKIP_PATHS

    def test_health_status_constants_are_distinct(self) -> None:
        """The four health status strings are all distinct."""

        statuses = [
            API_HEALTH_STATUS_HEALTHY,
            API_HEALTH_STATUS_READY,
            API_HEALTH_STATUS_NOT_READY,
            API_HEALTH_STATUS_ALIVE,
        ]
        assert len(set(statuses)) == len(statuses)
        assert all(isinstance(s, str) for s in statuses)

    def test_router_agents_names_are_strings(self) -> None:
        """All router agent name constants are distinct non-empty strings."""

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
        """Service name constant is a non-empty string."""

        assert isinstance(API_SERVICE_NAME, str)
        assert len(API_SERVICE_NAME) > 0

    def test_default_ratelimit_rpm_is_positive(self) -> None:
        """Default rate-limit RPM is a positive integer."""

        assert isinstance(API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM, int)
        assert API_MIDDLEWARE_RATELIMIT_DEFAULT_RPM > 0
