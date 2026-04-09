"""LoRA Fine-Tuning Module for Agentics SDLC."""

from src.tuning.tuning_config import (
    ProtocolDecision,
    SyntheticDataPoint,
    TuningSettings,
    tuning_config_settings_get,
)

__all__ = [
    "ProtocolDecision",
    "SyntheticDataPoint",
    "TuningSettings",
    "tuning_config_settings_get",
    "TuningGenerator",
    "TuningTrain",
    "TuningEvaluate",
    "tuning_evaluate_tuned_endpoint",
]


def __getattr__(name: str):
    """Lazy-import heavy modules only when accessed directly."""

    if name == "TuningTrain":
        from src.tuning.tuning_train import TuningTrain

        return TuningTrain
    if name == "TuningGenerator":
        from src.tuning.tuning_generator import TuningGenerator

        return TuningGenerator
    if name in ("TuningEvaluate", "tuning_evaluate_tuned_endpoint"):
        from src.tuning import tuning_evaluate

        return getattr(tuning_evaluate, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
