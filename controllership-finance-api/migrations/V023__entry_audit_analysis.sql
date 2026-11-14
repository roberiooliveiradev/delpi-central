-- V023 — Auditoria de entradas. Só cria tabela. Rollback de código não apaga.
-- Schema controllership_finance.

BEGIN;

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_analysis (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date_from             DATE         NOT NULL,
    date_to               DATE         NOT NULL,
    document_types        TEXT[]       NOT NULL,
    branches              TEXT[]       NOT NULL,
    config_snapshot       JSONB        NOT NULL,
    status                TEXT         NOT NULL,
    requested_by_user_id  TEXT         NOT NULL,
    requested_by_name     TEXT         NOT NULL DEFAULT '',
    requested_via         TEXT         NOT NULL,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    finished_at           TIMESTAMPTZ,
    CONSTRAINT entry_audit_analysis_status_check
        CHECK (status IN ('queued', 'running', 'done', 'failed')),
    CONSTRAINT entry_audit_analysis_via_check
        CHECK (requested_via IN ('user', 'clara')),
    CONSTRAINT entry_audit_analysis_period_check
        CHECK (date_from <= date_to)
);

CREATE UNIQUE INDEX IF NOT EXISTS entry_audit_analysis_open_filters_uidx
    ON controllership_finance.entry_audit_analysis (date_from, date_to, document_types, branches)
    WHERE status IN ('queued', 'running');

CREATE INDEX IF NOT EXISTS entry_audit_analysis_status_created_idx
    ON controllership_finance.entry_audit_analysis (status, created_at DESC);

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_run (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id      UUID        NOT NULL
        REFERENCES controllership_finance.entry_audit_analysis (id) ON DELETE CASCADE,
    branch_code      TEXT        NOT NULL,
    status           TEXT        NOT NULL,
    stage            TEXT        NOT NULL DEFAULT '',
    documents_read   INTEGER     NOT NULL DEFAULT 0,
    xml_downloaded   INTEGER     NOT NULL DEFAULT 0,
    counts           JSONB       NOT NULL DEFAULT '{}'::jsonb,
    engine_version   TEXT        NOT NULL DEFAULT '',
    sources_hash     TEXT        NOT NULL DEFAULT '',
    error_message    TEXT        NOT NULL DEFAULT '',
    started_at       TIMESTAMPTZ,
    finished_at      TIMESTAMPTZ,
    CONSTRAINT entry_audit_run_status_check
        CHECK (status IN ('queued', 'running', 'done', 'failed')),
    UNIQUE (analysis_id, branch_code)
);

CREATE INDEX IF NOT EXISTS entry_audit_run_queued_idx
    ON controllership_finance.entry_audit_run (status)
    WHERE status = 'queued';

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_document (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id            UUID        NOT NULL
        REFERENCES controllership_finance.entry_audit_run (id) ON DELETE CASCADE,
    access_key        TEXT        NOT NULL DEFAULT '',
    branch_code       TEXT        NOT NULL,
    document_number   TEXT        NOT NULL,
    series            TEXT        NOT NULL DEFAULT '',
    supplier_code     TEXT        NOT NULL DEFAULT '',
    supplier_store    TEXT        NOT NULL DEFAULT '',
    supplier_name     TEXT        NOT NULL DEFAULT '',
    issue_date        DATE,
    received_date     DATE,
    situation         TEXT        NOT NULL DEFAULT '',
    divergence_count  INTEGER     NOT NULL DEFAULT 0,
    comparison        JSONB       NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_occurrence (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id           UUID        NOT NULL
        REFERENCES controllership_finance.entry_audit_run (id) ON DELETE CASCADE,
    analysis_id      UUID        NOT NULL
        REFERENCES controllership_finance.entry_audit_analysis (id) ON DELETE CASCADE,
    stable_key       TEXT        NOT NULL,
    rule_id          TEXT        NOT NULL,
    severity         TEXT        NOT NULL,
    theme            TEXT        NOT NULL DEFAULT '',
    title            TEXT        NOT NULL,
    document_number  TEXT        NOT NULL DEFAULT '',
    series           TEXT        NOT NULL DEFAULT '',
    supplier_name    TEXT        NOT NULL DEFAULT '',
    item             TEXT        NOT NULL DEFAULT '',
    field            TEXT        NOT NULL DEFAULT '',
    protheus_value   TEXT        NOT NULL DEFAULT '',
    xml_value        TEXT        NOT NULL DEFAULT '',
    difference       TEXT        NOT NULL DEFAULT '',
    tes              TEXT        NOT NULL DEFAULT '',
    why              TEXT        NOT NULL DEFAULT '',
    action           TEXT        NOT NULL DEFAULT '',
    access_key       TEXT        NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS entry_audit_occurrence_analysis_severity_idx
    ON controllership_finance.entry_audit_occurrence (analysis_id, severity);

CREATE INDEX IF NOT EXISTS entry_audit_occurrence_stable_key_idx
    ON controllership_finance.entry_audit_occurrence (stable_key);

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_unmatched (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id           UUID        NOT NULL
        REFERENCES controllership_finance.entry_audit_run (id) ON DELETE CASCADE,
    analysis_id      UUID        NOT NULL
        REFERENCES controllership_finance.entry_audit_analysis (id) ON DELETE CASCADE,
    stable_key       TEXT        NOT NULL,
    side             TEXT        NOT NULL,
    rule_id          TEXT        NOT NULL,
    severity         TEXT        NOT NULL,
    reason           TEXT        NOT NULL DEFAULT '',
    situation        TEXT        NOT NULL DEFAULT '',
    lnf_request_id   TEXT        NOT NULL DEFAULT '',
    lnf_status       TEXT        NOT NULL DEFAULT '',
    access_key       TEXT        NOT NULL DEFAULT '',
    document_number  TEXT        NOT NULL DEFAULT '',
    series           TEXT        NOT NULL DEFAULT '',
    party_name       TEXT        NOT NULL DEFAULT '',
    issue_date       DATE,
    amount           NUMERIC(18, 2),
    CONSTRAINT entry_audit_unmatched_side_check
        CHECK (side IN ('xml', 'protheus'))
);

CREATE INDEX IF NOT EXISTS entry_audit_unmatched_analysis_idx
    ON controllership_finance.entry_audit_unmatched (analysis_id);

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_cte (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id      UUID  NOT NULL
        REFERENCES controllership_finance.entry_audit_run (id) ON DELETE CASCADE,
    access_key  TEXT  NOT NULL DEFAULT '',
    comparison  JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_tes_used (
    id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id    UUID  NOT NULL
        REFERENCES controllership_finance.entry_audit_run (id) ON DELETE CASCADE,
    tes_code  TEXT  NOT NULL,
    sf4       JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (run_id, tes_code)
);

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_status (
    stable_key           TEXT PRIMARY KEY,
    kind                 TEXT        NOT NULL,
    status               TEXT        NOT NULL,
    resolved_by_user_id  TEXT        NOT NULL DEFAULT '',
    resolved_by_name     TEXT        NOT NULL DEFAULT '',
    resolved_at          TIMESTAMPTZ,
    reopened_at          TIMESTAMPTZ,
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT entry_audit_status_kind_check
        CHECK (kind IN ('occurrence', 'unmatched')),
    CONSTRAINT entry_audit_status_status_check
        CHECK (status IN ('pending', 'resolved'))
);

CREATE TABLE IF NOT EXISTS controllership_finance.entry_audit_xml_cache (
    access_key  TEXT PRIMARY KEY,
    model       TEXT        NOT NULL,
    xml_gzip    BYTEA       NOT NULL,
    fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
