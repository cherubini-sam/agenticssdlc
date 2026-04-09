"""LLM-driven synthetic data generation for LoRA fine-tuning."""

import json
import logging
import random
from pathlib import Path

from google.cloud import storage
from langchain_google_vertexai import ChatVertexAI

from src.tuning.tuning_config import SyntheticDataPoint, tuning_config_settings_get
from src.tuning.tuning_utils import (
    TUNING_AGENTS_DIRECTORY,
    TUNING_CATEGORY_ADVERSARIAL,
    TUNING_CATEGORY_COMPLIANT,
    TUNING_CATEGORY_EDGE_CASE,
    TUNING_GENERATOR_SYSTEM_INSTRUCTION,
    TUNING_LOG_AGENTS_DIR_NOT_FOUND,
    TUNING_LOG_GENERATOR_ADVERSARIAL,
    TUNING_LOG_GENERATOR_COMPLETE,
    TUNING_LOG_GENERATOR_COMPLIANT,
    TUNING_LOG_GENERATOR_EDGE_CASE,
    TUNING_LOG_GENERATOR_ERROR,
    TUNING_LOG_GENERATOR_GENERATED,
    TUNING_LOG_GENERATOR_INVALID_JSON,
    TUNING_LOG_GENERATOR_POLICY_EXTRACTED,
    TUNING_LOG_GENERATOR_POLICY_READ_FAILED,
    TUNING_LOG_GENERATOR_SCAN_ERROR,
    TUNING_LOG_GENERATOR_START,
    TUNING_LOG_GENERATOR_TOTAL,
    TUNING_LOG_GENERATOR_UPLOAD,
    TUNING_LOG_GENERATOR_UPLOAD_FAILED,
    TUNING_PROMPT_ADVERSARIAL_TEMPLATE,
    TUNING_PROMPT_COMPLIANT_TEMPLATE,
    TUNING_PROMPT_EDGE_CASE_TEMPLATE,
    TUNING_PROTOCOL_STATUS_GREEN,
    TUNING_ROLE_MODEL,
    TUNING_ROLE_USER,
    TUNING_SYNTHETIC_ADVERSARIAL_RATIO,
    TUNING_SYNTHETIC_COMPLIANT_RATIO,
    TUNING_SYNTHETIC_EDGE_CASE_RATIO,
    TUNING_TRAIN_SPLIT_RATIO,
)

logger = logging.getLogger(__name__)


class TuningGenerator:
    """Generate synthetic training data for Protocol gatekeeper fine-tuning."""

    def __init__(self, project_id: str = None, gcs_bucket: str = None):
        """Initialize generator with GCP and storage configuration."""

        self.settings = tuning_config_settings_get()
        self.project_id = project_id or self.settings.gcp_project_id
        self.gcs_bucket = gcs_bucket or self.settings.gcs_bucket
        self.gcs_client = storage.Client(project=self.project_id)
        self.synthesizer = ChatVertexAI(
            model_name=self.settings.synthesizer_model,
            project=self.project_id,
            location=self.settings.gcp_region,
        )
        self.logger = logging.getLogger(__name__)

    def tuning_generator_extract_policies(self) -> str:
        """Parse .agent directory and extract policy text."""

        agents_dir = Path(TUNING_AGENTS_DIRECTORY)
        if not agents_dir.exists():
            self.logger.warning(TUNING_LOG_AGENTS_DIR_NOT_FOUND)
            return ""

        policies = []
        try:
            for md_file in agents_dir.glob("**/*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    cleaned = self._tuning_generator_clean_markdown(content)
                    if cleaned:
                        policies.append(cleaned)
                except Exception as e:
                    self.logger.warning(
                        TUNING_LOG_GENERATOR_POLICY_READ_FAILED.format(file=md_file, error=e)
                    )
        except Exception as e:
            self.logger.error(TUNING_LOG_GENERATOR_SCAN_ERROR.format(error=e))

        return "\n\n".join(policies)

    def _tuning_generator_clean_markdown(self, content: str) -> str:
        """Remove extraneous markdown formatting while preserving semantic content."""

        lines = []
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("---"):
                lines.append(stripped)
        return "\n".join(lines[:500])

    async def tuning_generator_generate_compliant(
        self, policy_context: str, count: int = 100
    ) -> list[SyntheticDataPoint]:
        """Generate compliant training examples."""

        prompt = TUNING_PROMPT_COMPLIANT_TEMPLATE.format(
            policy_context=policy_context,
            count=count,
        )
        self.logger.info(TUNING_LOG_GENERATOR_COMPLIANT.format(count=count))
        return await self._tuning_generator_generate_examples(
            prompt, count, category=TUNING_CATEGORY_COMPLIANT
        )

    async def tuning_generator_generate_adversarial(
        self, policy_context: str, count: int = 10
    ) -> list[SyntheticDataPoint]:
        """Generate adversarial training examples."""

        prompt = TUNING_PROMPT_ADVERSARIAL_TEMPLATE.format(
            policy_context=policy_context,
            count=count,
        )
        self.logger.info(TUNING_LOG_GENERATOR_ADVERSARIAL.format(count=count))
        return await self._tuning_generator_generate_examples(
            prompt, count, category=TUNING_CATEGORY_ADVERSARIAL
        )

    async def tuning_generator_generate_edge_case(
        self, policy_context: str, count: int = 5
    ) -> list[SyntheticDataPoint]:
        """Generate edge case training examples."""

        prompt = TUNING_PROMPT_EDGE_CASE_TEMPLATE.format(
            policy_context=policy_context,
            count=count,
        )
        self.logger.info(TUNING_LOG_GENERATOR_EDGE_CASE.format(count=count))
        return await self._tuning_generator_generate_examples(
            prompt, count, category=TUNING_CATEGORY_EDGE_CASE
        )

    async def _tuning_generator_generate_examples(
        self, prompt: str, count: int, category: str
    ) -> list[SyntheticDataPoint]:
        """Call synthesizer and parse structured output."""

        try:
            response = await self.synthesizer.ainvoke(prompt)
            examples = self._tuning_generator_parse_json_response(response, category)
            self.logger.info(
                TUNING_LOG_GENERATOR_GENERATED.format(count=len(examples), category=category)
            )
            return examples
        except Exception as e:
            self.logger.error(TUNING_LOG_GENERATOR_ERROR.format(category=category, error=e))
            return []

    def _tuning_generator_parse_json_response(
        self, response: str, category: str
    ) -> list[SyntheticDataPoint]:
        """Parse LLM JSON response into SyntheticDataPoint objects."""

        from src.tuning.tuning_config import ProtocolDecision

        examples = []
        for line in response.split("\n"):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                decision = ProtocolDecision(
                    protocol_status=obj.get("protocol_status", TUNING_PROTOCOL_STATUS_GREEN),
                    protocol_violations=obj.get("protocol_violations", []),
                )
                examples.append(
                    SyntheticDataPoint(
                        user_intent=obj.get("user_intent", ""),
                        protocol_decision=decision,
                        category=category,
                    )
                )
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.debug(TUNING_LOG_GENERATOR_INVALID_JSON.format(error=e))
        return examples

    def tuning_generator_format_jsonl(self, examples: list[SyntheticDataPoint]) -> str:
        """Format examples into Vertex AI SFT JSONL schema."""

        jsonl_lines = []
        system_instruction = {
            "role": TUNING_ROLE_USER,
            "parts": [{"text": TUNING_GENERATOR_SYSTEM_INSTRUCTION}],
        }

        for example in examples:
            entry = {
                "systemInstruction": system_instruction,
                "contents": [
                    {"role": TUNING_ROLE_USER, "parts": [{"text": example.user_intent}]},
                    {
                        "role": TUNING_ROLE_MODEL,
                        "parts": [{"text": example.protocol_decision.model_dump_json()}],
                    },
                ],
            }
            jsonl_lines.append(json.dumps(entry))

        return "\n".join(jsonl_lines)

    def tuning_generator_upload_gcs(self, jsonl_content: str, is_training: bool = True) -> str:
        """Upload JSONL dataset to GCS bucket."""

        filename = "train.jsonl" if is_training else "val.jsonl"
        bucket = self.gcs_client.bucket(self.gcs_bucket)
        blob = bucket.blob(filename)

        try:
            blob.upload_from_string(jsonl_content, content_type="application/jsonlines")
            uri = f"gs://{self.gcs_bucket}/{filename}"
            self.logger.info(TUNING_LOG_GENERATOR_UPLOAD.format(filename=filename, uri=uri))
            return uri
        except Exception as e:
            self.logger.error(TUNING_LOG_GENERATOR_UPLOAD_FAILED.format(filename=filename, error=e))
            raise

    async def tuning_generator_generate_datasets(self) -> tuple[str, str]:
        """Orchestrate complete synthetic data pipeline."""

        self.logger.info(TUNING_LOG_GENERATOR_START)

        policy_context = self.tuning_generator_extract_policies()
        self.logger.info(
            TUNING_LOG_GENERATOR_POLICY_EXTRACTED.format(char_count=len(policy_context))
        )

        compliant_count = int(100 * TUNING_SYNTHETIC_COMPLIANT_RATIO)
        adversarial_count = int(100 * TUNING_SYNTHETIC_ADVERSARIAL_RATIO)
        edge_case_count = int(100 * TUNING_SYNTHETIC_EDGE_CASE_RATIO)

        compliant_examples = await self.tuning_generator_generate_compliant(
            policy_context, count=compliant_count
        )
        adversarial_examples = await self.tuning_generator_generate_adversarial(
            policy_context, count=adversarial_count
        )
        edge_case_examples = await self.tuning_generator_generate_edge_case(
            policy_context, count=edge_case_count
        )

        all_examples = compliant_examples + adversarial_examples + edge_case_examples
        self.logger.info(TUNING_LOG_GENERATOR_TOTAL.format(count=len(all_examples)))

        random.shuffle(all_examples)
        split_idx = int(len(all_examples) * TUNING_TRAIN_SPLIT_RATIO)
        train_examples = all_examples[:split_idx]
        val_examples = all_examples[split_idx:]

        train_jsonl = self.tuning_generator_format_jsonl(train_examples)
        val_jsonl = self.tuning_generator_format_jsonl(val_examples)

        train_uri = self.tuning_generator_upload_gcs(train_jsonl, is_training=True)
        val_uri = self.tuning_generator_upload_gcs(val_jsonl, is_training=False)

        self.logger.info(TUNING_LOG_GENERATOR_COMPLETE)
        return train_uri, val_uri
