"""core_llm_get_llm tier dispatch and cache behavior."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.core_llm import core_llm_get_llm


@pytest.fixture(autouse=True)
def _clear_llm_cache():
    core_llm_get_llm.cache_clear()
    yield
    core_llm_get_llm.cache_clear()


def _settings_stub(model_high: str = "gemini-2.5-pro", model_low: str = "gemini-2.5-flash"):
    s = MagicMock()
    s.gemini_model_high = model_high
    s.gemini_model_low = model_low
    s.gcp_project_id = "test-project"
    s.gcp_region = "us-central1"
    return s


class TestCoreLlmTierDispatch:
    """core_llm_get_llm resolves model_name from the requested tier."""

    def test_high_tier_uses_gemini_model_high(self) -> None:
        with (
            patch("core.core_llm.get_settings", return_value=_settings_stub()),
            patch("core.core_llm.ChatVertexAI") as mock_cls,
        ):
            core_llm_get_llm(tier="high")
            kwargs = mock_cls.call_args.kwargs
            assert kwargs["model_name"] == "gemini-2.5-pro"

    def test_low_tier_uses_gemini_model_low(self) -> None:
        with (
            patch("core.core_llm.get_settings", return_value=_settings_stub()),
            patch("core.core_llm.ChatVertexAI") as mock_cls,
        ):
            core_llm_get_llm(tier="low")
            kwargs = mock_cls.call_args.kwargs
            assert kwargs["model_name"] == "gemini-2.5-flash"

    def test_default_tier_is_low(self) -> None:
        with (
            patch("core.core_llm.get_settings", return_value=_settings_stub()),
            patch("core.core_llm.ChatVertexAI") as mock_cls,
        ):
            core_llm_get_llm()
            kwargs = mock_cls.call_args.kwargs
            assert kwargs["model_name"] == "gemini-2.5-flash"

    def test_unknown_tier_raises_value_error(self) -> None:
        with (
            patch("core.core_llm.get_settings", return_value=_settings_stub()),
            patch("core.core_llm.ChatVertexAI"),
        ):
            with pytest.raises(ValueError, match="Unknown LLM tier"):
                core_llm_get_llm(tier="bogus")

    def test_env_override_propagates(self) -> None:
        overridden = _settings_stub(
            model_high="gemini-2.5-pro-preview", model_low="gemini-2.5-flash-lite"
        )
        with (
            patch("core.core_llm.get_settings", return_value=overridden),
            patch("core.core_llm.ChatVertexAI") as mock_cls,
        ):
            core_llm_get_llm(tier="high")
            core_llm_get_llm(tier="low")
            calls = [c.kwargs["model_name"] for c in mock_cls.call_args_list]
            assert calls == ["gemini-2.5-pro-preview", "gemini-2.5-flash-lite"]


class TestCoreLlmCache:
    """Cache key is (tier, temperature)."""

    def test_same_tier_temperature_returns_same_instance(self) -> None:
        with (
            patch("core.core_llm.get_settings", return_value=_settings_stub()),
            patch("core.core_llm.ChatVertexAI", return_value=MagicMock()),
        ):
            a = core_llm_get_llm(tier="high", temperature=0.1)
            b = core_llm_get_llm(tier="high", temperature=0.1)
            assert a is b

    def test_distinct_tiers_return_distinct_instances(self) -> None:
        with (
            patch("core.core_llm.get_settings", return_value=_settings_stub()),
            patch("core.core_llm.ChatVertexAI", side_effect=lambda **_: MagicMock()),
        ):
            high = core_llm_get_llm(tier="high", temperature=0.1)
            low = core_llm_get_llm(tier="low", temperature=0.1)
            assert high is not low

    def test_distinct_temperatures_return_distinct_instances(self) -> None:
        with (
            patch("core.core_llm.get_settings", return_value=_settings_stub()),
            patch("core.core_llm.ChatVertexAI", side_effect=lambda **_: MagicMock()),
        ):
            a = core_llm_get_llm(tier="high", temperature=0.0)
            b = core_llm_get_llm(tier="high", temperature=0.5)
            assert a is not b
