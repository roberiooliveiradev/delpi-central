-- Auditoria 5S operacional — tabelas core (schema quality)

CREATE TABLE IF NOT EXISTS quality.audit_5s_sensos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sort_order SMALLINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_audit_5s_sensos_sort_order UNIQUE (sort_order),
    CONSTRAINT ck_audit_5s_sensos_sort_order CHECK (sort_order BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS quality.audit_5s_criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    senso_id UUID NOT NULL,
    code VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    sort_order SMALLINT NOT NULL,
    catalog_version INTEGER NOT NULL DEFAULT 1,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_audit_5s_criteria_senso
        FOREIGN KEY (senso_id)
        REFERENCES quality.audit_5s_sensos (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT uq_audit_5s_criteria_code_version UNIQUE (code, catalog_version),
    CONSTRAINT uq_audit_5s_criteria_senso_sort_version
        UNIQUE (senso_id, sort_order, catalog_version),
    CONSTRAINT ck_audit_5s_criteria_sort_order CHECK (sort_order >= 1)
);

CREATE TABLE IF NOT EXISTS quality.audit_5s_areas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_code VARCHAR(2) NOT NULL,
    name VARCHAR(200) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_audit_5s_areas_branch CHECK (branch_code IN ('01', '02'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_audit_5s_areas_branch_name
    ON quality.audit_5s_areas (branch_code, lower(trim(name)));

CREATE TABLE IF NOT EXISTS quality.audit_5s_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_code VARCHAR(2) NOT NULL,
    audit_code VARCHAR(20) NOT NULL,
    catalog_version INTEGER NOT NULL DEFAULT 1,
    audit_date DATE NOT NULL,
    area_id UUID NOT NULL,
    area_responsible VARCHAR(200) NOT NULL,
    shift VARCHAR(30) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    overall_score_pct NUMERIC(6, 2),
    senso_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_audit_5s_audits_code UNIQUE (audit_code),

    CONSTRAINT fk_audit_5s_audits_area
        FOREIGN KEY (area_id)
        REFERENCES quality.audit_5s_areas (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT ck_audit_5s_audits_branch CHECK (branch_code IN ('01', '02')),

    CONSTRAINT ck_audit_5s_audits_shift CHECK (
        shift IN ('TURNO_1', 'TURNO_2', 'TURNO_3', 'ADMINISTRATIVO')
    ),

    CONSTRAINT ck_audit_5s_audits_status CHECK (
        status IN ('draft', 'evaluation_complete', 'nc_in_progress', 'closed')
    )
);

CREATE TABLE IF NOT EXISTS quality.audit_5s_auditors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_audit_5s_auditors_audit
        FOREIGN KEY (audit_id)
        REFERENCES quality.audit_5s_audits (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT uq_audit_5s_auditors_audit_user UNIQUE (audit_id, user_id)
);

CREATE TABLE IF NOT EXISTS quality.audit_5s_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL,
    criterion_id UUID NOT NULL,
    score SMALLINT,
    is_not_applicable BOOLEAN NOT NULL DEFAULT FALSE,
    observation TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    updated_by_user_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_audit_5s_responses_audit
        FOREIGN KEY (audit_id)
        REFERENCES quality.audit_5s_audits (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_audit_5s_responses_criterion
        FOREIGN KEY (criterion_id)
        REFERENCES quality.audit_5s_criteria (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT uq_audit_5s_responses_audit_criterion UNIQUE (audit_id, criterion_id),

    CONSTRAINT ck_audit_5s_responses_score CHECK (
        (is_not_applicable = TRUE AND score IS NULL)
        OR (is_not_applicable = FALSE AND score IN (1, 3, 5))
        OR (is_not_applicable = FALSE AND score IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS quality.audit_5s_response_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    response_id UUID NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(150),
    size_bytes BIGINT NOT NULL,
    storage_provider VARCHAR(50) NOT NULL DEFAULT 'local',
    storage_path TEXT NOT NULL,
    uploaded_by_user_id VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_audit_5s_response_attachments_response
        FOREIGN KEY (response_id)
        REFERENCES quality.audit_5s_responses (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_audit_5s_response_attachments_size_bytes
        CHECK (size_bytes >= 0)
);

CREATE TABLE IF NOT EXISTS quality.audit_5s_nonconformities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    audit_id UUID NOT NULL,
    response_id UUID NOT NULL,
    description TEXT NOT NULL,
    responsible_name VARCHAR(200) NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    created_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_audit_5s_nc_audit
        FOREIGN KEY (audit_id)
        REFERENCES quality.audit_5s_audits (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_audit_5s_nc_response
        FOREIGN KEY (response_id)
        REFERENCES quality.audit_5s_responses (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT,

    CONSTRAINT uq_audit_5s_nc_response UNIQUE (response_id),

    CONSTRAINT ck_audit_5s_nc_status CHECK (
        status IN ('open', 'in_progress', 'closed', 'cancelled')
    )
);

CREATE TABLE IF NOT EXISTS quality.audit_5s_nc_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID NOT NULL,
    description TEXT NOT NULL,
    actor_user_id VARCHAR(100) NOT NULL,
    actor_display_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_audit_5s_nc_actions_nc
        FOREIGN KEY (nonconformity_id)
        REFERENCES quality.audit_5s_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS quality.audit_5s_nc_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    actor_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_audit_5s_nc_events_nc
        FOREIGN KEY (nonconformity_id)
        REFERENCES quality.audit_5s_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_audit_5s_audits_branch_status
    ON quality.audit_5s_audits (branch_code, status, audit_date DESC);

CREATE INDEX IF NOT EXISTS idx_audit_5s_areas_branch_active
    ON quality.audit_5s_areas (branch_code, active);

CREATE INDEX IF NOT EXISTS idx_audit_5s_responses_audit
    ON quality.audit_5s_responses (audit_id);

CREATE INDEX IF NOT EXISTS idx_audit_5s_criteria_catalog
    ON quality.audit_5s_criteria (catalog_version, active);
