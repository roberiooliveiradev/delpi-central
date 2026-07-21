-- Delpi Reports — núcleo transacional (V001)
-- Schema reports (criado pelo runner de migrations de plugins).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS reports.report_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    provider_key VARCHAR(100) NOT NULL,
    params JSONB NOT NULL DEFAULT '{}'::jsonb,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_reports_definitions_name_not_blank
        CHECK (char_length(btrim(name)) > 0),
    CONSTRAINT ck_reports_definitions_provider_key_not_blank
        CHECK (char_length(btrim(provider_key)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_reports_definitions_provider_active
    ON reports.report_definitions (provider_key, active);

CREATE TABLE IF NOT EXISTS reports.report_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    definition_id UUID NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    email VARCHAR(320) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_reports_recipients_definition
        FOREIGN KEY (definition_id)
        REFERENCES reports.report_definitions (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_reports_recipients_email_not_blank
        CHECK (char_length(btrim(email)) > 0),
    CONSTRAINT ck_reports_recipients_user_id_not_blank
        CHECK (char_length(btrim(user_id)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_reports_recipients_definition_user
    ON reports.report_recipients (definition_id, user_id);

CREATE INDEX IF NOT EXISTS idx_reports_recipients_definition_active
    ON reports.report_recipients (definition_id, active);

CREATE TABLE IF NOT EXISTS reports.report_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    definition_id UUID NOT NULL,
    schedule_kind VARCHAR(20) NOT NULL,
    cron_expression VARCHAR(100),
    timezone VARCHAR(64) NOT NULL DEFAULT 'America/Sao_Paulo',
    next_run_at TIMESTAMPTZ,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_reports_schedules_definition
        FOREIGN KEY (definition_id)
        REFERENCES reports.report_definitions (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_reports_schedules_kind
        CHECK (schedule_kind IN ('daily', 'weekly'))
);

CREATE INDEX IF NOT EXISTS idx_reports_schedules_next_run
    ON reports.report_schedules (next_run_at)
    WHERE enabled = TRUE;

CREATE INDEX IF NOT EXISTS idx_reports_schedules_definition
    ON reports.report_schedules (definition_id);

CREATE TABLE IF NOT EXISTS reports.report_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    definition_id UUID NOT NULL,
    trigger VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_reports_runs_definition
        FOREIGN KEY (definition_id)
        REFERENCES reports.report_definitions (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_reports_runs_trigger
        CHECK (trigger IN ('manual', 'schedule')),
    CONSTRAINT ck_reports_runs_status
        CHECK (status IN ('pending', 'running', 'succeeded', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_reports_runs_definition_created
    ON reports.report_runs (definition_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_reports_runs_status
    ON reports.report_runs (status);

CREATE TABLE IF NOT EXISTS reports.report_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL,
    recipient_email VARCHAR(320) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    provider_message_id VARCHAR(200),
    error TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_reports_deliveries_run
        FOREIGN KEY (run_id)
        REFERENCES reports.report_runs (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_reports_deliveries_status
        CHECK (status IN ('pending', 'sent', 'failed')),
    CONSTRAINT ck_reports_deliveries_email_not_blank
        CHECK (char_length(btrim(recipient_email)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_reports_deliveries_run
    ON reports.report_deliveries (run_id);

CREATE INDEX IF NOT EXISTS idx_reports_deliveries_status
    ON reports.report_deliveries (status);
