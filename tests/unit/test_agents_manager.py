"""Pin the confidence threshold at 0.85 other code depends on this exact value."""

from __future__ import annotations

from agents.agents_utils import AGENTS_MANAGER_CONFIDENCE_THRESHOLD


class TestConfidenceThreshold:
    """Pin tests for the AGENTS_MANAGER_CONFIDENCE_THRESHOLD constant."""

    def test_confidence_threshold_value(self) -> None:
        """Constant equals exactly 0.85."""

        assert AGENTS_MANAGER_CONFIDENCE_THRESHOLD == 0.85

    def test_confidence_threshold_type(self) -> None:
        """Constant is a float."""

        assert isinstance(AGENTS_MANAGER_CONFIDENCE_THRESHOLD, float)
