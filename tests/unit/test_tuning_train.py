"""Unit tests for LoRA training orchestration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tuning.tuning_config import tuning_config_settings_get

_VERTEXAI_SFT_MOCK = MagicMock()


@pytest.fixture(scope="module", autouse=True)
def _patch_vertexai_sft_module():
    """Patch vertexai.tuning.sft before tuning_train is imported for the first time."""

    with patch.dict("sys.modules", {"vertexai.tuning": MagicMock(sft=_VERTEXAI_SFT_MOCK)}):
        # Import here so the module sees mocked sys.modules on first load
        import src.tuning.tuning_train  # noqa: F401  (side-effect import)

        yield


class TestTuningTrain:
    """Test LoRA training orchestration."""

    @pytest.fixture(autouse=True)
    def _clear_settings_cache(self):
        """Clear lru_cache before and after every test for isolation."""
        tuning_config_settings_get.cache_clear()
        yield
        tuning_config_settings_get.cache_clear()

    @pytest.fixture
    def trainer(self):
        """Create trainer instance; vertexai.tuning.sft is already mocked module-wide."""
        from src.tuning.tuning_train import TuningTrain

        return TuningTrain(project_id="test-project", region="us-central1")

    def test_trainer_initialization(self, trainer):
        """Test trainer initialization."""

        assert trainer.project_id == "test-project"
        assert trainer.region == "us-central1"

    async def test_poll_job_completion_success(self, trainer):
        """Test successful job completion polling."""

        mock_job = MagicMock()
        mock_job.has_ended = MagicMock(side_effect=[False, True])
        mock_job.has_succeeded = MagicMock(return_value=True)
        mock_job.resource_name = "projects/test/locations/us-central1/jobs/job123"
        mock_job.model_name = "models/tuned-model-123"
        mock_job.training_loss = 0.05
        mock_job.validation_loss = 0.08

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await trainer._tuning_train_poll_job(mock_job)

        assert result["status"] == "SUCCESS"
        assert result["tuned_model_endpoint"] == "models/tuned-model-123"

    async def test_poll_job_completion_failure(self, trainer):
        """Test failed job completion."""

        mock_job = MagicMock()
        mock_job.has_ended = MagicMock(return_value=True)
        mock_job.has_succeeded = MagicMock(return_value=False)
        mock_job.has_failed = MagicMock(return_value=True)
        mock_job.error = "Training job failed"
        mock_job.state = "FAILED"

        with pytest.raises(RuntimeError):
            await trainer._tuning_train_poll_job(mock_job)

    async def test_deploy_tuned_endpoint(self, trainer):
        """Test endpoint deployment extracts the trailing model ID."""

        tuned_model_name = "projects/test/locations/us-central1/models/tuned-123"
        endpoint_id = await trainer.tuning_train_deploy_endpoint(tuned_model_name)
        assert "tuned-123" in endpoint_id

    async def test_train_lora_adapter_with_mock(self, trainer):
        """Test LoRA training with mocked Vertex AI."""

        mock_job = MagicMock()
        mock_job.has_ended = MagicMock(side_effect=[False, True])
        mock_job.has_succeeded = MagicMock(return_value=True)
        mock_job.resource_name = "projects/test/locations/us-central1/jobs/job123"
        mock_job.model_name = "models/tuned-model"

        with patch("src.tuning.tuning_train.sft.train", return_value=mock_job):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await trainer.tuning_train_lora_adapter(
                    train_uri="gs://bucket/train.jsonl",
                    validation_uri="gs://bucket/val.jsonl",
                )

        assert result["status"] == "SUCCESS"
        assert "tuned_model_endpoint" in result

    async def test_orchestrate_full_pipeline(self, trainer):
        """Test full training pipeline orchestration."""

        mock_job = MagicMock()
        mock_job.has_ended = MagicMock(side_effect=[False, True])
        mock_job.has_succeeded = MagicMock(return_value=True)
        mock_job.resource_name = "projects/test/locations/us-central1/jobs/job123"
        mock_job.model_name = "models/tuned-model"

        with patch("src.tuning.tuning_train.sft.train", return_value=mock_job):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                endpoint_id = await trainer.tuning_train_orchestrate_pipeline(
                    train_uri="gs://bucket/train.jsonl",
                    validation_uri="gs://bucket/val.jsonl",
                )

        assert endpoint_id is not None
        assert isinstance(endpoint_id, str)

    async def test_poll_job_timeout(self, trainer):
        """Test job polling raises TimeoutError when max wait is exceeded."""

        mock_job = MagicMock()
        mock_job.has_ended = MagicMock(return_value=False)
        mock_job.state = "RUNNING"

        call_count = [0]

        def mock_time():
            call_count[0] += 1
            return 0 if call_count[0] == 1 else 10_000

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with patch("src.tuning.tuning_train.time.time", side_effect=mock_time):
                with pytest.raises(TimeoutError):
                    await trainer._tuning_train_poll_job(mock_job)

    async def test_poll_job_unexpected_state(self, trainer):
        """Test job with unexpected state (not succeeded, not failed) raises RuntimeError."""

        mock_job = MagicMock()
        mock_job.has_ended = MagicMock(return_value=True)
        mock_job.has_succeeded = MagicMock(return_value=False)
        mock_job.has_failed = MagicMock(return_value=False)
        mock_job.state = "CANCELLED"

        with pytest.raises(RuntimeError):
            await trainer._tuning_train_poll_job(mock_job)

    async def test_orchestrate_pipeline_training_failure(self, trainer):
        """Test pipeline raises RuntimeError when the training job fails."""

        mock_job = MagicMock()
        mock_job.has_ended = MagicMock(return_value=True)
        mock_job.has_succeeded = MagicMock(return_value=False)
        mock_job.has_failed = MagicMock(return_value=True)
        mock_job.error = "Out of memory"

        with patch("src.tuning.tuning_train.sft.train", return_value=mock_job):
            with pytest.raises(RuntimeError):
                await trainer.tuning_train_orchestrate_pipeline(
                    train_uri="gs://bucket/train.jsonl",
                    validation_uri="gs://bucket/val.jsonl",
                )

    async def test_deploy_endpoint_extracts_id(self, trainer):
        """Test deployment extracts endpoint ID from model name."""

        endpoint_id = await trainer.tuning_train_deploy_endpoint(
            "projects/test/locations/us-central1/models/tuned-123"
        )
        assert endpoint_id == "tuned-123"
