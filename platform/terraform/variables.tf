variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "agentics-sdlc"
}

variable "region" {
  description = "GCP region for all resources"
  type        = string
  default     = "us-central1"
}

variable "image_tag" {
  description = "Docker image tag for Cloud Run deploys"
  type        = string
  default     = "latest"
}

variable "min_instances" {
  description = "Min Cloud Run instances (0 = scale to zero)"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Max Cloud Run instances"
  type        = number
  default     = 10
}

variable "cloud_run_memory" {
  description = "Memory per Cloud Run instance"
  type        = string
  default     = "4Gi"
}

variable "cloud_run_cpu" {
  description = "vCPUs per Cloud Run instance"
  type        = string
  default     = "2"
}

variable "bigquery_dataset_id" {
  description = "BigQuery dataset for agent telemetry"
  type        = string
  default     = "agentics_sdlc_analytics"
}

variable "artifacts_bucket_name" {
  description = "GCS bucket for ML artifacts and knowledge base"
  type        = string
  default     = ""  # falls back to artifacts-{project_id} in main.tf
}
