#!/usr/bin/env bash
# Agentics SDLC Bootstrap Script
# Enables required GCP APIs and creates Terraform state bucket.
# Does NOT provision application infrastructure — that is Terraform's job.
# Usage: ./scripts/scripts_bootstrap.sh [--project PROJECT_ID] [--region REGION]

set -euo pipefail

# Defaults

PROJECT_ID="${GCP_PROJECT_ID:-agentics-sdlc}"
REGION="${GCP_REGION:-us-central1}"
TF_STATE_BUCKET="tf-state-${PROJECT_ID}"

# Argument parsing

while [[ $# -gt 0 ]]; do
    case "$1" in
        --project) PROJECT_ID="$2"; shift 2 ;;
        --region)  REGION="$2";     shift 2 ;;
        *)         echo "Unknown argument: $1"; exit 1 ;;
    esac
done

echo "=================================================="
echo " Agentics SDLC Bootstrap"
echo "  Project: ${PROJECT_ID}"
echo "  Region:  ${REGION}"
echo "=================================================="

# Step 1: Verify gcloud is authenticated

echo "[1/4] Verifying gcloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q "@"; then
    echo "ERROR: No active gcloud account. Run: gcloud auth login"
    exit 1
fi
gcloud config set project "${PROJECT_ID}"
echo "Authenticated as: $(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -1)"

# Step 2: Enable required GCP APIs

echo "[2/4] Enabling required GCP APIs..."
APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
    "storage.googleapis.com"
    "bigquery.googleapis.com"
    "secretmanager.googleapis.com"
    "iam.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "generativelanguage.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "  Enabling ${api}..."
    gcloud services enable "${api}" --project="${PROJECT_ID}" --quiet
done
echo "All APIs enabled"

# Step 3: Create Terraform state bucket (GCS)

echo "[3/4] Creating Terraform state bucket..."
if gsutil ls "gs://${TF_STATE_BUCKET}" &>/dev/null; then
    echo "Bucket gs://${TF_STATE_BUCKET} already exists"
else
    gsutil mb \
        -p "${PROJECT_ID}" \
        -l "${REGION}" \
        -b on \
        "gs://${TF_STATE_BUCKET}"
    gsutil versioning set on "gs://${TF_STATE_BUCKET}"
    echo "Created gs://${TF_STATE_BUCKET} (versioning enabled)"
fi

# Step 4: Output next steps

echo "[4/4] Bootstrap complete."
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env and fill in all values"
echo "  2. cd platform/terraform"
echo "  3. terraform init -backend-config=\"bucket=${TF_STATE_BUCKET}\""
echo "  4. terraform plan"
echo "  5. terraform apply"
echo ""
echo "TF_STATE_BUCKET=${TF_STATE_BUCKET}"
