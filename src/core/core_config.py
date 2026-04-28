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
    CORE_CONFIG_TUNED_PROTOCOL_ENDPOINT_ID_DEFAULT,
    CORE_LOGGING_DEFAULT_LOG_LEVEL,
)


class CoreSettings(BaseSettings):
    """Fail-fast Pydantic BaseSettings model loaded from environment variables and .env file.

    Field groups:
        GCP: gcp_project_id, gcp_region, gcs_bucket.
        Gemini: gemini_model, tuned_protocol_endpoint_id.
        Supabase: supabase_url, supabase_key, supabase_db_url.
        Qdrant: qdrant_url, qdrant_api_key.
        ChromaDB: chroma_path (local fallback when qdrant_url is empty).
        BigQuery: bigquery_dataset.
        Application: log_level, port.
        Auth: agentics_sdlc_api_key (empty = auth disabled).
        Grafana: metrics_username, metrics_password, grafana_prometheus_url,
            grafana_instance_id, grafana_api_key.
        CORS: allowed_origins.
        Rate Limiting: rate_limit_rpm (0 = no limit).
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

    # Tuned Protocol Gatekeeper endpoint — empty disables LLM path (local dev uses legacy heuristic)
    tuned_protocol_endpoint_id: str = Field(
        default=CORE_CONFIG_TUNED_PROTOCOL_ENDPOINT_ID_DEFAULT,
        alias="TUNED_PROTOCOL_ENDPOINT_ID",
    )

    # Supabase
    supabase_url: str = Field(default="")
    supabase_key: str = Field(default="")
    supabase_db_url: str = Field(default="")

    # Qdrant — leave empty to fall back to local ChromaDB
    qdrant_url: str = Field(default="")
    qdrant_api_key: str = Field(default="")

    # ChromaDB — local persistence path; only used when qdrant_url is empty
    chroma_path: str = Field(default="./data/chroma")

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
    """Blow up early if GCP project ID is missing.

    Args:
        s: CoreSettings instance to validate.

    Raises:
        ValueError: If gcp_project_id is empty.
    """

    if not s.gcp_project_id:
        raise ValueError(CORE_CONFIG_MISSING_PROJECT_ID_ERROR)


@lru_cache(maxsize=1)
def core_config_get_settings() -> CoreSettings:
    """Singleton settings — created once, cached for the process lifetime.

    Validates required environment variables on first call; raises immediately when
    a fail-closed invariant is violated, so the application refuses to boot rather
    than running with silently broken configuration.

    Returns:
        Singleton CoreSettings instance, created once and cached for process lifetime.

    Raises:
        ValueError: When required configuration is missing (see
            ``core_config_validate_settings``).
    """

    settings = CoreSettings()
    core_config_validate_settings(settings)
    return settings
