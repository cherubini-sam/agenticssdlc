"""App configuration backed by env vars and .env file."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.core_utils import (
    CORE_CONFIG_DEFAULT_BIGQUERY_DATASET,
    CORE_CONFIG_DEFAULT_GCP_PROJECT,
    CORE_CONFIG_DEFAULT_GCP_REGION,
    CORE_CONFIG_DEFAULT_GCS_BUCKET,
    CORE_CONFIG_DEFAULT_GEMINI_MODEL,
    CORE_CONFIG_DEFAULT_PORT,
    CORE_CONFIG_DEFAULT_RATE_LIMIT_RPM,
    CORE_CONFIG_ENV_ENCODING,
    CORE_CONFIG_ENV_FILE,
    CORE_CONFIG_MISSING_PROJECT_ID_ERROR,
    CORE_LOGGING_DEFAULT_LOG_LEVEL,
)


class CoreSettings(BaseSettings):
    """
    Pydantic settings model loaded from environment variables.

    :return: Validated CoreSettings instance.
    :rtype: CoreSettings
    """

    model_config = SettingsConfigDict(
        env_file=CORE_CONFIG_ENV_FILE, env_file_encoding=CORE_CONFIG_ENV_ENCODING, extra="ignore"
    )

    # GCP
    gcp_project_id: str = Field(default=CORE_CONFIG_DEFAULT_GCP_PROJECT)
    gcp_region: str = Field(default=CORE_CONFIG_DEFAULT_GCP_REGION)
    gcs_bucket: str = Field(default=CORE_CONFIG_DEFAULT_GCS_BUCKET)

    # Single Gemini model for all agents — auth handled via ADC
    gemini_model: str = Field(default=CORE_CONFIG_DEFAULT_GEMINI_MODEL)

    # Supabase
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")
    supabase_db_url: str = Field(default="")

    # Qdrant — leave empty to fall back to local ChromaDB
    qdrant_url: str = Field(default="")
    qdrant_api_key: str = Field(default="")

    # BigQuery
    bigquery_dataset: str = Field(default=CORE_CONFIG_DEFAULT_BIGQUERY_DATASET)

    # Application
    log_level: str = Field(default=CORE_LOGGING_DEFAULT_LOG_LEVEL)
    port: int = Field(default=CORE_CONFIG_DEFAULT_PORT)

    # Empty string = auth disabled (fine for local dev)
    agentics_sdlc_api_key: str = Field(default="", alias="AGENTICS_SDLC_API_KEY")

    # Grafana hosted scrape expects basic auth on /metrics
    metrics_username: str = Field(default="", alias="METRICS_USERNAME")
    metrics_password: str = Field(default="", alias="METRICS_PASSWORD")

    # Grafana Cloud remote-write — empty disables push (local dev)
    grafana_prometheus_url: str = Field(default="", alias="GRAFANA_PROMETHEUS_URL")
    grafana_instance_id: str = Field(default="", alias="GRAFANA_INSTANCE_ID")
    grafana_api_key: str = Field(default="", alias="GRAFANA_API_KEY")

    # Comma-separated origins, or "*" for dev
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")

    # RPM per API key, 0 = no limit
    rate_limit_rpm: int = Field(default=CORE_CONFIG_DEFAULT_RATE_LIMIT_RPM, alias="RATE_LIMIT_RPM")


def core_config_validate_settings(s: CoreSettings) -> None:
    """Blow up early if GCP project ID is missing."""

    if not s.gcp_project_id:
        raise ValueError(CORE_CONFIG_MISSING_PROJECT_ID_ERROR)


@lru_cache(maxsize=1)
def core_config_get_settings() -> CoreSettings:
    """Singleton settings — created once, cached for the process lifetime."""

    return CoreSettings()
