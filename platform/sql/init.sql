-- Local dev schema (production runs on Supabase managed Postgres)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Agent audit trail

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
-- Partial index: confidence filtering is only meaningful on successful calls;
-- excluding error/retry rows keeps the index small and avoids skewed stats.
CREATE INDEX IF NOT EXISTS idx_audit_confidence   ON agent_audit_log (confidence) WHERE status = 'success';

-- RAG evaluation results

CREATE TABLE IF NOT EXISTS rag_evaluations (
    id                  UUID        DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_id          TEXT        NOT NULL,
    faithfulness        NUMERIC(5, 4),
    answer_relevancy    NUMERIC(5, 4),
    context_recall      NUMERIC(5, 4),
    context_precision   NUMERIC(5, 4),
    passed              BOOLEAN     NOT NULL DEFAULT FALSE,
    evaluated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_session_id     ON rag_evaluations (session_id);
CREATE INDEX IF NOT EXISTS idx_rag_evaluated_at   ON rag_evaluations (evaluated_at DESC);
CREATE INDEX IF NOT EXISTS idx_rag_passed         ON rag_evaluations (passed);

-- Workflow snapshots (debugging and audit)

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

-- Keep updated_at in sync automatically

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON workflow_snapshots;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON workflow_snapshots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
