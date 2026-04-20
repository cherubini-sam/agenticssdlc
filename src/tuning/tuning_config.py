"""Configuration, settings, and schemas for LoRA fine-tuning."""

from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.tuning.tuning_utils import (
    TUNING_CONFIG_DEFAULT_ADAPTER_SIZE,
    TUNING_CONFIG_DEFAULT_BASE_MODEL,
    TUNING_CONFIG_DEFAULT_EPOCHS,
    TUNING_CONFIG_DEFAULT_GCP_PROJECT,
    TUNING_CONFIG_DEFAULT_GCP_REGION,
    TUNING_CONFIG_DEFAULT_GCS_BUCKET,
    TUNING_CONFIG_DEFAULT_LEARNING_RATE_MULTIPLIER,
    TUNING_CONFIG_DEFAULT_SYNTHESIZER_MODEL,
    TUNING_CONFIG_ENV_ENCODING,
    TUNING_CONFIG_ENV_FILE,
    TUNING_TRAIN_JSONL_FILENAME,
    TUNING_VAL_JSONL_FILENAME,
)


class ProtocolDecision(BaseModel):
    """Structured output schema for fine-tuned Protocol gatekeeper."""

    protocol_status: str = Field(
        ...,
        description='Must be "GREEN" (compliant) or "ERROR" (violation detected)',
        pattern="^(GREEN|ERROR)$",
    )
    protocol_violations: list[str] = Field(
        default_factory=list,
        description="Empty array if status is GREEN; list of rule violations if ERROR",
    )

    def tuning_config_to_state_dict(self) -> dict:
        """Convert to AgentsState-compatible dictionary."""

        return {
            "protocol_status": self.protocol_status,
            "protocol_violations": self.protocol_violations,
        }


class SyntheticDataPoint(BaseModel):
    """Single synthetic training example for JSONL generation."""

    user_intent: str = Field(..., description="The user's task request")
    protocol_decision: ProtocolDecision = Field(..., description="Ground truth classification")
    category: str = Field(..., description='One of: "compliant", "adversarial", "edge_case"')


class TuningSettings(BaseSettings):
    """Pydantic settings model loaded from environment variables and .env file.

    Covers GCP project/region, GCS bucket, base model, synthesizer model,
    training hyperparameters (epochs, learning rate multiplier, adapter size),
    and the optional tuned Protocol endpoint ID.
    """

    model_config = SettingsConfigDict(
        env_file=TUNING_CONFIG_ENV_FILE,
        env_file_encoding=TUNING_CONFIG_ENV_ENCODING,
        extra="ignore",
    )

    gcp_project_id: str = Field(default=TUNING_CONFIG_DEFAULT_GCP_PROJECT)
    gcp_region: str = Field(default=TUNING_CONFIG_DEFAULT_GCP_REGION)
    gcs_bucket: str = Field(default=TUNING_CONFIG_DEFAULT_GCS_BUCKET)
    base_model: str = Field(default=TUNING_CONFIG_DEFAULT_BASE_MODEL)
    synthesizer_model: str = Field(default=TUNING_CONFIG_DEFAULT_SYNTHESIZER_MODEL)
    epochs: int = Field(default=TUNING_CONFIG_DEFAULT_EPOCHS)
    learning_rate_multiplier: float = Field(default=TUNING_CONFIG_DEFAULT_LEARNING_RATE_MULTIPLIER)
    adapter_size: int = Field(default=TUNING_CONFIG_DEFAULT_ADAPTER_SIZE)
    tuned_protocol_endpoint_id: str = Field(default="", alias="TUNED_PROTOCOL_ENDPOINT_ID")

    @property
    def tuning_config_gcs_train_uri(self) -> str:
        """GCS URI for training dataset."""

        return f"gs://{self.gcs_bucket}/{TUNING_TRAIN_JSONL_FILENAME}"

    @property
    def tuning_config_gcs_val_uri(self) -> str:
        """GCS URI for validation dataset."""

        return f"gs://{self.gcs_bucket}/{TUNING_VAL_JSONL_FILENAME}"


@lru_cache(maxsize=1)
def tuning_config_settings_get() -> TuningSettings:
    """Get singleton TuningSettings instance.

    Returns:
        TuningSettings created once and cached for the process lifetime.
    """

    return TuningSettings()
