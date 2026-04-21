#!/usr/bin/env bash
# Verify Grafana Cloud live dashboard panels are populated.
# Queries the Grafana Cloud Prometheus HTTP API for each of the three live
# panel expressions and exits non-zero if any result set is empty.
#
# Required env: GRAFANA_PROMETHEUS_URL, GRAFANA_INSTANCE_ID, GRAFANA_API_KEY

set -euo pipefail

: "${GRAFANA_PROMETHEUS_URL:?GRAFANA_PROMETHEUS_URL is required}"
: "${GRAFANA_INSTANCE_ID:?GRAFANA_INSTANCE_ID is required}"
: "${GRAFANA_API_KEY:?GRAFANA_API_KEY is required}"

# Derive the query base URL from the remote-write push URL.
# Grafana Cloud layout: https://<region>.grafana.net/api/prom/push -> /api/prom/api/v1/query
QUERY_BASE="${GRAFANA_PROMETHEUS_URL%/push}"

urlencode() {
    # POSIX-portable urlencoder via jq.
    jq -rn --arg v "$1" '$v|@uri'
}

query_panel() {
    local label="$1"
    local promql="$2"
    local encoded
    encoded="$(urlencode "$promql")"
    local url="${QUERY_BASE}/api/v1/query?query=${encoded}"

    local length
    length="$(
        curl -sSf --max-time 15 \
            -u "${GRAFANA_INSTANCE_ID}:${GRAFANA_API_KEY}" \
            "$url" \
            | jq '.data.result | length'
    )"

    if [ "$length" -ge 1 ]; then
        echo "PASS: ${label}"
        return 0
    fi
    echo "FAIL: ${label} (empty result)"
    return 1
}

STATUS=0

query_panel "active_workflows" \
    'max(last_over_time(agentics_sdlc_active_workflows[5m]))' || STATUS=1

query_panel "agent_confidence" \
    'avg(agentics_sdlc_agent_confidence)' || STATUS=1

query_panel "agent_calls_total" \
    'sum by (status) (increase(agentics_sdlc_agent_calls_total[5m]))' || STATUS=1

exit "$STATUS"
