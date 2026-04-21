"""Startup warning fires when Grafana remote-write URL is empty."""

from __future__ import annotations

from api.api_utils import API_MAIN_LOG_GRAFANA_DISABLED, API_MAIN_LOG_GRAFANA_ENABLED


class TestGrafanaStartupMessages:
    """Log templates referenced by the lifespan hook."""

    def test_disabled_template_names_panels(self) -> None:
        """The disabled warning mentions each affected dashboard panel."""

        assert "Active Workflows" in API_MAIN_LOG_GRAFANA_DISABLED
        assert "Live Confidence" in API_MAIN_LOG_GRAFANA_DISABLED
        assert "Call Rate & Error Rate" in API_MAIN_LOG_GRAFANA_DISABLED

    def test_enabled_template_accepts_url_host(self) -> None:
        """The enabled log accepts a url_host placeholder without credentials."""

        formatted = API_MAIN_LOG_GRAFANA_ENABLED.format(url_host="prometheus-prod.grafana.net")
        assert "prometheus-prod.grafana.net" in formatted
        assert "api_key" not in formatted.lower()
        assert "instance_id" not in formatted.lower()
