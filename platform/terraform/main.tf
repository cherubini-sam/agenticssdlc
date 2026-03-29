provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  artifacts_bucket = coalesce(
    var.artifacts_bucket_name,
    "artifacts-${var.project_id}"
  )
  image = "gcr.io/${var.project_id}/agentics-sdlc-api:${var.image_tag}"
  # Throwaway image for first apply — CI/CD deploys the real one
  bootstrap_image = "us-docker.pkg.dev/cloudrun/container/hello:latest"
}

# GCS bucket: ML artifacts, knowledge base, MLflow runs

resource "google_storage_bucket" "artifacts" {
  name          = local.artifacts_bucket
  location      = var.region
  project       = var.project_id
  force_destroy = false

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

# BigQuery: agent telemetry & audit

resource "google_bigquery_dataset" "analytics" {
  dataset_id                  = var.bigquery_dataset_id
  project                     = var.project_id
  location                    = var.region
  description                 = "Agentics SDLC agent telemetry and audit logs"
  delete_contents_on_destroy  = false
}

resource "google_bigquery_table" "agent_audit_log" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  table_id   = "agent_audit_log"
  project    = var.project_id

  deletion_protection = true

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["agent_name"]

  schema = jsonencode([
    { name = "session_id",   type = "STRING",    mode = "REQUIRED" },
    { name = "agent_name",   type = "STRING",    mode = "REQUIRED" },
    { name = "phase",        type = "INTEGER",   mode = "REQUIRED" },
    { name = "latency_ms",   type = "FLOAT64",   mode = "REQUIRED" },
    { name = "confidence",   type = "FLOAT64",   mode = "REQUIRED" },
    { name = "status",       type = "STRING",    mode = "REQUIRED" },
    { name = "task_content", type = "STRING",    mode = "NULLABLE" },
    { name = "error",        type = "STRING",    mode = "NULLABLE" },
    { name = "timestamp",    type = "TIMESTAMP", mode = "REQUIRED" },
  ])
}

# Secret Manager: API keys & service credentials

resource "google_secret_manager_secret" "agentics_sdlc_api_key" {
  secret_id = "agentics-sdlc-api-key"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "qdrant_url" {
  secret_id = "qdrant-url"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "qdrant_api_key" {
  secret_id = "qdrant-api-key"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "supabase_url" {
  secret_id = "supabase-url"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "supabase_key" {
  secret_id = "supabase-key"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "supabase_db_url" {
  secret_id = "supabase-db-url"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "chainlit_auth_secret" {
  secret_id = "chainlit-auth-secret"
  project   = var.project_id

  replication {
    auto {}
  }
}

# Cloud Run: API service

resource "google_cloud_run_v2_service" "api" {
  name     = "agentics-sdlc-api"
  location = var.region
  project  = var.project_id

  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = local.bootstrap_image

      resources {
        limits = {
          memory = var.cloud_run_memory
          cpu    = var.cloud_run_cpu
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "GCS_BUCKET"
        value = local.artifacts_bucket
      }

      env {
        name  = "BIGQUERY_DATASET"
        value = var.bigquery_dataset_id
      }

      # Secrets (GOOGLE_API_KEY, etc.) are wired up by CI/CD via --set-secrets
      # after the first version is populated. Terraform only creates the shells.

      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 70
        timeout_seconds       = 10
        period_seconds        = 10
        failure_threshold     = 15
      }

      liveness_probe {
        http_get {
          path = "/liveness"
          port = 8080
        }
        period_seconds    = 30
        timeout_seconds   = 5
        failure_threshold = 3
      }
    }

    timeout = "300s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].containers[0].env,
    ]
  }
}

# Cloud Run: Chainlit UI

locals {
  ui_image           = "gcr.io/${var.project_id}/agentics-sdlc-ui:${var.image_tag}"
  ui_bootstrap_image = "us-docker.pkg.dev/cloudrun/container/hello:latest"
}

resource "google_cloud_run_v2_service" "ui" {
  name     = "agentics-sdlc-ui"
  location = var.region
  project  = var.project_id

  template {
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = local.ui_bootstrap_image

      resources {
        limits = {
          memory = var.cloud_run_memory
          cpu    = var.cloud_run_cpu
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 70
        timeout_seconds       = 10
        period_seconds        = 10
        failure_threshold     = 15
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        period_seconds    = 30
        timeout_seconds   = 5
        failure_threshold = 3
      }
    }

    # Chainlit uses WebSockets, so give it a longer request timeout
    timeout = "900s"
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      template[0].containers[0].env,
    ]
  }
}

# Public access — auth is handled inside the app via Chainlit's auth secret
resource "google_cloud_run_v2_service_iam_member" "ui_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.ui.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Let the default Compute SA read secrets at runtime
data "google_project" "current" {
  project_id = var.project_id
}

resource "google_project_iam_member" "compute_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com"
}

# CI/CD service account (GitHub Actions)

resource "google_service_account" "cicd" {
  account_id   = "agentics-sdlc-cicd"
  display_name = "Agentics SDLC CI/CD"
  project      = var.project_id
}

resource "google_project_iam_member" "cicd_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_service_account_key" "cicd" {
  service_account_id = google_service_account.cicd.name
}

# Grafana SA: read-only BigQuery access for dashboards

resource "google_service_account" "grafana_bq_reader" {
  account_id   = "grafana-bigquery-reader"
  display_name = "Grafana BigQuery Reader"
  project      = var.project_id
}

resource "google_project_iam_member" "grafana_bq_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.grafana_bq_reader.email}"
}

resource "google_project_iam_member" "grafana_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.grafana_bq_reader.email}"
}

resource "google_service_account_key" "grafana_bq_reader" {
  service_account_id = google_service_account.grafana_bq_reader.name
}

# Public access — the API enforces its own key-based auth
resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
