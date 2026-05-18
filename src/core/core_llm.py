"""Shared Gemini client via Vertex AI with tiered routing.

High tier (Pro) serves reasoning-heavy agents (ARCHITECT, REFLECTOR, ENGINEER, MANAGER);
low tier (Flash) serves classification/utility agents (PROTOCOL, LIBRARIAN, VALIDATOR).
Agent-to-tier binding lives in `CORE_LLM_AGENT_TIER_MAP`.
"""

import warnings
from functools import lru_cache

# Suppress deprecation noise from langchain's ChatVertexAI and GCS
warnings.filterwarnings("ignore", message=r"The class `ChatVertexAI` was deprecated")
warnings.filterwarnings("ignore", message=r"Support for google-cloud-storage < 3\.0\.0")

from langchain_google_vertexai import ChatVertexAI  # noqa: E402

from src.core.core_config import core_config_get_settings as get_settings  # noqa: E402
from src.core.core_utils import (  # noqa: E402
    CORE_LLM_DEFAULT_TEMPERATURE,
    CORE_LLM_DEFAULT_TIER,
    CORE_LLM_TIER_HIGH,
    CORE_LLM_TIER_LOW,
    CORE_LLM_UNKNOWN_TIER_ERROR,
)


@lru_cache(maxsize=8)
def core_llm_get_llm(
    tier: str = CORE_LLM_DEFAULT_TIER,
    temperature: float = CORE_LLM_DEFAULT_TEMPERATURE,
) -> ChatVertexAI:
    """Cached Gemini client for the requested tier. Auth via ADC — no keys needed in code.

    Args:
        tier: Either `"high"` (Pro, reasoning agents) or `"low"` (Flash, utility agents).
            Defaults to `"low"` so legacy callers receive Flash behavior unchanged.
        temperature: Sampling temperature; 0.0 for deterministic outputs,
            higher values increase creativity.

    Returns:
        Singleton ChatVertexAI instance cached on (tier, temperature) for the process lifetime.

    Raises:
        ValueError: If `tier` is not one of the supported tier values.
    """

    s = get_settings()
    if tier == CORE_LLM_TIER_HIGH:
        model_name = s.gemini_model_high
    elif tier == CORE_LLM_TIER_LOW:
        model_name = s.gemini_model_low
    else:
        raise ValueError(CORE_LLM_UNKNOWN_TIER_ERROR.format(tier=tier))
    return ChatVertexAI(
        model_name=model_name,
        project=s.gcp_project_id,
        location=s.gcp_region,
        temperature=temperature,
    )
