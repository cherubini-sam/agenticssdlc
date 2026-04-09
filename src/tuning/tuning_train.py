"""Orchestrate Vertex AI Supervised Fine-Tuning job for LoRA adaptation."""

import asyncio
import logging
import time

from vertexai.tuning import sft

from src.tuning.tuning_config import tuning_config_settings_get
from src.tuning.tuning_utils import (
    TUNING_LOG_TRAIN_DEPLOY,
    TUNING_LOG_TRAIN_DEPLOY_FAILED,
    TUNING_LOG_TRAIN_ENDPOINT_ID,
    TUNING_LOG_TRAIN_EXCEEDED_MAX,
    TUNING_LOG_TRAIN_FAILED,
    TUNING_LOG_TRAIN_JOB_CREATED,
    TUNING_LOG_TRAIN_JOB_STATUS,
    TUNING_LOG_TRAIN_PIPELINE_COMPLETE,
    TUNING_LOG_TRAIN_PIPELINE_FAILED,
    TUNING_LOG_TRAIN_PIPELINE_START,
    TUNING_LOG_TRAIN_POLLING,
    TUNING_LOG_TRAIN_SUBMIT,
    TUNING_LOG_TRAIN_SUCCESS,
    TUNING_LOG_TRAIN_UNEXPECTED,
    TUNING_TRAIN_MAX_WAIT_TIME,
    TUNING_TRAIN_POLL_INTERVAL,
    TUNING_TRAIN_STATUS_SUCCESS,
)

logger = logging.getLogger(__name__)


class TuningTrain:
    """Submit and monitor LoRA fine-tuning jobs on Vertex AI."""

    def __init__(self, project_id: str = None, region: str = None):
        """Initialize trainer with Vertex AI configuration."""

        self.settings = tuning_config_settings_get()
        self.project_id = project_id or self.settings.gcp_project_id
        self.region = region or self.settings.gcp_region
        self.logger = logging.getLogger(__name__)

    async def tuning_train_lora_adapter(self, train_uri: str, validation_uri: str) -> dict:
        """Submit LoRA fine-tuning job to Vertex AI."""

        self.logger.info(
            TUNING_LOG_TRAIN_SUBMIT.format(
                project=self.project_id,
                region=self.region,
                base_model=self.settings.base_model,
                train_uri=train_uri,
                val_uri=validation_uri,
                epochs=self.settings.epochs,
                lr_mult=self.settings.learning_rate_multiplier,
                adapter_size=self.settings.adapter_size,
            )
        )

        try:
            job = sft.train(
                source_model=self.settings.base_model,
                training_data=train_uri,
                validation_data=validation_uri,
                epochs=self.settings.epochs,
                learning_rate_multiplier=self.settings.learning_rate_multiplier,
                tuning_job_location=self.region,
                project=self.project_id,
            )

            self.logger.info(TUNING_LOG_TRAIN_JOB_CREATED.format(resource_name=job.resource_name))

            result = await self._tuning_train_poll_job(job)
            return result

        except Exception as e:
            self.logger.error(f"Failed to submit fine-tuning job: {e}")
            raise

    async def _tuning_train_poll_job(self, job) -> dict:
        """Poll job status until completion."""

        self.logger.info(TUNING_LOG_TRAIN_POLLING)
        start_time = time.time()

        while not job.has_ended():
            elapsed = time.time() - start_time
            if elapsed > TUNING_TRAIN_MAX_WAIT_TIME:
                self.logger.error(
                    TUNING_LOG_TRAIN_EXCEEDED_MAX.format(max_time=TUNING_TRAIN_MAX_WAIT_TIME)
                )
                raise TimeoutError(f"Fine-tuning job timeout after {elapsed}s")

            self.logger.info(
                TUNING_LOG_TRAIN_JOB_STATUS.format(state=job.state, elapsed=int(elapsed))
            )
            await asyncio.sleep(TUNING_TRAIN_POLL_INTERVAL)
            job.refresh()

        if job.has_succeeded():
            self.logger.info(TUNING_LOG_TRAIN_SUCCESS)
            return {
                "status": TUNING_TRAIN_STATUS_SUCCESS,
                "job_resource_name": job.resource_name,
                "tuned_model_endpoint": job.model_name,
                "training_loss": getattr(job, "training_loss", None),
                "validation_loss": getattr(job, "validation_loss", None),
            }
        elif job.has_failed():
            error_msg = getattr(job, "error", "Unknown error")
            self.logger.error(TUNING_LOG_TRAIN_FAILED.format(error=error_msg))
            raise RuntimeError(TUNING_LOG_TRAIN_FAILED.format(error=error_msg))
        else:
            self.logger.error(TUNING_LOG_TRAIN_UNEXPECTED.format(state=job.state))
            raise RuntimeError(TUNING_LOG_TRAIN_UNEXPECTED.format(state=job.state))

    async def tuning_train_deploy_endpoint(self, tuned_model_name: str) -> str:
        """Deploy endpoint for fine-tuned model."""

        self.logger.info(TUNING_LOG_TRAIN_DEPLOY.format(model_name=tuned_model_name))

        try:
            endpoint_id = tuned_model_name.split("/")[-1]
            self.logger.info(TUNING_LOG_TRAIN_ENDPOINT_ID.format(endpoint_id=endpoint_id))
            return endpoint_id
        except Exception as e:
            self.logger.error(TUNING_LOG_TRAIN_DEPLOY_FAILED.format(error=e))
            raise

    async def tuning_train_orchestrate_pipeline(self, train_uri: str, validation_uri: str) -> str:
        """Orchestrate complete training and deployment."""

        self.logger.info(TUNING_LOG_TRAIN_PIPELINE_START)

        result = await self.tuning_train_lora_adapter(train_uri, validation_uri)

        if result["status"] != TUNING_TRAIN_STATUS_SUCCESS:
            raise RuntimeError(TUNING_LOG_TRAIN_PIPELINE_FAILED.format(result=result))

        endpoint_id = await self.tuning_train_deploy_endpoint(result["tuned_model_endpoint"])

        self.logger.info(TUNING_LOG_TRAIN_PIPELINE_COMPLETE.format(endpoint_id=endpoint_id))
        return endpoint_id
