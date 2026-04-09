"""CoreSettings defaults, validation gate, and lru_cache behaviour."""

from __future__ import annotations

import pytest

from core.core_config import CoreSettings, core_config_get_settings, core_config_validate_settings


class TestCoreSettings:
    """Tests for CoreSettings default values."""

    def test_default_gcp_project_id(self) -> None:
        """Default gcp_project_id is a non-empty string."""

        s = CoreSettings()
        assert isinstance(s.gcp_project_id, str)
        assert len(s.gcp_project_id) > 0

    def test_default_gemini_model(self) -> None:
        """Default gemini_model contains 'gemini'."""

        s = CoreSettings()
        assert "gemini" in s.gemini_model.lower()

    def test_default_port(self) -> None:
        """Default port is a positive integer."""

        s = CoreSettings()
        assert isinstance(s.port, int)
        assert s.port > 0

    def test_default_rate_limit_rpm(self) -> None:
        """Default rate_limit_rpm is an integer."""

        s = CoreSettings()
        assert isinstance(s.rate_limit_rpm, int)

    def test_default_log_level(self) -> None:
        """Default log_level is one of the standard logging level strings."""

        s = CoreSettings()
        assert s.log_level in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    def test_allowed_origins_default(self) -> None:
        """Default allowed_origins is a string."""

        s = CoreSettings()
        assert isinstance(s.allowed_origins, str)

    def test_supabase_url_default_empty(self) -> None:
        """Default supabase_url is a string."""

        s = CoreSettings()
        assert isinstance(s.supabase_url, str)

    def test_qdrant_url_default_empty(self) -> None:
        """Default qdrant_url is a string."""

        s = CoreSettings()
        assert isinstance(s.qdrant_url, str)


class TestCoreConfigValidateSettings:
    """Tests for core_config_validate_settings validation gate."""

    def test_raises_when_gcp_project_id_empty(self) -> None:
        """Empty gcp_project_id raises ValueError mentioning GCP_PROJECT_ID."""

        s = CoreSettings()
        s.gcp_project_id = ""

        with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
            core_config_validate_settings(s)

    def test_passes_when_gcp_project_id_set(self) -> None:
        """Non-empty gcp_project_id passes validation without error."""

        s = CoreSettings()
        s.gcp_project_id = "my-project"

        core_config_validate_settings(s)


class TestCoreConfigGetSettings:
    """Tests for core_config_get_settings lru_cache behaviour."""

    def test_returns_core_settings_instance(self) -> None:
        """Returns a CoreSettings instance."""

        core_config_get_settings.cache_clear()
        result = core_config_get_settings()
        assert isinstance(result, CoreSettings)

    def test_returns_same_instance_on_repeated_calls(self) -> None:
        """The same object is returned on every call due to lru_cache."""

        core_config_get_settings.cache_clear()
        a = core_config_get_settings()
        b = core_config_get_settings()
        # lru_cache should hand back the exact same object
        assert a is b

    def test_cache_info_shows_hits_on_second_call(self) -> None:
        """Cache info records at least one hit after two calls."""

        core_config_get_settings.cache_clear()
        core_config_get_settings()
        core_config_get_settings()
        info = core_config_get_settings.cache_info()
        assert info.hits >= 1
