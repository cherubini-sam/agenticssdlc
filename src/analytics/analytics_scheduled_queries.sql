-- Agentics SDLC BigQuery KPI Queries
-- Dataset: agentics_sdlc_analytics
-- Table: agent_audit_log (partitioned on timestamp, clustered on agent_name)

-- KPI 1: Daily Agent Call Volume by Agent

SELECT
    DATE(timestamp)             AS day,
    agent_name,
    COUNT(*)                    AS total_calls,
    COUNTIF(status = 'success') AS successful_calls,
    COUNTIF(status = 'error')   AS failed_calls,
    SAFE_DIVIDE(
        COUNTIF(status = 'success'), COUNT(*)
    ) * 100                     AS success_rate_pct
FROM
    `agentics_sdlc_analytics.agent_audit_log`
WHERE
    DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY
    1, 2
ORDER BY
    day DESC, total_calls DESC;


-- KPI 2: Average Confidence and Latency per Agent (Last 7 Days)

SELECT
    agent_name,
    ROUND(AVG(confidence), 4)                                   AS avg_confidence,
    ROUND(STDDEV(confidence), 4)                                AS stddev_confidence,
    ROUND(AVG(latency_ms), 1)                                   AS avg_latency_ms,
    ROUND(APPROX_QUANTILES(latency_ms, 100)[OFFSET(95)], 1)    AS p95_latency_ms,
    COUNT(*)                                                    AS sample_size
FROM
    `agentics_sdlc_analytics.agent_audit_log`
WHERE
    DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND status = 'success'
GROUP BY
    agent_name
ORDER BY
    avg_confidence DESC;


-- KPI 3: Low-Confidence Sessions (Confidence < 0.85 Threshold)

SELECT
    session_id,
    agent_name,
    phase,
    ROUND(confidence, 4) AS confidence,
    ROUND(latency_ms, 1) AS latency_ms,
    error,
    timestamp
FROM
    `agentics_sdlc_analytics.agent_audit_log`
WHERE
    DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND confidence < 0.85
    AND status = 'success'
ORDER BY
    confidence ASC,
    timestamp DESC
LIMIT 500;
