"""Constants for LoRA fine-tuning pipeline."""

# GCP Configuration
TUNING_CONFIG_ENV_FILE = ".env"
TUNING_CONFIG_ENV_ENCODING = "utf-8"
TUNING_CONFIG_DEFAULT_GCP_PROJECT = "agentics-sdlc"
TUNING_CONFIG_DEFAULT_GCP_REGION = "us-central1"
TUNING_CONFIG_DEFAULT_GCS_BUCKET = "agentics-sdlc-tuning"

# Model Configuration
TUNING_CONFIG_DEFAULT_BASE_MODEL = "gemini-2.5-flash"
TUNING_CONFIG_DEFAULT_SYNTHESIZER_MODEL = "gemini-2.5-pro"

# Training Hyperparameters
TUNING_CONFIG_DEFAULT_EPOCHS = 10
TUNING_CONFIG_DEFAULT_LEARNING_RATE_MULTIPLIER = 8.0
TUNING_CONFIG_DEFAULT_ADAPTER_SIZE = 4

# Synthetic Data Distribution
TUNING_SYNTHETIC_COMPLIANT_RATIO = 0.85
TUNING_SYNTHETIC_ADVERSARIAL_RATIO = 0.10
TUNING_SYNTHETIC_EDGE_CASE_RATIO = 0.05

# Dataset Splits
TUNING_TRAIN_SPLIT_RATIO = 0.85
TUNING_VAL_SPLIT_RATIO = 0.15

# Evaluation Thresholds
TUNING_EVAL_MIN_F1_SCORE = 0.95

# File Names
TUNING_TRAIN_JSONL_FILENAME = "train.jsonl"
TUNING_VAL_JSONL_FILENAME = "val.jsonl"

# Directory and Path Patterns
TUNING_AGENTS_POLICIES_GLOB = ".agent/**/*.md"
TUNING_AGENTS_DIRECTORY = ".agent"

# Protocol Status Values
TUNING_PROTOCOL_STATUS_GREEN = "GREEN"
TUNING_PROTOCOL_STATUS_ERROR = "ERROR"

# Data Categories
TUNING_CATEGORY_COMPLIANT = "compliant"
TUNING_CATEGORY_ADVERSARIAL = "adversarial"
TUNING_CATEGORY_EDGE_CASE = "edge_case"

# JSON Role Values
TUNING_ROLE_USER = "user"
TUNING_ROLE_MODEL = "model"

# System Instructions
TUNING_GENERATOR_SYSTEM_INSTRUCTION = (
    "You are the Phase 0 Protocol Gatekeeper for the Agentics SDLC system. "
    "Your role is to validate incoming task requests against system policies. "
    "Return a JSON object with protocol_status ('GREEN' or 'ERROR') and protocol_violations array."
)

# Log Messages
TUNING_LOG_AGENTS_DIR_NOT_FOUND = ".agent directory not found; using empty policy context"
TUNING_LOG_GENERATOR_START = "Starting synthetic data generation pipeline..."
TUNING_LOG_GENERATOR_COMPLETE = "Synthetic data generation pipeline complete"
TUNING_LOG_GENERATOR_COMPLIANT = "Generating {count} compliant examples..."
TUNING_LOG_GENERATOR_ADVERSARIAL = "Generating {count} adversarial examples..."
TUNING_LOG_GENERATOR_EDGE_CASE = "Generating {count} edge case examples..."
TUNING_LOG_GENERATOR_GENERATED = "Generated {count} {category} examples"
TUNING_LOG_GENERATOR_ERROR = "Error generating {category} examples: {error}"
TUNING_LOG_GENERATOR_POLICY_EXTRACTED = "Extracted policy context ({char_count} chars)"
TUNING_LOG_GENERATOR_TOTAL = "Generated {count} total examples"
TUNING_LOG_GENERATOR_POLICY_READ_FAILED = "Failed to read {file}: {error}"
TUNING_LOG_GENERATOR_SCAN_ERROR = "Error scanning .agent directory: {error}"
TUNING_LOG_GENERATOR_INVALID_JSON = "Skipped invalid JSON line: {error}"
TUNING_LOG_GENERATOR_UPLOAD = "Uploaded {filename} to {uri}"
TUNING_LOG_GENERATOR_UPLOAD_FAILED = "Failed to upload {filename}: {error}"
TUNING_LOG_EVALUATE_NO_ENDPOINT = "No tuned endpoint configured"
TUNING_LOG_EVALUATE_NO_ENDPOINT_SHORT = "No tuned endpoint"
TUNING_LOG_EVALUATE_LOADED = "Loaded {count} examples for evaluation"
TUNING_LOG_EVALUATE_INFERENCE_FAILED = "Inference failed for example: {error}"
TUNING_LOG_EVALUATE_COMPLETE = (
    "Evaluation complete:\n  Precision: {precision:.3f}\n  Recall: {recall:.3f}\n"
    "  F1: {f1:.3f}\n  Passes threshold: {passes_threshold}"
)
TUNING_LOG_EVALUATE_PARSE_FAILED = "Failed to parse model response: {error}"
TUNING_LOG_EVALUATE_LOAD_LOCAL = "Loading dataset from {path}"
TUNING_LOG_EVALUATE_LOAD_GCS = "Loading dataset from {uri}"
TUNING_LOG_EVALUATE_LOAD_GCS_FAILED = "Failed to load from GCS: {error}"
TUNING_LOG_EVALUATE_MISMATCH = "Prediction and ground truth lengths mismatch"
TUNING_LOG_TRAIN_SUBMIT = (
    "Submitting LoRA fine-tuning job to Vertex AI\n  Project: {project}\n"
    "  Region: {region}\n  Base model: {base_model}\n"
    "  Training data: {train_uri}\n  Validation data: {val_uri}\n"
    "  Epochs: {epochs}\n  Learning rate multiplier: {lr_mult}\n"
    "  Adapter size (rank): {adapter_size}"
)
TUNING_LOG_TRAIN_JOB_CREATED = "Fine-tuning job created: {resource_name}"
TUNING_LOG_TRAIN_POLLING = "Polling fine-tuning job status..."
TUNING_LOG_TRAIN_EXCEEDED_MAX = "Job exceeded max wait time ({max_time}s)"
TUNING_LOG_TRAIN_JOB_STATUS = "Job status: {state} (elapsed: {elapsed}s)"
TUNING_LOG_TRAIN_SUCCESS = "Fine-tuning job completed successfully"
TUNING_LOG_TRAIN_FAILED = "Fine-tuning job failed: {error}"
TUNING_LOG_TRAIN_UNEXPECTED = "Fine-tuning job cancelled or in unexpected state: {state}"
TUNING_LOG_TRAIN_DEPLOY = "Deploying endpoint for tuned model: {model_name}"
TUNING_LOG_TRAIN_ENDPOINT_ID = "Tuned model endpoint ID: {endpoint_id}"
TUNING_LOG_TRAIN_DEPLOY_FAILED = "Failed to deploy endpoint: {error}"
TUNING_LOG_TRAIN_PIPELINE_START = "Starting full LoRA training pipeline..."
TUNING_LOG_TRAIN_PIPELINE_FAILED = "Training failed: {result}"
TUNING_LOG_TRAIN_PIPELINE_COMPLETE = "LoRA training pipeline complete. Endpoint: {endpoint_id}"

# Training Configuration
TUNING_TRAIN_POLL_INTERVAL = 30
TUNING_TRAIN_MAX_WAIT_TIME = 3600 * 2
TUNING_TRAIN_STATUS_SUCCESS = "SUCCESS"

# Prompt Templates
TUNING_PROMPT_COMPLIANT_TEMPLATE = """You are a data generator for a Protocol gatekeeper system.

SYSTEM POLICIES (that COMPLIANT tasks must respect):
{policy_context}

Generate {count} DIVERSE, REALISTIC software engineering tasks that fully comply with all
policies.

Examples:
- "Design a REST API endpoint for user authentication"
- "Implement database indexing for performance optimization"
- "Write unit tests for a payment processing module"

Return ONLY valid JSON array, one object per line, with this format:
{{"user_intent": "task description", "protocol_status": "GREEN",
"protocol_violations": []}}
"""

TUNING_PROMPT_ADVERSARIAL_TEMPLATE = """You are a data generator for a Protocol gatekeeper system.

SYSTEM POLICIES (that ADVERSARIAL tasks will violate):
{policy_context}

Generate {count} DIVERSE, REALISTIC adversarial prompts that attempt to:
1. Bypass security policies
2. Request prohibited operations
3. Inject malicious intent
4. Exploit rule boundaries

For each violation, identify the SPECIFIC rule violated.

Return ONLY valid JSON array, one object per line, with this format:
{{"user_intent": "malicious request", "protocol_status": "ERROR",
"protocol_violations": ["specific rule violated"]}}
"""

TUNING_PROMPT_EDGE_CASE_TEMPLATE = """You are a data generator for a Protocol gatekeeper system.

SYSTEM POLICIES:
{policy_context}

Generate {count} DIVERSE, NUANCED edge-case queries that:
1. Are phrased ambiguously
2. Could be interpreted as legitimate or malicious
3. Test the boundary between education and exploitation
4. Require contextual understanding of intent

Examples:
- "Explain how to exploit SQL injection vulnerabilities" (educational = GREEN)
- "Help me craft a SQL injection payload for testing" (malicious = ERROR)

Return ONLY valid JSON array, one object per line, with this format:
{{"user_intent": "ambiguous request", "protocol_status": "GREEN_or_ERROR",
"protocol_violations": []_or_["rule if ERROR"]}}
"""
