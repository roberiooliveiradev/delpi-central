-- Relatórios de análise metalográfica (schema engineering, owner api-delpi).
-- Binários ficam no volume METALLOGRAPHIC_IMAGE_UPLOAD_DIR; aqui só metadados.

CREATE TABLE IF NOT EXISTS engineering.metallographic_report_counters (
    year INTEGER PRIMARY KEY,
    last_value INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS engineering.metallographic_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_number VARCHAR(32) NOT NULL,
    report_date DATE,
    revision VARCHAR(16) NOT NULL DEFAULT '00',
    terminal_code VARCHAR(240),
    terminal_part_number VARCHAR(240),
    product_harness VARCHAR(240),
    cable VARCHAR(240),
    conductor_section VARCHAR(240),
    applicator_tool VARCHAR(240),
    press_equipment VARCHAR(240),
    batch_production_order VARCHAR(240),
    sample_identification VARCHAR(240),
    measurements JSONB NOT NULL DEFAULT '{}'::jsonb,
    conclusion_result VARCHAR(32),
    conclusion_notes TEXT,
    analyst_name VARCHAR(160),
    analyst_user_id VARCHAR(120),
    status VARCHAR(16) NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(120) NOT NULL,
    updated_by VARCHAR(120) NOT NULL,
    deleted_at TIMESTAMPTZ,
    deleted_by VARCHAR(120),
    CONSTRAINT uq_metallographic_reports_number UNIQUE (report_number),
    CONSTRAINT ck_metallographic_reports_status CHECK (status IN ('draft')),
    CONSTRAINT ck_metallographic_reports_conclusion CHECK (
        conclusion_result IS NULL OR conclusion_result IN ('conforming', 'nonconforming')
    ),
    CONSTRAINT ck_metallographic_reports_version CHECK (version >= 1)
);

CREATE INDEX IF NOT EXISTS ix_metallographic_reports_active_created
    ON engineering.metallographic_reports (created_at DESC, id DESC)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_metallographic_reports_active_date
    ON engineering.metallographic_reports (report_date DESC, id DESC)
    WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS engineering.metallographic_report_images (
    report_id UUID NOT NULL REFERENCES engineering.metallographic_reports (id),
    slot VARCHAR(16) NOT NULL,
    content_type VARCHAR(64) NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256 CHAR(64) NOT NULL,
    stored_name VARCHAR(80) NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (report_id, slot),
    CONSTRAINT ck_metallographic_report_images_slot CHECK (slot IN ('original', 'measured')),
    CONSTRAINT ck_metallographic_report_images_size CHECK (size_bytes > 0)
);

CREATE TABLE IF NOT EXISTS engineering.metallographic_report_idempotency (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_subject VARCHAR(120) NOT NULL,
    operation VARCHAR(16) NOT NULL,
    idempotency_key VARCHAR(200) NOT NULL,
    request_hash CHAR(64) NOT NULL,
    report_id UUID NOT NULL REFERENCES engineering.metallographic_reports (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_metallographic_idempotency UNIQUE (actor_subject, operation, idempotency_key),
    CONSTRAINT ck_metallographic_idempotency_operation CHECK (operation IN ('create', 'copy'))
);

CREATE TABLE IF NOT EXISTS engineering.metallographic_report_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES engineering.metallographic_reports (id),
    operation VARCHAR(32) NOT NULL,
    actor_subject VARCHAR(120) NOT NULL,
    outcome VARCHAR(16) NOT NULL,
    detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_metallographic_report_audit_report
    ON engineering.metallographic_report_audit (report_id, created_at DESC);
