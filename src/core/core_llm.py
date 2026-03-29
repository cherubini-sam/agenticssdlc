"""Shared Gemini Flash client via Vertex AI."""

import warnings
from functools import lru_cache

# Suppress deprecation noise from langchain's ChatVertexAI and GCS
warnings.filterwarnings("ignore", message=r"The class `ChatVertexAI` was deprecated")
warnings.filterwarnings("ignore", message=r"Support for google-cloud-storage < 3\.0\.0")

from langchain_google_vertexai import ChatVertexAI  # noqa: E402

from src.core.core_config import core_config_get_settings as get_settings  # noqa: E402
from src.core.core_utils import CORE_LLM_DEFAULT_TEMPERATURE  # noqa: E402


@lru_cache(maxsize=1)
def core_llm_get_llm(temperature: float = CORE_LLM_DEFAULT_TEMPERATURE) -> ChatVertexAI:
    """Cached Gemini client. Auth via ADC — no keys needed in code."""

    s = get_settings()
    return ChatVertexAI(
        model_name=s.gemini_model,
        project=s.gcp_project_id,
        location=s.gcp_region,
        temperature=temperature,
    )
