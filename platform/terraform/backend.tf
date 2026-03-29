terraform {
  required_version = ">= 1.7.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # GCS remote state - bucket is created by bootstrap.sh
  backend "gcs" {
    # Pass bucket at init: terraform init -backend-config="bucket=tf-state-agentics-sdlc"
    prefix = "terraform/state"
  }
}
