output "cloud_run_url" {
  description = "API service URL on Cloud Run"
  value       = google_cloud_run_v2_service.api.uri
}

output "ui_cloud_run_url" {
  description = "Chainlit UI service URL on Cloud Run"
  value       = google_cloud_run_v2_service.ui.uri
}

output "artifacts_bucket_name" {
  description = "GCS bucket for ML artifacts"
  value       = google_storage_bucket.artifacts.name
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset for agent telemetry"
  value       = google_bigquery_dataset.analytics.dataset_id
}

output "bigquery_table_id" {
  description = "Fully qualified BigQuery table ID"
  value       = "${var.project_id}.${google_bigquery_dataset.analytics.dataset_id}.${google_bigquery_table.agent_audit_log.table_id}"
}

output "project_id" {
  description = "GCP project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP region"
  value       = var.region
}

output "cicd_sa_key_base64" {
  description = "Base64 CI/CD service account key (store in GitHub Secrets)"
  value       = google_service_account_key.cicd.private_key
  sensitive   = true
}

output "artifact_registry_url" {
  description = "GCR base URL for container images"
  value       = "gcr.io/${var.project_id}"
}

output "api_sa_email" {
  description = "Default Compute SA email used by Cloud Run"
  value       = "${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

output "grafana_sa_key_base64" {
  description = "Base64 Grafana SA key for BigQuery reads"
  value       = google_service_account_key.grafana_bq_reader.private_key
  sensitive   = true
}
