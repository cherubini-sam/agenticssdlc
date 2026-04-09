"""Smoke tests for core_utils and agents_utils constants types, ranges, uniqueness."""

from __future__ import annotations

import logging

from agents.agents_utils import (
    AGENTS_ARCHITECT_AGENT_NAME,
    AGENTS_BASE_DEFAULT_MAX_RETRIES,
    AGENTS_ENGINEER_AGENT_NAME,
    AGENTS_LIBRARIAN_AGENT_NAME,
    AGENTS_LIBRARIAN_DEFAULT_K,
    AGENTS_MANAGER_AGENT_NAME,
    AGENTS_MANAGER_CONFIDENCE_THRESHOLD,
    AGENTS_MANAGER_GRAPH_RECURSION_LIMIT,
    AGENTS_MANAGER_MAX_RETRIES,
    AGENTS_MANAGER_NODE_ARCHITECT,
    AGENTS_MANAGER_NODE_END_FAILED,
    AGENTS_MANAGER_NODE_END_SUCCESS,
    AGENTS_MANAGER_NODE_EXECUTE,
    AGENTS_MANAGER_NODE_LIBRARIAN,
    AGENTS_MANAGER_NODE_PROTOCOL,
    AGENTS_MANAGER_NODE_RETRY,
    AGENTS_MANAGER_NODE_REVIEW,
    AGENTS_MANAGER_NODE_TASK,
    AGENTS_MANAGER_NODE_VERIFY,
    AGENTS_MANAGER_PHASE_2,
    AGENTS_MANAGER_PHASE_3,
    AGENTS_MANAGER_PHASE_4,
    AGENTS_MANAGER_PHASE_5,
    AGENTS_MANAGER_PHASE_6,
    AGENTS_MANAGER_VALIDATOR_THRESHOLD_DEFAULT,
    AGENTS_MANAGER_WORKFLOW_TIMEOUT_SECONDS,
    AGENTS_PROTOCOL_AGENT_NAME,
    AGENTS_PROTOCOL_MAX_CONTENT_LENGTH,
    AGENTS_PROTOCOL_STATUS_ERROR,
    AGENTS_PROTOCOL_STATUS_GREEN,
    AGENTS_REFLECTOR_AGENT_NAME,
    AGENTS_VALIDATOR_AGENT_NAME,
)
from core.core_utils import (
    CORE_CONFIG_DEFAULT_GCP_PROJECT,
    CORE_CONFIG_DEFAULT_GEMINI_MODEL,
    CORE_CONFIG_DEFAULT_PORT,
    CORE_CONFIG_DEFAULT_RATE_LIMIT_RPM,
    CORE_CONFIG_ENV_FILE,
    CORE_CONFIG_MISSING_PROJECT_ID_ERROR,
    CORE_LLM_DEFAULT_TEMPERATURE,
    CORE_LOGGING_DEFAULT_LOG_LEVEL,
    CORE_LOGGING_NOISY_LOGGERS,
    CORE_REMOTE_WRITE_TIMEOUT_S,
)


class TestCoreUtils:
    """Smoke tests for core_utils constants — types, ranges, and values."""

    def test_env_file_is_string(self) -> None:
        """ENV_FILE constant is a non-empty string."""

        assert isinstance(CORE_CONFIG_ENV_FILE, str)
        assert len(CORE_CONFIG_ENV_FILE) > 0

    def test_default_gcp_project_is_string(self) -> None:
        """DEFAULT_GCP_PROJECT constant is a string."""

        assert isinstance(CORE_CONFIG_DEFAULT_GCP_PROJECT, str)

    def test_default_gemini_model_contains_gemini(self) -> None:
        """Default Gemini model name contains 'gemini'."""

        assert "gemini" in CORE_CONFIG_DEFAULT_GEMINI_MODEL.lower()

    def test_default_port_is_positive_int(self) -> None:
        """Default port is a positive integer."""

        assert isinstance(CORE_CONFIG_DEFAULT_PORT, int)
        assert CORE_CONFIG_DEFAULT_PORT > 0

    def test_default_rate_limit_rpm_is_non_negative(self) -> None:
        """Default rate-limit RPM is a non-negative integer."""

        assert isinstance(CORE_CONFIG_DEFAULT_RATE_LIMIT_RPM, int)
        assert CORE_CONFIG_DEFAULT_RATE_LIMIT_RPM >= 0

    def test_missing_project_id_error_is_string(self) -> None:
        """Missing project-ID error message is a non-empty string."""

        assert isinstance(CORE_CONFIG_MISSING_PROJECT_ID_ERROR, str)
        assert len(CORE_CONFIG_MISSING_PROJECT_ID_ERROR) > 0

    def test_default_log_level_is_valid(self) -> None:
        """Default log level maps to a valid logging attribute."""

        assert hasattr(logging, CORE_LOGGING_DEFAULT_LOG_LEVEL)

    def test_noisy_loggers_is_list(self) -> None:
        """NOISY_LOGGERS is a non-empty list of strings."""

        assert isinstance(CORE_LOGGING_NOISY_LOGGERS, list)
        assert len(CORE_LOGGING_NOISY_LOGGERS) > 0
        assert all(isinstance(name, str) for name in CORE_LOGGING_NOISY_LOGGERS)

    def test_llm_default_temperature_is_float(self) -> None:
        """Default LLM temperature is a float in [0.0, 1.0]."""

        assert isinstance(CORE_LLM_DEFAULT_TEMPERATURE, float)
        assert 0.0 <= CORE_LLM_DEFAULT_TEMPERATURE <= 1.0

    def test_remote_write_timeout_is_positive(self) -> None:
        """Remote write timeout is a positive float."""

        assert isinstance(CORE_REMOTE_WRITE_TIMEOUT_S, float)
        assert CORE_REMOTE_WRITE_TIMEOUT_S > 0


class TestAgentsUtils:
    """Smoke tests for agents_utils constants — types, ranges, and uniqueness."""

    def test_agent_names_are_non_empty_strings(self) -> None:
        """All agent name constants are non-empty strings."""

        names = [
            AGENTS_ARCHITECT_AGENT_NAME,
            AGENTS_ENGINEER_AGENT_NAME,
            AGENTS_LIBRARIAN_AGENT_NAME,
            AGENTS_MANAGER_AGENT_NAME,
            AGENTS_PROTOCOL_AGENT_NAME,
            AGENTS_REFLECTOR_AGENT_NAME,
            AGENTS_VALIDATOR_AGENT_NAME,
        ]
        for name in names:
            assert isinstance(name, str)
            assert len(name) > 0

    def test_confidence_threshold_in_range(self) -> None:
        """Confidence threshold is a float in (0, 1]."""

        assert 0.0 < AGENTS_MANAGER_CONFIDENCE_THRESHOLD <= 1.0

    def test_max_retries_is_positive_int(self) -> None:
        """MAX_RETRIES is a positive integer."""

        assert isinstance(AGENTS_MANAGER_MAX_RETRIES, int)
        assert AGENTS_MANAGER_MAX_RETRIES > 0

    def test_workflow_timeout_is_positive(self) -> None:
        """Workflow timeout is a positive integer."""

        assert isinstance(AGENTS_MANAGER_WORKFLOW_TIMEOUT_SECONDS, int)
        assert AGENTS_MANAGER_WORKFLOW_TIMEOUT_SECONDS > 0

    def test_phase_constants_ordered(self) -> None:
        """Phase constants are strictly ordered from 2 to 6."""

        assert AGENTS_MANAGER_PHASE_2 < AGENTS_MANAGER_PHASE_3
        assert AGENTS_MANAGER_PHASE_3 < AGENTS_MANAGER_PHASE_4
        assert AGENTS_MANAGER_PHASE_4 < AGENTS_MANAGER_PHASE_5
        assert AGENTS_MANAGER_PHASE_5 < AGENTS_MANAGER_PHASE_6

    def test_graph_recursion_limit_is_reasonable(self) -> None:
        """Graph recursion limit is an integer of at least 10."""

        assert isinstance(AGENTS_MANAGER_GRAPH_RECURSION_LIMIT, int)
        assert AGENTS_MANAGER_GRAPH_RECURSION_LIMIT >= 10

    def test_protocol_max_content_length_is_positive(self) -> None:
        """Protocol max content length is a positive integer."""

        assert isinstance(AGENTS_PROTOCOL_MAX_CONTENT_LENGTH, int)
        assert AGENTS_PROTOCOL_MAX_CONTENT_LENGTH > 0

    def test_validator_threshold_in_range(self) -> None:
        """Validator default threshold is a float in (0, 1]."""

        assert 0.0 < AGENTS_MANAGER_VALIDATOR_THRESHOLD_DEFAULT <= 1.0

    def test_librarian_default_k_is_positive(self) -> None:
        """Librarian default k is a positive integer."""

        assert isinstance(AGENTS_LIBRARIAN_DEFAULT_K, int)
        assert AGENTS_LIBRARIAN_DEFAULT_K > 0

    def test_base_default_max_retries_is_non_negative(self) -> None:
        """Base default max retries is a non-negative integer."""

        assert isinstance(AGENTS_BASE_DEFAULT_MAX_RETRIES, int)
        assert AGENTS_BASE_DEFAULT_MAX_RETRIES >= 0

    def test_protocol_status_constants_are_distinct(self) -> None:
        """GREEN and ERROR protocol status strings are distinct."""

        assert AGENTS_PROTOCOL_STATUS_GREEN != AGENTS_PROTOCOL_STATUS_ERROR
        assert isinstance(AGENTS_PROTOCOL_STATUS_GREEN, str)
        assert isinstance(AGENTS_PROTOCOL_STATUS_ERROR, str)

    def test_node_names_are_distinct_strings(self) -> None:
        """All graph node name constants are distinct non-empty strings."""

        nodes = [
            AGENTS_MANAGER_NODE_PROTOCOL,
            AGENTS_MANAGER_NODE_TASK,
            AGENTS_MANAGER_NODE_LIBRARIAN,
            AGENTS_MANAGER_NODE_ARCHITECT,
            AGENTS_MANAGER_NODE_REVIEW,
            AGENTS_MANAGER_NODE_EXECUTE,
            AGENTS_MANAGER_NODE_VERIFY,
            AGENTS_MANAGER_NODE_RETRY,
            AGENTS_MANAGER_NODE_END_FAILED,
            AGENTS_MANAGER_NODE_END_SUCCESS,
        ]
        assert len(set(nodes)) == len(nodes)
        assert all(isinstance(n, str) and len(n) > 0 for n in nodes)
