# Agentics Build & Deploy

## Table of Contents

- [Agentics Build \& Deploy](#agentics-build--deploy)
  - [Table of Contents](#table-of-contents)
  - [1. GCP Project Setup](#1-gcp-project-setup)
  - [2. Vertex AI (LLM)](#2-vertex-ai-llm)
  - [3. API Key](#3-api-key)
  - [4. Qdrant Cloud (Vector Store)](#4-qdrant-cloud-vector-store)
  - [5. Supabase (Audit Trail)](#5-supabase-audit-trail)
  - [6. Grafana Cloud (Observability)](#6-grafana-cloud-observability)
  - [7. GitHub Configuration](#7-github-configuration)
  - [8. Local Development](#8-local-development)
  - [9. Local Stack \& First Test](#9-local-stack--first-test)
  - [10. Deploy API to Cloud Run](#10-deploy-api-to-cloud-run)
    - [First-Time Deploy (Service YAML)](#first-time-deploy-service-yaml)
    - [Subsequent Redeploys](#subsequent-redeploys)
    - [Verify](#verify)
  - [11. Deploy UI to Cloud Run](#11-deploy-ui-to-cloud-run)
  - [12. BigQuery Scheduled Queries](#12-bigquery-scheduled-queries)
  - [13. Grafana Dashboard](#13-grafana-dashboard)
  - [14. Production Redeploy (CI/CD)](#14-production-redeploy-cicd)
  - [15. Qdrant — Erase Collection \& Reingest from Zero](#15-qdrant--erase-collection--reingest-from-zero)
  - [16. Rebuild, Push \& Deploy Both Services](#16-rebuild-push--deploy-both-services)

---

## 1. GCP Project Setup

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

```bash
PROJECT_ID="agentics-sdlc"
TF_BUCKET="tf-state-agentics-sdlc"

cd platform/terraform
terraform init -backend-config="bucket=${TF_BUCKET}"
terraform plan -var="project_id=${PROJECT_ID}"
terraform apply -var="project_id=${PROJECT_ID}"
cd ../..
```

**Capture outputs:**

```bash
cd platform/terraform
terraform output artifacts_bucket_name
terraform output artifact_registry_url
terraform output api_sa_email

terraform output -raw cicd_sa_key_base64 | python3 -c "
import sys, base64; print(base64.b64decode(sys.stdin.read().strip()).decode())
" > /tmp/agentics-sdlc-cicd-key.json
cd ../..
```

---

## 2. Vertex AI (LLM)

```bash
PROJECT_ID="agentics-sdlc"

gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID

PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/aiplatform.user"

python3 - << 'EOF'
import vertexai
from vertexai.generative_models import GenerativeModel
vertexai.init(project="agentics-sdlc", location="us-central1")
model = GenerativeModel("gemini-2.5-flash")
print(model.generate_content("Reply with one word only: Hello").text.strip())
EOF
```

---

## 3. API Key

```bash
PROJECT_ID="agentics-sdlc"

AGENTICS_SDLC_API_KEY=$(openssl rand -hex 32)
echo "$AGENTICS_SDLC_API_KEY"

echo -n "${AGENTICS_SDLC_API_KEY}" | gcloud secrets versions add agentics-sdlc-api-key \
  --data-file=- --project=$PROJECT_ID

gcloud secrets versions access latest --secret=agentics-sdlc-api-key --project=$PROJECT_ID
```

---

## 4. Qdrant Cloud (Vector Store)

```
cloud.qdrant.io
  Name:     agentics-sdlc-kb
```

```bash
QDRANT_URL="https://XXXX.us-east4-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY="your-uuid-key"
PROJECT_ID="agentics-sdlc"

curl -s -H "api-key: ${QDRANT_API_KEY}" "${QDRANT_URL}/collections" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print('Collections:', len(r['result']['collections']))"

echo -n "${QDRANT_URL}"     | gcloud secrets versions add qdrant-url     --data-file=- --project=$PROJECT_ID
echo -n "${QDRANT_API_KEY}" | gcloud secrets versions add qdrant-api-key --data-file=- --project=$PROJECT_ID
```

---

## 5. Supabase (Audit Trail)

```
supabase.com/dashboard
  Name: agentics-sdlc
```

**SQL Editor:**

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS agent_audit_log (
    id            UUID        DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id    TEXT        NOT NULL,
    agent_name    TEXT        NOT NULL,
    phase         INTEGER     NOT NULL CHECK (phase BETWEEN 1 AND 6),
    latency_ms    NUMERIC(10, 2) NOT NULL DEFAULT 0,
    confidence    NUMERIC(5, 4) NOT NULL DEFAULT 0 CHECK (confidence BETWEEN 0 AND 1),
    status        TEXT        NOT NULL CHECK (status IN ('success', 'error', 'retry')),
    task_content  TEXT        NOT NULL DEFAULT '',
    error         TEXT        NOT NULL DEFAULT '',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_session_id   ON agent_audit_log (session_id);
CREATE INDEX IF NOT EXISTS idx_audit_agent_name   ON agent_audit_log (agent_name);
CREATE INDEX IF NOT EXISTS idx_audit_created_at   ON agent_audit_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_confidence   ON agent_audit_log (confidence) WHERE status = 'success';

CREATE TABLE IF NOT EXISTS workflow_snapshots (
    id              UUID        DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id      TEXT        NOT NULL UNIQUE,
    phase_reached   INTEGER     NOT NULL DEFAULT 1,
    retry_count     INTEGER     NOT NULL DEFAULT 0,
    final_status    TEXT        NOT NULL CHECK (final_status IN ('completed', 'failed', 'retrying')),
    confidence      NUMERIC(5, 4),
    latency_ms      NUMERIC(10, 2),
    snapshot_data   JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_session_id ON workflow_snapshots (session_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_status     ON workflow_snapshots (final_status);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON workflow_snapshots;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON workflow_snapshots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

GRANT SELECT, INSERT ON agent_audit_log TO anon, authenticated;
GRANT SELECT, INSERT ON workflow_snapshots TO anon, authenticated;
```

**Project Settings**

```bash
PROJECT_ID="agentics-sdlc"
SUPABASE_URL="https://XXXXXXXXXXXX.supabase.co"
SUPABASE_KEY="eyJ..."
SUPABASE_DB_URL="postgresql://postgres:PASSWORD@db.XXXXXXXXXXXX.supabase.co:5432/postgres"

echo -n "${SUPABASE_URL}"    | gcloud secrets versions add supabase-url    --data-file=- --project=$PROJECT_ID
echo -n "${SUPABASE_KEY}"    | gcloud secrets versions add supabase-key    --data-file=- --project=$PROJECT_ID
echo -n "${SUPABASE_DB_URL}" | gcloud secrets versions add supabase-db-url --data-file=- --project=$PROJECT_ID
```

---

## 6. Grafana Cloud (Observability)

```
grafana.com
Create stack: agentics-sdlc
```

**Add to `~/.zshrc` or `~/.bashrc` (NOT in .env):**
```bash
export GRAFANA_INSTANCE_ID="123456789"
export GRAFANA_API_KEY="glc_eyJ..."
export GRAFANA_PROMETHEUS_URL="https://prometheus-prod-XX-prod-us-east-2.grafana.net/api/prom/push"
```

**BigQuery data source:**
```bash
cd platform/terraform
terraform output -raw grafana_sa_key_base64 | python3 -c "
import sys, base64; print(base64.b64decode(sys.stdin.read().strip()).decode())
" > /tmp/grafana-bq-key.json
cat /tmp/grafana-bq-key.json
rm /tmp/grafana-bq-key.json
cd ../..
```

---

## 7. GitHub Configuration

**Repository Secrets**

| Secret | Value |
|---|---|
| `GCP_SA_JSON` | `cat /tmp/agentics-sdlc-cicd-key.json` |
| `AGENTICS_SDLC_API_KEY` | Generated key from §3 |

**Repository Variables**
```
GCP_PROJECT_ID = agentics-sdlc
QDRANT_URL     = https://<your-cluster-id>.us-east4-0.gcp.cloud.qdrant.io:6333
```

---

## 8. Local Development

```bash
cat > .env << EOF
GCP_PROJECT_ID=agentics-sdlc
GCP_REGION=us-central1
GCS_BUCKET=$(cd platform/terraform && terraform output -raw artifacts_bucket_name && cd ../..)
GEMINI_MODEL=gemini-2.5-flash
SUPABASE_URL=https://XXXXXXXXXXXX.supabase.co
SUPABASE_KEY=eyJ...
SUPABASE_DB_URL=postgresql://postgres:PASSWORD@db.XXXXXXXXXXXX.supabase.co:5432/postgres
QDRANT_URL=
QDRANT_API_KEY=
BIGQUERY_DATASET=agentics_sdlc_analytics
MLFLOW_LOCAL=true
LOG_LEVEL=INFO
PORT=8080
AGENTICS_SDLC_API_KEY=
ALLOWED_ORIGINS=*
RATE_LIMIT_RPM=60
METRICS_USERNAME=
METRICS_PASSWORD=
EOF
```

---

## 9. Local Stack & First Test

```bash
# Terminal 1 — API
poetry run uvicorn src.api.main:create_app --factory --reload --port 8080

# Terminal 2 — ingest knowledge base (first run only)
poetry run python scripts/scripts_rag.py --path .agent/

# Terminal 3 — health check
curl -sf http://localhost:8080/health

# Submit task
curl -s -X POST http://localhost:8080/api/v1/task \
  -H "Content-Type: application/json" \
  -d '{"content": "Explain the REFLECTOR confidence audit in Agentics SDLC"}' \
  | python3 -c "
import sys,json; r=json.load(sys.stdin)
print(f'Status:     {r[\"status\"]}')
print(f'Confidence: {r[\"confidence\"]:.2f}')
print(f'Latency:    {r[\"latency_ms\"]:.0f}ms')
"

# Verify rate limit headers
curl -s -D - -X POST http://localhost:8080/api/v1/task \
  -H "Content-Type: application/json" \
  -d '{"content": "ping"}' \
  -o /dev/null | grep -i "x-ratelimit\|x-rate"

# Verify Prometheus metrics
curl -s http://localhost:8080/metrics | grep "^agentics_sdlc_" | head -6
```

---

## 10. Deploy API to Cloud Run

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

cat > /tmp/agentics-sdlc-deploy.yaml << EOF
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: agentics-sdlc-api
  namespace: '${NAMESPACE}'
  annotations:
    run.googleapis.com/ingress: all
    run.googleapis.com/client-name: gcloud
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: '1'
        autoscaling.knative.dev/maxScale: '10'
        run.googleapis.com/cpu-throttling: 'true'
        run.googleapis.com/sessionAffinity: 'false'
        run.googleapis.com/startup-cpu-boost: 'true'
      labels:
        run.googleapis.com/startupProbeType: Custom
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
        - name: MLFLOW_LOCAL
          value: 'false'
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
        - name: METRICS_USERNAME
          valueFrom:
            secretKeyRef:
              name: metrics-username
              key: latest
        - name: METRICS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: metrics-password
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

CLOUD_RUN_URL=$(gcloud run services describe agentics-sdlc-api \
  --region=us-central1 --format="value(status.url)" --project=$PROJECT_ID)
echo "API deployed: ${CLOUD_RUN_URL}"
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
  --memory 4Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCS_BUCKET=artifacts-${PROJECT_ID},BIGQUERY_DATASET=agentics_sdlc_analytics,RATE_LIMIT_RPM=60,MLFLOW_LOCAL=false,ALLOWED_ORIGINS=*" \
  --set-secrets "AGENTICS_SDLC_API_KEY=agentics-sdlc-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,SUPABASE_DB_URL=supabase-db-url:latest,QDRANT_URL=qdrant-url:latest,QDRANT_API_KEY=qdrant-api-key:latest,METRICS_USERNAME=metrics-username:latest,METRICS_PASSWORD=metrics-password:latest"
```

### Verify

```bash
CLOUD_RUN_URL=$(gcloud run services describe agentics-sdlc-api \
  --region=us-central1 --format="value(status.url)" --project=$PROJECT_ID)

curl -f "${CLOUD_RUN_URL}/health"

PROD_KEY=$(gcloud secrets versions access latest --secret=agentics-sdlc-api-key --project=$PROJECT_ID)
curl -s -X POST "${CLOUD_RUN_URL}/api/v1/task" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${PROD_KEY}" \
  -d '{"content": "Explain the REFLECTOR confidence audit in Agentics SDLC"}' \
  | python3 -c "
import sys,json; r=json.load(sys.stdin)
print(f'Status:     {r[\"status\"]}')
print(f'Confidence: {r[\"confidence\"]:.2f}')
print(f'Latency:    {r[\"latency_ms\"]:.0f}ms')
"

curl -s -D - -X POST "${CLOUD_RUN_URL}/api/v1/task" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${PROD_KEY}" \
  -d '{"content": "ping"}' \
  -o /dev/null | grep -i "x-ratelimit\|x-rate"
```

---

## 11. Deploy UI to Cloud Run

```bash
# Generate and copy in UI_AUTH_PASSWORD_HASH
python -c "import bcrypt; print(bcrypt.hashpw(b'your-chosen-password', bcrypt.gensalt()).decode())"

echo -n '<bcrypt-hash>' | gcloud secrets versions add ui-auth-password-hash \
  --data-file=- --project=$GCP_PROJECT_ID

openssl rand -hex 32

# Copy output to CHAINLIT_AUTH_SECRET
echo -n "<jwt-secret>" | gcloud secrets versions add chainlit-auth-secret \
  --data-file=- --project=$GCP_PROJECT_ID

# Apply Terraform
cd platform/terraform
terraform apply -var="project_id=$GCP_PROJECT_ID" -var="region=us-central1"
cd ../..

# Build and push
docker system prune -f && docker builder prune -f
gcloud auth configure-docker gcr.io

docker build \
  --platform linux/amd64 \
  --no-cache \
  -f platform/docker/Dockerfile.ui \
  -t gcr.io/$GCP_PROJECT_ID/agentics-sdlc-ui:latest \
  .

docker push gcr.io/$GCP_PROJECT_ID/agentics-sdlc-ui:latest

# Deploy
gcloud run deploy agentics-sdlc-ui \
  --image gcr.io/$GCP_PROJECT_ID/agentics-sdlc-ui:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --timeout 900 \
  --session-affinity \
  --set-env-vars "GCP_PROJECT_ID=$GCP_PROJECT_ID,ENVIRONMENT=production" \
  --set-secrets "AGENTICS_SDLC_API_KEY=agentics-sdlc-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,SUPABASE_DB_URL=supabase-db-url:latest,QDRANT_URL=qdrant-url:latest,QDRANT_API_KEY=qdrant-api-key:latest,CHAINLIT_AUTH_SECRET=chainlit-auth-secret:latest,UI_AUTH_PASSWORD_HASH=ui-auth-password-hash:latest,METRICS_USERNAME=metrics-username:latest,METRICS_PASSWORD=metrics-password:latest" \
  --project $GCP_PROJECT_ID

# Sync Terraform state
cd platform/terraform
terraform apply -var="project_id=$GCP_PROJECT_ID" -var="region=us-central1"
cd ../..

# Verify
UI_URL=$(gcloud run services describe agentics-sdlc-ui \
  --region us-central1 --format 'value(status.url)')
echo "UI: $UI_URL"
curl -f "$UI_URL/health"
```

---

## 12. BigQuery Scheduled Queries

```
  KPI 1 — Daily Agent Call Volume:
    Destination table: agentics_sdlc_analytics.kpi_daily_agent_call_volume

  KPI 2 — Avg Confidence & Latency per Agent (7d):
    Destination table: agentics_sdlc_analytics.kpi_avg_confidence_latency

  KPI 3 — Low-Confidence Sessions:
    Destination table: agentics_sdlc_analytics.kpi_low_confidence_sessions
```

---

## 13. Grafana Dashboard

**Import dashboard:**
```
Grafana Cloud
  Import: observability/grafana/agentics-sdlc-dashboard.json
  Select Prometheus data source
```

---

## 14. Production Redeploy (CI/CD)

Every push to `main` triggers the GitHub Actions pipeline automatically (4 sequential jobs):

1. **quality** — Black format check, isort, Flake8 lint, Mypy type-check
2. **test** — pytest unit tests with coverage (≥70%) against a Postgres 16 service container
3. **build** — Build & push `agentics-sdlc-api:<sha>` and `agentics-sdlc-ui:<sha>` to GCR (main branch only)
4. **deploy** — Deploy API then UI to Cloud Run (`us-central1`), verify `/health` on both (requires `production` environment approval)

**Re-ingest knowledge base after deploy:**

```bash
QDRANT_URL=$(gcloud secrets versions access latest --secret=qdrant-url --project=$PROJECT_ID)
QDRANT_API_KEY=$(gcloud secrets versions access latest --secret=qdrant-api-key --project=$PROJECT_ID)
QDRANT_URL=$QDRANT_URL QDRANT_API_KEY=$QDRANT_API_KEY \
  poetry run python scripts/scripts_rag.py --path .agent/
```

---

## 15. Qdrant — Erase Collection & Reingest from Zero

Wipes the `agentics_sdlc_kb` collection entirely and rebuilds it from scratch.

```bash
PROJECT_ID="agentics-sdlc"

# Pull credentials from Secret Manager
QDRANT_URL=$(gcloud secrets versions access latest --secret=qdrant-url --project=$PROJECT_ID)
QDRANT_API_KEY=$(gcloud secrets versions access latest --secret=qdrant-api-key --project=$PROJECT_ID)

# 1. Delete the collection
curl -s -X DELETE "${QDRANT_URL}/collections/agentics_sdlc_kb" \
  -H "api-key: ${QDRANT_API_KEY}" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print('Deleted:', r)"

# 2. Verify collection is gone
curl -s "${QDRANT_URL}/collections" \
  -H "api-key: ${QDRANT_API_KEY}" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print('Collections:', [c['name'] for c in r['result']['collections']])"

# 3. Reingest — collection is auto-created on first upsert
QDRANT_URL=$QDRANT_URL QDRANT_API_KEY=$QDRANT_API_KEY \
  poetry run python scripts/scripts_rag.py --path .agent/

# 4. Verify point count
curl -s "${QDRANT_URL}/collections/agentics_sdlc_kb" \
  -H "api-key: ${QDRANT_API_KEY}" \
  | python3 -c "import sys,json; r=json.load(sys.stdin); print('Points:', r['result']['points_count'])"
```

---

## 16. Rebuild, Push & Deploy Both Services

Full rebuild of both Docker images from scratch, push to GCR, and deploy to Cloud Run.

```bash
# Safe prune — only removes unused/dangling resources
# docker system prune -f
# docker builder prune -f

PROJECT_ID="agentics-sdlc"
REGISTRY_URL=$(cd platform/terraform && terraform output -raw artifact_registry_url && cd ../..)

API_IMAGE="${REGISTRY_URL}/agentics-sdlc-api"
UI_IMAGE="gcr.io/${PROJECT_ID}/agentics-sdlc-ui"

gcloud auth configure-docker gcr.io --quiet

# Clean Docker cache
docker system prune -f && docker builder prune -f

# API
docker build \
  --platform linux/amd64 \
  --no-cache \
  -f platform/docker/Dockerfile.api \
  -t "${API_IMAGE}:latest" .

docker push "${API_IMAGE}:latest"

gcloud run deploy agentics-sdlc-api \
  --image="${API_IMAGE}:latest" \
  --region=us-central1 \
  --project=$PROJECT_ID \
  --platform managed \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCS_BUCKET=artifacts-${PROJECT_ID},BIGQUERY_DATASET=agentics_sdlc_analytics,RATE_LIMIT_RPM=60,MLFLOW_LOCAL=false,ALLOWED_ORIGINS=*" \
  --set-secrets "AGENTICS_SDLC_API_KEY=agentics-sdlc-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,SUPABASE_DB_URL=supabase-db-url:latest,QDRANT_URL=qdrant-url:latest,QDRANT_API_KEY=qdrant-api-key:latest,METRICS_USERNAME=metrics-username:latest,METRICS_PASSWORD=metrics-password:latest"

# Verify API
API_URL=$(gcloud run services describe agentics-sdlc-api \
  --region=us-central1 --format="value(status.url)" --project=$PROJECT_ID)
curl -f "${API_URL}/health" && echo "API OK"

# UI
docker build \
  --platform linux/amd64 \
  --no-cache \
  -f platform/docker/Dockerfile.ui \
  -t "${UI_IMAGE}:latest" .

docker push "${UI_IMAGE}:latest"

gcloud run deploy agentics-sdlc-ui \
  --image="${UI_IMAGE}:latest" \
  --region=us-central1 \
  --project=$PROJECT_ID \
  --platform managed \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --timeout 900 \
  --session-affinity \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},ENVIRONMENT=production" \
  --set-secrets "AGENTICS_SDLC_API_KEY=agentics-sdlc-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_KEY=supabase-key:latest,SUPABASE_DB_URL=supabase-db-url:latest,QDRANT_URL=qdrant-url:latest,QDRANT_API_KEY=qdrant-api-key:latest,CHAINLIT_AUTH_SECRET=chainlit-auth-secret:latest,UI_AUTH_PASSWORD_HASH=ui-auth-password-hash:latest,METRICS_USERNAME=metrics-username:latest,METRICS_PASSWORD=metrics-password:latest" \
  --project=$PROJECT_ID

# Verify UI
UI_URL=$(gcloud run services describe agentics-sdlc-ui \
  --region=us-central1 --format="value(status.url)" --project=$PROJECT_ID)
curl -f "${UI_URL}/health" && echo "UI OK"
```
