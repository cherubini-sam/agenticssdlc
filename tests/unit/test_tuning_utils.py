"""Unit tests for tuning configuration and schemas."""

import pytest
from pydantic import ValidationError

from src.tuning.tuning_config import (
    ProtocolDecision,
    SyntheticDataPoint,
    tuning_config_settings_get,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Clear the lru_cache before and after every test."""

    tuning_config_settings_get.cache_clear()
    yield
    tuning_config_settings_get.cache_clear()


class TestProtocolDecision:
    """Test ProtocolDecision schema."""

    def test_protocol_decision_green_status(self):
        """Test GREEN status with empty violations."""

        decision = ProtocolDecision(protocol_status="GREEN", protocol_violations=[])
        assert decision.protocol_status == "GREEN"
        assert decision.protocol_violations == []

    def test_protocol_decision_error_status(self):
        """Test ERROR status with violations."""

        violations = ["Exceeds length limit", "Contains forbidden keyword"]
        decision = ProtocolDecision(protocol_status="ERROR", protocol_violations=violations)
        assert decision.protocol_status == "ERROR"
        assert len(decision.protocol_violations) == 2

    def test_protocol_decision_to_state_dict(self):
        """Test conversion to state dictionary."""

        decision = ProtocolDecision(protocol_status="GREEN", protocol_violations=[])
        state_dict = decision.tuning_config_to_state_dict()
        assert "protocol_status" in state_dict
        assert "protocol_violations" in state_dict

    def test_protocol_decision_invalid_status(self):
        """Test that invalid status raises ValidationError."""

        with pytest.raises(ValidationError):
            ProtocolDecision(protocol_status="INVALID", protocol_violations=[])

    def test_protocol_decision_model_dump(self):
        """Test ProtocolDecision serialization."""

        decision = ProtocolDecision(protocol_status="GREEN", protocol_violations=["rule1", "rule2"])
        dumped = decision.model_dump()
        assert dumped["protocol_status"] == "GREEN"
        assert len(dumped["protocol_violations"]) == 2

    def test_protocol_decision_state_dict_structure(self):
        """Test ProtocolDecision state dict has correct structure."""

        decision = ProtocolDecision(protocol_status="ERROR", protocol_violations=["violation1"])
        state = decision.tuning_config_to_state_dict()
        assert "protocol_status" in state
        assert "protocol_violations" in state
        assert state["protocol_violations"][0] == "violation1"


class TestSyntheticDataPoint:
    """Test SyntheticDataPoint schema."""

    def test_synthetic_data_point_creation(self):
        """Test creating a synthetic data point."""

        decision = ProtocolDecision(protocol_status="GREEN", protocol_violations=[])
        point = SyntheticDataPoint(
            user_intent="Design a REST API",
            protocol_decision=decision,
            category="compliant",
        )
        assert point.user_intent == "Design a REST API"
        assert point.protocol_decision.protocol_status == "GREEN"
        assert point.category == "compliant"

    def test_synthetic_data_point_categories(self):
        """Test all valid categories."""

        decision = ProtocolDecision(protocol_status="GREEN")
        for category in ["compliant", "adversarial", "edge_case"]:
            point = SyntheticDataPoint(
                user_intent="Test intent",
                protocol_decision=decision,
                category=category,
            )
            assert point.category == category

    def test_synthetic_data_point_with_violations(self):
        """Test SyntheticDataPoint with violations."""

        decision = ProtocolDecision(
            protocol_status="ERROR", protocol_violations=["Security violation", "Policy violation"]
        )
        point = SyntheticDataPoint(
            user_intent="Malicious request", protocol_decision=decision, category="adversarial"
        )
        assert point.protocol_decision.protocol_status == "ERROR"
        assert len(point.protocol_decision.protocol_violations) == 2

    def test_synthetic_data_point_empty_violations(self):
        """Test SyntheticDataPoint with empty violations."""

        decision = ProtocolDecision(protocol_status="GREEN", protocol_violations=[])
        point = SyntheticDataPoint(
            user_intent="Safe task", protocol_decision=decision, category="compliant"
        )
        assert point.protocol_decision.protocol_violations == []


class TestTuningSettings:
    """Test TuningSettings configuration."""

    def test_tuning_settings_defaults(self):
        """Test default configuration values."""

        settings = tuning_config_settings_get()
        assert settings.base_model == "gemini-2.5-flash"
        assert settings.synthesizer_model == "gemini-2.5-pro"
        assert settings.epochs == 10
        assert settings.learning_rate_multiplier == 8.0
        assert settings.adapter_size == 4

    def test_tuning_settings_gcs_uris(self):
        """Test GCS URI generation."""

        settings = tuning_config_settings_get()
        train_uri = settings.tuning_config_gcs_train_uri
        val_uri = settings.tuning_config_gcs_val_uri
        assert train_uri.startswith("gs://")
        assert "train.jsonl" in train_uri
        assert "val.jsonl" in val_uri

    def test_tuning_settings_singleton(self):
        """Test that settings is a singleton (lru_cache returns same object)."""

        settings1 = tuning_config_settings_get()
        settings2 = tuning_config_settings_get()
        assert settings1 is settings2
