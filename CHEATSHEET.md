# Agentics SDLC — Developer Cheatsheet

A quick-reference guide for local development, deployment, and operational commands.

## Table of Contents

- [Prerequisites](#prerequisites)
- [GCP Project Setup](#gcp-project-setup)
- [Local Development](#local-development)
- [RAG Knowledge Base](#rag-knowledge-base)
- [Testing](#testing)
- [Cloud Run Deployment](#cloud-run-deployment)
- [Terraform Infrastructure](#terraform-infrastructure)
- [Production Redeploy CI/CD](#production-redeploy-cicd)
- [LoRA Fine-tuning Pipeline](#lora-fine-tuning-pipeline)
- [Conventional Commits Protocol](#conventional-commits-protocol)

---

## Prerequisites

| Tool | Min Version | Install |
|:---|:---|:---|
| Python | 3.11+ | `pyenv install 3.11` |
| Poetry | 1.8+ | `pip install poetry` |
| gcloud CLI | any | `brew install google-cloud-sdk` |
| Docker | 24+ | `brew install --cask docker` |
| Terraform | 1.7+ | `brew install terraform` |

---

## GCP Project Setup

```bash
PROJECT_ID="agentics-sdlc"
gcloud auth login
gcloud config set project $PROJECT_ID
gcloud config set compute/region us-central1
gcloud auth application-default login
```

```bash
export GCP_PROJECT_ID="agentics-sdlc"
bash scripts/scripts_bootstrap.sh
```

### Terraform Bootstrap

```bash
TF_BUCKET="tf-state-agentics-sdlc"
cd platform/terraform
terraform init -backend-config="bucket=${TF_BUCKET}"
terraform plan -var="project_id=${PROJECT_ID}"
terraform apply -var="project_id=${PROJECT_ID}"
cd ../..
```

### Capture Terraform Outputs

```bash
cd platform/terraform
terraform output artifacts_bucket_name
terraform output artifact_registry_url
terraform output api_sa_email

# Export CI/CD service account key
terraform output -raw cicd_sa_key_base64 | python3 -c "
import sys, base64; print(base64.b64decode(sys.stdin.read().strip()).decode())
" > /tmp/agentics-sdlc-cicd-key.json
cd ../..
```

---

## Local Development

### Minimum `.env`

```dotenv
GCP_PROJECT_ID=agentics-sdlc
GCP_REGION=us-central1
GEMINI_MODEL=gemini-2.5-flash
BIGQUERY_DATASET=agentics_sdlc_analytics
LOG_LEVEL=INFO
PORT=8080
ALLOWED_ORIGINS=*
RATE_LIMIT_RPM=60

# Leave empty — disables auth for local dev
AGENTICS_SDLC_API_KEY=

# Leave empty — falls back to local ChromaDB
QDRANT_URL=
QDRANT_API_KEY=
```

### Start Local Stack

| Terminal | Command | Purpose |
|:---|:---|:---|
| 1 | `poetry run uvicorn src.api.main:create_app --factory --reload --port 8080` | API backend |
| 2 | `poetry run python scripts/scripts_rag.py` | Ingest knowledge base |
| 3 | `curl -sf http://localhost:8080/health` | Health check |

### Submit a Test Task

```bash
curl -s -X POST http://localhost:8080/api/v1/task \
  -H "Content-Type: application/json" \
  -d '{"content": "Explain the REFLECTOR confidence audit in Agentics SDLC"}' \
  | python3 -c "
import sys,json; r=json.load(sys.stdin)
print(f'Status:     {r[\"status\"]}')
print(f'Confidence: {r[\"confidence\"]:.2f}')
print(f'Latency:    {r[\"latency_ms\"]:.0f}ms')
"
```

### Verify Rate Limit Headers

```bash
curl -s -D - -X POST http://localhost:8080/api/v1/task \
  -H "Content-Type: application/json" \
  -d '{"content": "ping"}' \
  -o /dev/null | grep -i "x-ratelimit\|x-rate"
```

### Verify Prometheus Metrics

```bash
curl -s http://localhost:8080/metrics | grep "^agentics_sdlc_" | head -6
```

### Enabling the Grafana dashboard locally

The three live panels (`Active Workflows`, `Live Confidence`, `Call Rate & Error Rate (Live)`) require Grafana Cloud remote-write credentials. The `api` service in `docker-compose.yml` forwards them if they are set in `.env`:

```bash
# .env — uncomment and fill with your tenant values
GRAFANA_INSTANCE_ID=...
GRAFANA_API_KEY=glc_...
GRAFANA_PROMETHEUS_URL=https://prometheus-prod-<n>-prod-<region>.grafana.net/api/prom/push
```

Restart the container so the new env is picked up (`restart` alone does not re-evaluate env vars):

```bash
docker compose up -d --force-recreate api
```

Verify via the startup log — one of these two lines appears:

```bash
docker compose logs api | grep -i grafana
# Grafana remote-write enabled — pushing to prometheus-prod-<n>-prod-<region>.grafana.net
# Grafana remote-write disabled — GRAFANA_PROMETHEUS_URL is empty. …
```

When disabled, every workflow silently no-ops the push and the dashboard stays at "No data". When enabled, panels populate on the next workflow execution.

### Start Chainlit UI

```bash
# Generate bcrypt hash for UI auth
python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"

export UI_AUTH_PASSWORD_HASH='$2b$12$...'
poetry run chainlit run src/ui/ui_chainlit_app.py --host 0.0.0.0 --port 8000
```

---

## RAG Knowledge Base

| Command | Action |
|:---|:---|
| `poetry run python scripts/scripts_rag.py` | Incremental ingest (skips already-indexed chunks) |
| `poetry run python scripts/scripts_rag.py --reset` | Full reset: wipe collection + manifest, re-ingest |
| `poetry run python scripts/scripts_rag.py --path .agent/ --reset` | Target a custom path |

### Re-ingest Against Qdrant Cloud

```bash
QDRANT_URL=$(gcloud secrets versions access latest --secret=qdrant-url --project=$PROJECT_ID)
QDRANT_API_KEY=$(gcloud secrets versions access latest --secret=qdrant-api-key --project=$PROJECT_ID)

# Incremental (safe for routine redeploys)
QDRANT_URL=$QDRANT_URL QDRANT_API_KEY=$QDRANT_API_KEY poetry run python scripts/scripts_rag.py

# Full reset (use when chunk params or directory layout changed)
QDRANT_URL=$QDRANT_URL QDRANT_API_KEY=$QDRANT_API_KEY poetry run python scripts/scripts_rag.py --reset
```

---

## Testing

| Command | Scope |
|:---|:---|
| `poetry run pytest --cov=src --cov-report=term-missing` | All tests with coverage |
| `poetry run pytest tests/unit/` | Unit tests only |
| `poetry run pytest tests/integration/` | Integration tests only |

---

## Cloud Run Deployment

### First-Time Deploy (Service YAML)

```bash
PROJECT_ID="agentics-sdlc"
NAMESPACE=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

cd platform/terraform
REGISTRY_URL=$(terraform output -raw artifact_registry_url)
API_SA_EMAIL=$(terraform output -raw api_sa_email)
cd ../..

IMAGE="${REGISTRY_URL}/agentics-sdlc-api"

gcloud auth configure-docker gcr.io --quiet
docker build --platform linux/amd64 -f platform/docker/Dockerfile.api -t ${IMAGE}:latest .
docker push ${IMAGE}:latest

# Generate and apply the Cloud Run service manifest
cat > /tmp/agentics-sdlc-deploy.yaml << EOF
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: agentics-sdlc-api
  namespace: '${NAMESPACE}'
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: '1'
        autoscaling.knative.dev/maxScale: '10'
        run.googleapis.com/startup-cpu-boost: 'true'
    spec:
      containerConcurrency: 160
      timeoutSeconds: 300
      serviceAccountName: ${API_SA_EMAIL}
      containers:
      - image: ${IMAGE}:latest
        ports:
        - containerPort: 8080
          name: http1
        resources:
          limits:
            cpu: '2'
            memory: 4Gi
        env:
        - name: GCP_PROJECT_ID
          value: ${PROJECT_ID}
        - name: GCS_BUCKET
          value: artifacts-${PROJECT_ID}
        - name: BIGQUERY_DATASET
          value: agentics_sdlc_analytics
        - name: RATE_LIMIT_RPM
          value: '60'
        - name: ALLOWED_ORIGINS
          value: '*'
        - name: AGENTICS_SDLC_API_KEY
          valueFrom:
            secretKeyRef:
              name: agentics-sdlc-api-key
              key: latest
        - name: SUPABASE_URL
          valueFrom:
            secretKeyRef:
              name: supabase-url
              key: latest
        - name: SUPABASE_KEY
          valueFrom:
            secretKeyRef:
              name: supabase-key
              key: latest
        - name: SUPABASE_DB_URL
          valueFrom:
            secretKeyRef:
              name: supabase-db-url
              key: latest
        - name: QDRANT_URL
          valueFrom:
            secretKeyRef:
              name: qdrant-url
              key: latest
        - name: QDRANT_API_KEY
          valueFrom:
            secretKeyRef:
              name: qdrant-api-key
              key: latest
        startupProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 70
          periodSeconds: 10
          failureThreshold: 15
          timeoutSeconds: 10
        livenessProbe:
          httpGet:
            path: /liveness
            port: 8080
          periodSeconds: 30
          failureThreshold: 3
          timeoutSeconds: 5
  traffic:
  - latestRevision: true
    percent: 100
EOF

gcloud run services replace /tmp/agentics-sdlc-deploy.yaml \
  --region=us-central1 \
  --project=$PROJECT_ID
```

### Subsequent Redeploys

```bash
docker build --platform linux/amd64 -f platform/docker/Dockerfile.api -t ${IMAGE}:latest .
docker push ${IMAGE}:latest
gcloud run deploy agentics-sdlc-api \
  --image="${IMAGE}:latest" \
  --region=us-central1 \
  --project=$PROJECT_ID \
  --platform managed \
  --memory 4Gi --cpu 2 \
  --min-instances 0 --max-instances 10 \
  --timeout 300 \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCS_BUCKET=artifacts-${PROJECT_ID},BIGQUERY_DATASET=agentics_sdlc_analytics,RATE_LIMIT_RPM=60,ALLOWED_ORIGINS=*" \
  --set-secrets "AGENTICS_SDLC_API_KEY=agentics-sdlc-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,SUPABASE_DB_URL=supabase-db-url:latest,QDRANT_URL=qdrant-url:latest,QDRANT_API_KEY=qdrant-api-key:latest,METRICS_USERNAME=metrics-username:latest,METRICS_PASSWORD=metrics-password:latest"
```

### Verify API Deployment

```bash
CLOUD_RUN_URL=$(gcloud run services describe agentics-sdlc-api \
  --region=us-central1 --format="value(status.url)" --project=$PROJECT_ID)
curl -f "${CLOUD_RUN_URL}/health"

PROD_KEY=$(gcloud secrets versions access latest --secret=agentics-sdlc-api-key --project=$PROJECT_ID)
curl -s -X POST "${CLOUD_RUN_URL}/api/v1/task" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${PROD_KEY}" \
  -d '{"content": "Explain the REFLECTOR confidence audit"}' \
  | python3 -c "
import sys,json; r=json.load(sys.stdin)
print(f'Status:     {r[\"status\"]}')
print(f'Confidence: {r[\"confidence\"]:.2f}')
print(f'Latency:    {r[\"latency_ms\"]:.0f}ms')
"
```

### Deploy UI to Cloud Run

```bash
# Generate bcrypt hash and store as secret
python -c "import bcrypt; print(bcrypt.hashpw(b'your-chosen-password', bcrypt.gensalt()).decode())"
echo -n '<bcrypt-hash>' | gcloud secrets versions add ui-auth-password-hash --data-file=- --project=$GCP_PROJECT_ID

# Generate JWT secret for Chainlit session auth
openssl rand -hex 32
echo -n "<jwt-secret>" | gcloud secrets versions add chainlit-auth-secret --data-file=- --project=$GCP_PROJECT_ID

docker build --platform linux/amd64 --no-cache \
  -f platform/docker/Dockerfile.ui \
  -t gcr.io/$GCP_PROJECT_ID/agentics-sdlc-ui:latest .

docker push gcr.io/$GCP_PROJECT_ID/agentics-sdlc-ui:latest

gcloud run deploy agentics-sdlc-ui \
  --image gcr.io/$GCP_PROJECT_ID/agentics-sdlc-ui:latest \
  --region us-central1 --platform managed \
  --allow-unauthenticated \
  --memory 4Gi --cpu 2 \
  --min-instances 1 --max-instances 10 \
  --timeout 900 --session-affinity \
  --set-env-vars "GCP_PROJECT_ID=$GCP_PROJECT_ID,ENVIRONMENT=production" \
  --set-secrets "AGENTICS_SDLC_API_KEY=agentics-sdlc-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,SUPABASE_DB_URL=supabase-db-url:latest,QDRANT_URL=qdrant-url:latest,QDRANT_API_KEY=qdrant-api-key:latest,CHAINLIT_AUTH_SECRET=chainlit-auth-secret:latest,UI_AUTH_PASSWORD_HASH=ui-auth-password-hash:latest,METRICS_USERNAME=metrics-username:latest,METRICS_PASSWORD=metrics-password:latest" \
  --project $GCP_PROJECT_ID
```

### Rebuild and Deploy Both Services

```bash
PROJECT_ID="agentics-sdlc"
REGISTRY_URL=$(cd platform/terraform && terraform output -raw artifact_registry_url && cd ../..)
API_IMAGE="${REGISTRY_URL}/agentics-sdlc-api"
UI_IMAGE="gcr.io/${PROJECT_ID}/agentics-sdlc-ui"

gcloud auth configure-docker gcr.io --quiet
docker system prune -f && docker builder prune -f

# API
docker build --platform linux/amd64 --no-cache -f platform/docker/Dockerfile.api -t "${API_IMAGE}:latest" .
docker push "${API_IMAGE}:latest"
gcloud run deploy agentics-sdlc-api --image="${API_IMAGE}:latest" --region=us-central1 --project=$PROJECT_ID \
  --platform managed --memory 4Gi --cpu 2 --min-instances 0 --max-instances 10 --timeout 300 \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCS_BUCKET=artifacts-${PROJECT_ID},BIGQUERY_DATASET=agentics_sdlc_analytics,RATE_LIMIT_RPM=60,ALLOWED_ORIGINS=*" \
  --set-secrets "AGENTICS_SDLC_API_KEY=agentics-sdlc-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,SUPABASE_DB_URL=supabase-db-url:latest,QDRANT_URL=qdrant-url:latest,QDRANT_API_KEY=qdrant-api-key:latest,METRICS_USERNAME=metrics-username:latest,METRICS_PASSWORD=metrics-password:latest"

# UI
docker build --platform linux/amd64 --no-cache -f platform/docker/Dockerfile.ui -t "${UI_IMAGE}:latest" .
docker push "${UI_IMAGE}:latest"
gcloud run deploy agentics-sdlc-ui --image="${UI_IMAGE}:latest" --region=us-central1 --project=$PROJECT_ID \
  --platform managed --allow-unauthenticated --memory 4Gi --cpu 2 \
  --min-instances 1 --max-instances 10 --timeout 900 --session-affinity \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},ENVIRONMENT=production" \
  --set-secrets "AGENTICS_SDLC_API_KEY=agentics-sdlc-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,SUPABASE_DB_URL=supabase-db-url:latest,QDRANT_URL=qdrant-url:latest,QDRANT_API_KEY=qdrant-api-key:latest,CHAINLIT_AUTH_SECRET=chainlit-auth-secret:latest,UI_AUTH_PASSWORD_HASH=ui-auth-password-hash:latest,METRICS_USERNAME=metrics-username:latest,METRICS_PASSWORD=metrics-password:latest" \
  --project=$PROJECT_ID
```

---

## Terraform Infrastructure

```bash
cd platform/terraform

# Initialize with remote GCS backend
terraform init -backend-config="bucket=tf-state-agentics-sdlc"

# Plan
terraform plan -var="project_id=your-gcp-project"

# Apply
terraform apply -var="project_id=your-gcp-project"
```

### External Services Setup

| Service | Configuration |
|:---|:---|
| Qdrant Cloud | Create cluster at `cloud.qdrant.io`; store URL + API key as GCP secrets |
| Supabase | Run `platform/sql/init.sql` in the SQL editor; store URL + key + db-url as GCP secrets |
| Grafana Cloud | Create stack; configure Prometheus remote-write URL, instance ID, and API key as shell exports |

### Grafana BigQuery Data Source

```bash
cd platform/terraform
terraform output -raw grafana_sa_key_base64 | python3 -c "
import sys, base64; print(base64.b64decode(sys.stdin.read().strip()).decode())
" > /tmp/grafana-bq-key.json
cat /tmp/grafana-bq-key.json
rm /tmp/grafana-bq-key.json
cd ../..
```

### BigQuery Scheduled Queries

| KPI | Destination Table |
|:---|:---|
| Daily Agent Call Volume | `agentics_sdlc_analytics.kpi_daily_agent_call_volume` |
| Avg Confidence & Latency per Agent (7d) | `agentics_sdlc_analytics.kpi_avg_confidence_latency` |
| Low-Confidence Sessions | `agentics_sdlc_analytics.kpi_low_confidence_sessions` |

### Grafana Dashboard Import

Import `observability/grafana/agentics-sdlc-dashboard.json` in Grafana Cloud and select the Prometheus data source.

---

## Production Redeploy CI/CD

| Job | Action | Gate |
|:---|:---|:---|
| `quality` | Black, isort, Flake8, Mypy | Blocks `test` on failure |
| `test` | pytest unit tests, coverage ≥ 70%, Postgres 16 service container | Blocks `build` on failure |
| `build` | Build + push `agentics-sdlc-api:<sha>` and `agentics-sdlc-ui:<sha>` to GCR | Main branch only |
| `deploy` | Deploy API then UI to Cloud Run `us-central1`, verify `/health` | Requires `production` environment approval |

### Required GitHub Secrets and Variables

| Key | Type | Value |
|:---|:---|:---|
| `GCP_SA_JSON` | Secret | Content of CI/CD service account JSON key |
| `AGENTICS_SDLC_API_KEY` | Secret | Generated API key from GCP Secret Manager |
| `GCP_PROJECT_ID` | Variable | `agentics-sdlc` |
| `QDRANT_URL` | Variable | Qdrant cluster URL |

---

## LoRA Fine-tuning Pipeline

### Pipeline Phases

| Phase | Script / Command | Output |
|:---|:---|:---|
| 1 — Generate | `poetry run python -m src.tuning.tuning_generator` | Synthetic training examples (85% compliant, 10% adversarial, 5% edge-case) |
| 2 — Train | `poetry run python -m src.tuning.tuning_train` | Vertex AI SFT job + deployed LoRA endpoint |
| 3 — Evaluate | `poetry run python -m src.tuning.tuning_evaluate` | Precision / Recall / F1 (pass threshold: F1 ≥ 0.95) |

### Full Pipeline (Generate → Train → Evaluate)

```bash
poetry run python -m src.tuning.tuning_generator && \
poetry run python -m src.tuning.tuning_train && \
poetry run python -m src.tuning.tuning_evaluate
```

### Interactive Notebook

```bash
poetry run jupyter notebook src/tuning/notebook/notebook_exploration.ipynb
```

### Hyperparameter Reference

| Parameter | Default | Description |
|:---|:---|:---|
| `epochs` | 3 | Number of training passes |
| `learning_rate_multiplier` | 1.0 | Scales the base learning rate |
| `adapter_rank` | 4 | LoRA adapter rank (higher = more capacity) |
| `f1_threshold` | 0.95 | Minimum F1 required for evaluation pass |
| `train_split` | 0.85 | Fraction of examples used for training |

---

## Conventional Commits Protocol

| Prefix | Meaning | Semantic Version |
|:---|:---|:---|
| `feat:` | New feature | MINOR bump |
| `fix:` | Bug patch | PATCH bump |
| `docs:` | Documentation only | — |
| `style:` | Whitespace / formatting, no logic change | — |
| `refactor:` | Code restructure without API or behavior change | — |
| `test:` | Add or correct tests | — |
| `chore:` | Maintenance, dependency updates, build process | — |
| `perf:` | Performance improvement | PATCH bump |
| `ci:` | CI/CD pipeline changes | — |
