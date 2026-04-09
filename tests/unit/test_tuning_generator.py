"""Unit tests for synthetic data generation."""

import json
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tuning.tuning_config import (
    ProtocolDecision,
    SyntheticDataPoint,
    tuning_config_settings_get,
)
from src.tuning.tuning_generator import TuningGenerator


class TestTuningGenerator:
    """Test synthetic data generator."""

    @pytest.fixture(autouse=True)
    def _clear_settings_cache(self):
        """Clear lru_cache before and after every test for isolation."""

        tuning_config_settings_get.cache_clear()
        yield
        tuning_config_settings_get.cache_clear()

    @pytest.fixture
    def generator(self):
        """Create generator with heavy GCP clients fully mocked for the lifetime of each test."""

        mock_storage_client = MagicMock()
        mock_chat_vertex = MagicMock()

        with ExitStack() as stack:
            stack.enter_context(
                patch(
                    "src.tuning.tuning_generator.storage.Client", return_value=mock_storage_client
                )
            )
            stack.enter_context(
                patch("src.tuning.tuning_generator.ChatVertexAI", return_value=mock_chat_vertex)
            )
            gen = TuningGenerator(project_id="test-project", gcs_bucket="test-bucket")
            gen.synthesizer = mock_chat_vertex
            gen.gcs_client = mock_storage_client
            yield gen

    def test_generator_initialization(self, generator):
        """Test generator initialization."""

        assert generator.project_id == "test-project"
        assert generator.gcs_bucket is not None

    def test_clean_markdown(self, generator):
        """Test markdown cleaning."""

        content = "# Header\n\nSome **bold** text\n---\nMore text"
        cleaned = generator._tuning_generator_clean_markdown(content)
        assert "---" not in cleaned
        assert "Header" in cleaned

    def test_parse_json_response(self, generator):
        """Test JSON response parsing."""

        response = (
            '{"user_intent": "task1", "protocol_status": "GREEN", "protocol_violations": []}\n'
            '{"user_intent": "task2", "protocol_status": "ERROR", "protocol_violations": ["rule1"]}'
        )
        examples = generator._tuning_generator_parse_json_response(response, category="test")
        assert len(examples) == 2
        assert examples[0].user_intent == "task1"
        assert examples[1].protocol_decision.protocol_status == "ERROR"

    def test_format_to_jsonl(self, generator):
        """Test JSONL formatting."""

        decision = ProtocolDecision(protocol_status="GREEN")
        point = SyntheticDataPoint(
            user_intent="Test task",
            protocol_decision=decision,
            category="compliant",
        )
        jsonl = generator.tuning_generator_format_jsonl([point])

        entry = json.loads(jsonl.split("\n")[0])
        assert "systemInstruction" in entry
        assert "contents" in entry
        assert len(entry["contents"]) == 2

    async def test_generate_examples_integration(self, generator):
        """Test example generation with mocked LLM."""

        mock_response = (
            '{"user_intent": "Design API", "protocol_status": "GREEN", "protocol_violations": []}'
        )
        generator.synthesizer.ainvoke = AsyncMock(return_value=mock_response)

        examples = await generator._tuning_generator_generate_examples(
            "Test prompt", count=1, category="test"
        )
        assert len(examples) == 1
        assert examples[0].user_intent == "Design API"

    def test_extract_policies_empty_directory(self, generator):
        """Test policy extraction with missing directory."""

        with patch("pathlib.Path.exists", return_value=False):
            policies = generator.tuning_generator_extract_policies()
            assert policies == ""

    def test_extract_policies_with_files(self, generator):
        """Test policy extraction with mock files."""

        with patch("pathlib.Path.glob", return_value=[]):
            with patch("pathlib.Path.exists", return_value=True):
                policies = generator.tuning_generator_extract_policies()
                assert isinstance(policies, str)

    def test_clean_markdown_with_dashes(self, generator):
        """Test markdown cleaning removes dash separators."""

        content = "# Header\n---\nContent"
        cleaned = generator._tuning_generator_clean_markdown(content)
        assert "---" not in cleaned
        assert "Header" in cleaned

    def test_parse_json_response_invalid_json(self, generator):
        """Test JSON parsing with invalid data."""

        response = "not json\n{valid json line}"
        examples = generator._tuning_generator_parse_json_response(response, "test")
        assert len(examples) == 0

    async def test_generate_examples_api_failure(self, generator):
        """Test example generation handles API failures."""

        generator.synthesizer.ainvoke = AsyncMock(side_effect=Exception("API error"))

        examples = await generator._tuning_generator_generate_examples(
            "test prompt", count=1, category="test"
        )
        assert len(examples) == 0

    def test_format_jsonl_empty_list(self, generator):
        """Test JSONL formatting with empty list."""

        jsonl = generator.tuning_generator_format_jsonl([])
        assert jsonl == ""

    def test_upload_gcs_failure(self, generator):
        """Test GCS upload handles failures."""

        mock_blob = MagicMock()
        mock_blob.upload_from_string.side_effect = Exception("Upload failed")
        generator.gcs_client.bucket.return_value.blob.return_value = mock_blob

        with pytest.raises(Exception):
            generator.tuning_generator_upload_gcs("test content", is_training=True)
