"""Unit tests for synthetic data generation."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.tuning.tuning_config import ProtocolDecision, SyntheticDataPoint
from src.tuning.tuning_generator import TuningGenerator


class TestTuningGenerator:
    """Test synthetic data generator."""

    @pytest.fixture
    def generator(self):
        """Create generator with mocked GCP client."""

        with patch("src.tuning.tuning_generator.storage.Client"):
            with patch("src.tuning.tuning_generator.ChatVertexAI"):
                return TuningGenerator(project_id="test-project")

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

    @pytest.mark.asyncio
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

        mock_files = []
        with patch("pathlib.Path.glob", return_value=mock_files):
            with patch("pathlib.Path.exists", return_value=True):
                policies = generator.tuning_generator_extract_policies()
                assert isinstance(policies, str)
