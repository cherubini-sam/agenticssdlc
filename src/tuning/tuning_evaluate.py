"""Evaluate fine-tuned Protocol gatekeeper against holdout validation dataset."""

import json
import logging
from pathlib import Path

from langchain_google_vertexai import ChatVertexAI

from src.tuning.tuning_config import tuning_config_settings_get
from src.tuning.tuning_utils import (
    TUNING_EVAL_MIN_F1_SCORE,
    TUNING_LOG_EVALUATE_COMPLETE,
    TUNING_LOG_EVALUATE_INFERENCE_FAILED,
    TUNING_LOG_EVALUATE_LOAD_GCS,
    TUNING_LOG_EVALUATE_LOAD_GCS_FAILED,
    TUNING_LOG_EVALUATE_LOAD_LOCAL,
    TUNING_LOG_EVALUATE_LOADED,
    TUNING_LOG_EVALUATE_MISMATCH,
    TUNING_LOG_EVALUATE_NO_ENDPOINT,
    TUNING_LOG_EVALUATE_NO_ENDPOINT_SHORT,
    TUNING_LOG_EVALUATE_PARSE_FAILED,
    TUNING_PROTOCOL_STATUS_ERROR,
    TUNING_PROTOCOL_STATUS_GREEN,
)

logger = logging.getLogger(__name__)


class TuningEvaluate:
    """Compute precision, recall, and F1 for classification gatekeeper."""

    def __init__(self, endpoint_id: str = None, project_id: str = None):
        """Initialize evaluator with tuned endpoint."""

        self.settings = tuning_config_settings_get()
        self.endpoint_id = endpoint_id or self.settings.tuned_protocol_endpoint_id
        self.project_id = project_id or self.settings.gcp_project_id

        if self.endpoint_id:
            self.model_client = ChatVertexAI(
                model_name=self.endpoint_id,
                project=self.project_id,
                location=self.settings.gcp_region,
            )
        else:
            self.model_client = None

        self.logger = logging.getLogger(__name__)

    async def tuning_evaluate_on_dataset(self, jsonl_path: str = None, gcs_uri: str = None) -> dict:
        """Evaluate model on validation dataset.

        Args:
            jsonl_path: Local filesystem path to a JSONL validation file; used
                when the file exists on disk.
            gcs_uri: GCS URI to a JSONL validation file; used as fallback when
                jsonl_path is absent or does not exist.

        Returns:
            Dict with keys: true_positives, false_positives, false_negatives,
            precision, recall, f1, evaluated_examples, min_f1_threshold,
            passes_threshold. Returns an error status dict when no endpoint
            is configured.
        """

        if not self.model_client:
            self.logger.error(TUNING_LOG_EVALUATE_NO_ENDPOINT)
            return {"status": "ERROR", "message": TUNING_LOG_EVALUATE_NO_ENDPOINT_SHORT}

        examples = await self._tuning_evaluate_load_dataset(jsonl_path, gcs_uri)
        self.logger.info(TUNING_LOG_EVALUATE_LOADED.format(count=len(examples)))

        predictions = []
        ground_truth = []

        for example in examples:
            try:
                user_intent = example.get("user_intent", "")
                expected = example.get("protocol_decision", {})

                prediction = await self._tuning_evaluate_invoke_model(user_intent)
                predictions.append(prediction)

                gt_status = expected.get("protocol_status", "GREEN")
                ground_truth.append(gt_status)

            except Exception as e:
                self.logger.warning(TUNING_LOG_EVALUATE_INFERENCE_FAILED.format(error=e))

        metrics = self._tuning_evaluate_compute_metrics(predictions, ground_truth)
        metrics["evaluated_examples"] = len(predictions)
        metrics["min_f1_threshold"] = TUNING_EVAL_MIN_F1_SCORE
        metrics["passes_threshold"] = metrics["f1"] >= TUNING_EVAL_MIN_F1_SCORE

        self.logger.info(
            TUNING_LOG_EVALUATE_COMPLETE.format(
                precision=metrics["precision"],
                recall=metrics["recall"],
                f1=metrics["f1"],
                passes_threshold=metrics["passes_threshold"],
            )
        )

        return metrics

    async def _tuning_evaluate_invoke_model(self, user_intent: str) -> str:
        """Invoke tuned model."""

        try:
            response = await self.model_client.ainvoke(user_intent)

            if isinstance(response, str):
                obj = json.loads(response)
            else:
                obj = response.dict() if hasattr(response, "dict") else response

            return obj.get("protocol_status", TUNING_PROTOCOL_STATUS_GREEN)
        except Exception as e:
            self.logger.debug(TUNING_LOG_EVALUATE_PARSE_FAILED.format(error=e))
            return TUNING_PROTOCOL_STATUS_GREEN

    async def _tuning_evaluate_load_dataset(
        self, jsonl_path: str = None, gcs_uri: str = None
    ) -> list:
        """Load validation dataset."""

        examples = []

        if jsonl_path and Path(jsonl_path).exists():
            self.logger.info(TUNING_LOG_EVALUATE_LOAD_LOCAL.format(path=jsonl_path))
            with open(jsonl_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            examples.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

        elif gcs_uri:
            self.logger.info(TUNING_LOG_EVALUATE_LOAD_GCS.format(uri=gcs_uri))
            try:
                from google.cloud import storage

                parts = gcs_uri.replace("gs://", "").split("/", 1)
                bucket_name = parts[0]
                blob_path = parts[1] if len(parts) > 1 else "val.jsonl"

                client = storage.Client(project=self.project_id)
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(blob_path)
                content = blob.download_as_string().decode("utf-8")

                for line in content.split("\n"):
                    if line.strip():
                        try:
                            examples.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                self.logger.error(TUNING_LOG_EVALUATE_LOAD_GCS_FAILED.format(error=e))

        return examples

    def _tuning_evaluate_compute_metrics(
        self, predictions: list[str], ground_truth: list[str]
    ) -> dict:
        """Compute precision, recall, and F1 for binary ERROR/GREEN classification.

        Args:
            predictions: Model-predicted protocol_status values.
            ground_truth: Ground-truth protocol_status values aligned with predictions.

        Returns:
            Dict with keys: true_positives, false_positives, false_negatives,
            precision, recall, f1. All float metrics are in [0.0, 1.0].
        """

        if len(predictions) != len(ground_truth):
            self.logger.warning(TUNING_LOG_EVALUATE_MISMATCH)

        tp = sum(
            1
            for p, gt in zip(predictions, ground_truth)
            if p == TUNING_PROTOCOL_STATUS_ERROR and gt == TUNING_PROTOCOL_STATUS_ERROR
        )
        fp = sum(
            1
            for p, gt in zip(predictions, ground_truth)
            if p == TUNING_PROTOCOL_STATUS_ERROR and gt == TUNING_PROTOCOL_STATUS_GREEN
        )
        fn = sum(
            1
            for p, gt in zip(predictions, ground_truth)
            if p == TUNING_PROTOCOL_STATUS_GREEN and gt == TUNING_PROTOCOL_STATUS_ERROR
        )

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }


async def tuning_evaluate_tuned_endpoint(
    endpoint_id: str = None, validation_uri: str = None
) -> dict:
    """Evaluate tuned endpoint.

    Args:
        endpoint_id: Vertex AI endpoint ID of the fine-tuned model; falls back
            to the value in TuningSettings when None.
        validation_uri: GCS URI of the JSONL validation file.

    Returns:
        Evaluation metrics dict as returned by tuning_evaluate_on_dataset.
    """

    evaluator = TuningEvaluate(endpoint_id=endpoint_id)
    return await evaluator.tuning_evaluate_on_dataset(gcs_uri=validation_uri)
