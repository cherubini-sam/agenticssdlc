"""Unit tests for model evaluation."""

from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tuning.tuning_config import tuning_config_settings_get
from src.tuning.tuning_evaluate import TuningEvaluate, tuning_evaluate_tuned_endpoint


class TestTuningEvaluate:
    """Test model evaluation."""

    @pytest.fixture(autouse=True)
    def _clear_settings_cache(self):
        """Clear lru_cache before and after every test for isolation."""

        tuning_config_settings_get.cache_clear()
        yield
        tuning_config_settings_get.cache_clear()

    @pytest.fixture
    def evaluator(self):
        """Create evaluator with ChatVertexAI fully mocked for the lifetime of each test."""

        mock_model_client = MagicMock()

        with ExitStack() as stack:
            stack.enter_context(
                patch("src.tuning.tuning_evaluate.ChatVertexAI", return_value=mock_model_client)
            )
            ev = TuningEvaluate(
                endpoint_id="projects/test/locations/us-central1/endpoints/ep123",
                project_id="test-project",
            )
            ev.model_client = mock_model_client
            yield ev

    def test_evaluator_initialization(self, evaluator):
        """Test evaluator initialization."""

        assert evaluator.project_id == "test-project"
        assert evaluator.endpoint_id is not None

    def test_compute_metrics_all_correct(self, evaluator):
        """Test metrics computation with perfect predictions."""

        predictions = ["GREEN", "ERROR", "GREEN"]
        ground_truth = ["GREEN", "ERROR", "GREEN"]

        metrics = evaluator._tuning_evaluate_compute_metrics(predictions, ground_truth)
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1"] == 1.0

    def test_compute_metrics_false_positives(self, evaluator):
        """Test metrics with false positives."""

        predictions = ["ERROR", "ERROR", "GREEN"]
        ground_truth = ["GREEN", "ERROR", "GREEN"]

        metrics = evaluator._tuning_evaluate_compute_metrics(predictions, ground_truth)
        assert metrics["false_positives"] == 1
        assert metrics["precision"] < 1.0

    def test_compute_metrics_false_negatives(self, evaluator):
        """Test metrics with false negatives."""

        predictions = ["GREEN", "GREEN", "GREEN"]
        ground_truth = ["GREEN", "ERROR", "GREEN"]

        metrics = evaluator._tuning_evaluate_compute_metrics(predictions, ground_truth)
        assert metrics["false_negatives"] == 1
        assert metrics["recall"] < 1.0

    async def test_invoke_model(self, evaluator):
        """Test model invocation."""

        decision_json = '{"protocol_status": "GREEN", "protocol_violations": []}'
        evaluator.model_client.ainvoke = AsyncMock(return_value=decision_json)

        status = await evaluator._tuning_evaluate_invoke_model("Test intent")
        assert status == "GREEN"

    async def test_evaluate_on_dataset(self, evaluator):
        """Test evaluation on dataset."""

        test_examples = [
            {
                "user_intent": "Design API",
                "protocol_decision": {"protocol_status": "GREEN"},
            },
            {
                "user_intent": "Bypass security",
                "protocol_decision": {"protocol_status": "ERROR"},
            },
        ]

        evaluator.model_client.ainvoke = AsyncMock(
            side_effect=['{"protocol_status": "GREEN"}', '{"protocol_status": "ERROR"}']
        )

        with patch.object(
            evaluator, "_tuning_evaluate_load_dataset", new_callable=AsyncMock
        ) as mock_load:
            mock_load.return_value = test_examples
            metrics = await evaluator.tuning_evaluate_on_dataset(gcs_uri="gs://bucket/val.jsonl")

            assert "precision" in metrics
            assert "recall" in metrics
            assert "f1" in metrics
            assert "passes_threshold" in metrics

    def test_evaluator_no_endpoint(self):
        """Test evaluator initialization without endpoint produces None model_client."""

        mock_model = MagicMock()
        mock_settings = MagicMock()
        mock_settings.tuned_protocol_endpoint_id = ""
        mock_settings.gcp_project_id = "test-project"
        mock_settings.gcp_region = "us-central1"

        with patch("src.tuning.tuning_evaluate.ChatVertexAI", return_value=mock_model):
            with patch(
                "src.tuning.tuning_evaluate.tuning_config_settings_get", return_value=mock_settings
            ):
                evaluator = TuningEvaluate(project_id="test-project")
                assert evaluator.model_client is None

    async def test_evaluate_on_dataset_no_endpoint(self, evaluator):
        """Test evaluation fails gracefully without endpoint."""

        evaluator.model_client = None
        result = await evaluator.tuning_evaluate_on_dataset(gcs_uri="gs://bucket/val.jsonl")

        assert result["status"] == "ERROR"
        assert "message" in result

    async def test_invoke_model_json_dict_response(self, evaluator):
        """Test model invocation with dict response."""

        mock_response = MagicMock()
        mock_response.dict.return_value = {"protocol_status": "ERROR"}
        evaluator.model_client.ainvoke = AsyncMock(return_value=mock_response)

        status = await evaluator._tuning_evaluate_invoke_model("Test intent")
        assert status == "ERROR"

    async def test_invoke_model_invalid_response(self, evaluator):
        """Test model invocation with invalid JSON falls back to GREEN."""

        evaluator.model_client.ainvoke = AsyncMock(return_value="invalid json")

        status = await evaluator._tuning_evaluate_invoke_model("Test intent")
        assert status == "GREEN"  # Default fallback

    def test_compute_metrics_zero_metrics(self, evaluator):
        """Test metrics when all predictions are GREEN (no ERROR cases)."""

        predictions = ["GREEN", "GREEN", "GREEN"]
        ground_truth = ["GREEN", "GREEN", "GREEN"]

        metrics = evaluator._tuning_evaluate_compute_metrics(predictions, ground_truth)
        assert metrics["true_positives"] == 0
        assert metrics["false_positives"] == 0
        assert metrics["false_negatives"] == 0

    async def test_load_dataset_gcs_failure(self, evaluator):
        """Test dataset loading from GCS handles client errors gracefully."""

        with patch("google.cloud.storage.Client") as mock_client:
            mock_client.return_value.bucket.side_effect = Exception("GCS error")
            examples = await evaluator._tuning_evaluate_load_dataset(
                gcs_uri="gs://bucket/missing.jsonl"
            )
            assert examples == []

    async def test_evaluate_on_dataset_inference_exception(self, evaluator):
        """Test evaluation counts examples even when inference raises."""

        test_examples = [{"user_intent": "Test", "protocol_decision": {"protocol_status": "GREEN"}}]

        evaluator.model_client.ainvoke = AsyncMock(side_effect=Exception("API error"))

        with patch.object(
            evaluator, "_tuning_evaluate_load_dataset", new_callable=AsyncMock
        ) as mock_load:
            mock_load.return_value = test_examples
            metrics = await evaluator.tuning_evaluate_on_dataset(gcs_uri="gs://bucket/val.jsonl")

            assert metrics["evaluated_examples"] == 1
            assert metrics["f1"] == 0.0


class TestTuningEvaluateTunedEndpoint:
    """Test standalone evaluation function."""

    @pytest.fixture(autouse=True)
    def _clear_settings_cache(self):
        """Clear lru_cache before and after every test for isolation."""

        tuning_config_settings_get.cache_clear()
        yield
        tuning_config_settings_get.cache_clear()

    async def test_evaluate_tuned_endpoint_function(self):
        """Test standalone evaluation function delegates to TuningEvaluate correctly."""

        with patch(
            "src.tuning.tuning_evaluate.TuningEvaluate.tuning_evaluate_on_dataset",
            new_callable=AsyncMock,
        ) as mock_eval:
            mock_eval.return_value = {
                "precision": 0.95,
                "recall": 0.95,
                "f1": 0.95,
                "passes_threshold": True,
            }

            result = await tuning_evaluate_tuned_endpoint(
                endpoint_id="test-endpoint", validation_uri="gs://bucket/val.jsonl"
            )

            assert result["f1"] == 0.95
            assert result["passes_threshold"] is True
