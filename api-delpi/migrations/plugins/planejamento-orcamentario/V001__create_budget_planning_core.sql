-- Planejamento Orçamentário — schema inicial (Fase 1)
-- Schema: planejamento_orcamentario (slug: planejamento-orcamentario)
-- Estados do exercício (doc 04 + archived): draft | open | closing | locked | archived
-- published/closed do brief mapeiam para open / closing|locked

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Catálogo organizacional interno (não acopla a TOTVS não validado)
CREATE TABLE IF NOT EXISTS planejamento_orcamentario.org_units (
    code VARCHAR(20) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.org_areas (
    code VARCHAR(40) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    unit_code VARCHAR(20) REFERENCES planejamento_orcamentario.org_units(code),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.org_cost_centers (
    code VARCHAR(40) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    unit_code VARCHAR(20) REFERENCES planejamento_orcamentario.org_units(code),
    area_code VARCHAR(40) REFERENCES planejamento_orcamentario.org_areas(code),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_user_id VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS ix_po_org_cc_active
    ON planejamento_orcamentario.org_cost_centers (active)
    WHERE active = TRUE;

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.budget_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    year INTEGER NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    preparation_starts_at DATE,
    filling_starts_at DATE,
    deadline_at DATE,
    closed_at DATE,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_by_user_id VARCHAR(100) NOT NULL,
    created_by_name VARCHAR(200),
    updated_by_user_id VARCHAR(100),
    updated_by_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_po_budget_exercises_year UNIQUE (year),
    CONSTRAINT ck_po_budget_exercises_year CHECK (year >= 2000 AND year <= 2100),
    CONSTRAINT ck_po_budget_exercises_status CHECK (
        status IN ('draft', 'open', 'closing', 'locked', 'archived')
    ),
    CONSTRAINT ck_po_budget_exercises_dates CHECK (
        (preparation_starts_at IS NULL OR filling_starts_at IS NULL OR preparation_starts_at <= filling_starts_at)
        AND (filling_starts_at IS NULL OR deadline_at IS NULL OR filling_starts_at <= deadline_at)
        AND (deadline_at IS NULL OR closed_at IS NULL OR deadline_at <= closed_at)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_po_budget_exercises_one_active
    ON planejamento_orcamentario.budget_exercises (is_active)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_budget_exercises_status
    ON planejamento_orcamentario.budget_exercises (status);

-- Versões de orientações (draft editável ou published imutável)
CREATE TABLE IF NOT EXISTS planejamento_orcamentario.guidance_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id UUID NOT NULL REFERENCES planejamento_orcamentario.budget_exercises(id),
    version_number INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    title VARCHAR(300) NOT NULL,
    board_message TEXT NOT NULL DEFAULT '',
    sender_name VARCHAR(200),
    sender_role VARCHAR(200),
    objective TEXT NOT NULL DEFAULT '',
    general_guidance TEXT NOT NULL DEFAULT '',
    additional_notes TEXT NOT NULL DEFAULT '',
    published_at TIMESTAMPTZ,
    published_by_user_id VARCHAR(100),
    published_by_name VARCHAR(200),
    created_by_user_id VARCHAR(100) NOT NULL,
    updated_by_user_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_po_guidance_status CHECK (status IN ('draft', 'published')),
    CONSTRAINT ck_po_guidance_published_fields CHECK (
        (status = 'draft' AND version_number IS NULL AND published_at IS NULL)
        OR (status = 'published' AND version_number IS NOT NULL AND version_number >= 1 AND published_at IS NOT NULL)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_po_guidance_one_draft_per_exercise
    ON planejamento_orcamentario.guidance_versions (exercise_id)
    WHERE status = 'draft';

CREATE UNIQUE INDEX IF NOT EXISTS uq_po_guidance_version_number
    ON planejamento_orcamentario.guidance_versions (exercise_id, version_number)
    WHERE status = 'published' AND version_number IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_po_guidance_exercise_status
    ON planejamento_orcamentario.guidance_versions (exercise_id, status);

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.guidance_premises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guidance_version_id UUID NOT NULL REFERENCES planejamento_orcamentario.guidance_versions(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    value_text VARCHAR(500),
    value_numeric NUMERIC(18, 6),
    unit_label VARCHAR(80),
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_po_premise_has_value CHECK (
        value_text IS NOT NULL OR value_numeric IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS ix_po_premises_version_order
    ON planejamento_orcamentario.guidance_premises (guidance_version_id, display_order);

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.guidance_schedule_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guidance_version_id UUID NOT NULL REFERENCES planejamento_orcamentario.guidance_versions(id) ON DELETE CASCADE,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    starts_on DATE NOT NULL,
    ends_on DATE,
    display_order INTEGER NOT NULL DEFAULT 0,
    highlighted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_po_schedule_dates CHECK (ends_on IS NULL OR ends_on >= starts_on)
);

CREATE INDEX IF NOT EXISTS ix_po_schedule_version_order
    ON planejamento_orcamentario.guidance_schedule_items (guidance_version_id, display_order);

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.support_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id UUID NOT NULL REFERENCES planejamento_orcamentario.budget_exercises(id),
    guidance_version_id UUID REFERENCES planejamento_orcamentario.guidance_versions(id),
    display_name VARCHAR(300) NOT NULL,
    original_name VARCHAR(300) NOT NULL DEFAULT '',
    mime_type VARCHAR(120) NOT NULL DEFAULT '',
    size_bytes BIGINT NOT NULL DEFAULT 0,
    document_kind VARCHAR(40) NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    storage_key VARCHAR(500),
    external_url TEXT,
    uploaded_by_user_id VARCHAR(100) NOT NULL,
    uploaded_by_name VARCHAR(200),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ,
    archived_by_user_id VARCHAR(100),

    CONSTRAINT ck_po_doc_kind CHECK (document_kind IN (
        'pdf', 'spreadsheet', 'presentation', 'document', 'image', 'video', 'external_link'
    )),
    CONSTRAINT ck_po_doc_status CHECK (status IN ('active', 'archived')),
    CONSTRAINT ck_po_doc_storage CHECK (
        (document_kind = 'external_link' AND external_url IS NOT NULL AND btrim(external_url) <> '')
        OR (document_kind <> 'external_link' AND storage_key IS NOT NULL AND btrim(storage_key) <> '')
    ),
    CONSTRAINT ck_po_doc_size CHECK (size_bytes >= 0)
);

CREATE INDEX IF NOT EXISTS ix_po_docs_exercise_active
    ON planejamento_orcamentario.support_documents (exercise_id, status, display_order);

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.reading_acknowledgements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id UUID NOT NULL REFERENCES planejamento_orcamentario.budget_exercises(id),
    guidance_version_id UUID NOT NULL REFERENCES planejamento_orcamentario.guidance_versions(id),
    user_sub VARCHAR(100) NOT NULL,
    user_name VARCHAR(200),
    acknowledged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_id VARCHAR(100),
    CONSTRAINT uq_po_ack_user_version UNIQUE (user_sub, guidance_version_id)
);

CREATE INDEX IF NOT EXISTS ix_po_ack_exercise_user
    ON planejamento_orcamentario.reading_acknowledgements (exercise_id, user_sub);

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.user_org_scopes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_sub VARCHAR(100) NOT NULL,
    user_name VARCHAR(200),
    user_email VARCHAR(320),
    unit_code VARCHAR(20) NOT NULL REFERENCES planejamento_orcamentario.org_units(code),
    area_code VARCHAR(40) REFERENCES planejamento_orcamentario.org_areas(code),
    cost_center_code VARCHAR(40) REFERENCES planejamento_orcamentario.org_cost_centers(code),
    scope_level VARCHAR(30) NOT NULL,
    role_in_scope VARCHAR(30) NOT NULL DEFAULT 'editor',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    valid_from DATE,
    valid_to DATE,
    assigned_by_user_id VARCHAR(100) NOT NULL,
    assigned_by_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deactivated_at TIMESTAMPTZ,
    deactivated_by_user_id VARCHAR(100),

    CONSTRAINT ck_po_scope_level CHECK (scope_level IN (
        'unit', 'area', 'cost_center', 'directorate', 'admin'
    )),
    CONSTRAINT ck_po_scope_role CHECK (role_in_scope IN ('viewer', 'editor', 'owner')),
    CONSTRAINT ck_po_scope_validity CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from),
    CONSTRAINT ck_po_scope_cc_level CHECK (
        (scope_level = 'cost_center' AND cost_center_code IS NOT NULL)
        OR (scope_level <> 'cost_center')
    ),
    CONSTRAINT ck_po_scope_area_level CHECK (
        (scope_level = 'area' AND area_code IS NOT NULL)
        OR (scope_level <> 'area')
    )
);

CREATE INDEX IF NOT EXISTS ix_po_scopes_user_active
    ON planejamento_orcamentario.user_org_scopes (user_sub)
    WHERE active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_scopes_unit_cc
    ON planejamento_orcamentario.user_org_scopes (unit_code, cost_center_code)
    WHERE active = TRUE;

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id UUID REFERENCES planejamento_orcamentario.budget_exercises(id),
    entity_type VARCHAR(80) NOT NULL,
    entity_id UUID,
    action VARCHAR(80) NOT NULL,
    actor_user_id VARCHAR(100) NOT NULL,
    actor_name VARCHAR(200),
    before_state JSONB,
    after_state JSONB,
    request_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_po_audit_exercise_created
    ON planejamento_orcamentario.audit_events (exercise_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_po_audit_entity
    ON planejamento_orcamentario.audit_events (entity_type, entity_id);

-- Impede UPDATE/DELETE em auditoria (append-only)
CREATE OR REPLACE FUNCTION planejamento_orcamentario.prevent_audit_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'audit_events is append-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_po_audit_no_update ON planejamento_orcamentario.audit_events;
CREATE TRIGGER trg_po_audit_no_update
    BEFORE UPDATE OR DELETE ON planejamento_orcamentario.audit_events
    FOR EACH ROW EXECUTE PROCEDURE planejamento_orcamentario.prevent_audit_mutation();
