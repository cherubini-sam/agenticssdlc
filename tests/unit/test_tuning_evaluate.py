"""Unit tests for model evaluation."""

from unittest.mock import AsyncMock, patch

import pytest

from src.tuning.tuning_evaluate import TuningEvaluate, tuning_evaluate_tuned_endpoint


class TestTuningEvaluate:
    """Test model evaluation."""

    @pytest.fixture
    def evaluator(self):
        """Create evaluator instance."""

        with patch("src.tuning.tuning_evaluate.ChatVertexAI"):
            return TuningEvaluate(
                endpoint_id="projects/test/locations/us-central1/endpoints/ep123",
                project_id="test-project",
            )

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

    @pytest.mark.asyncio
    async def test_load_dataset_from_file(self, evaluator):
        """Test loading dataset from local file."""

        mock_content = (
            '{"user_intent": "task1", "protocol_decision": {"protocol_status": "GREEN"}}\n'
            '{"user_intent": "task2", "protocol_decision": {"protocol_status": "ERROR"}}'
        )

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value = mock_content.split("\n")

    @pytest.mark.asyncio
    async def test_invoke_model(self, evaluator):
        """Test model invocation."""

        decision_json = '{"protocol_status": "GREEN", "protocol_violations": []}'
        evaluator.model_client.ainvoke = AsyncMock(return_value=decision_json)

        status = await evaluator._tuning_evaluate_invoke_model("Test intent")
        assert status == "GREEN"

    @pytest.mark.asyncio
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


class TestTuningEvaluateTunedEndpoint:
    """Test standalone evaluation function."""

    @pytest.mark.asyncio
    async def test_evaluate_tuned_endpoint_function(self):
        """Test standalone evaluation function."""

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
