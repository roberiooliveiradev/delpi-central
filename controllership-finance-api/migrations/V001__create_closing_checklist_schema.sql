-- V001 — Central de Fechamento (PROC-0072): template versionado,
-- competência mensal e snapshot imutável. Schema controllership_finance.
BEGIN;

CREATE TABLE IF NOT EXISTS controllership_finance.checklist_template (
    template_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code          VARCHAR(64)  NOT NULL UNIQUE,
    name          VARCHAR(255) NOT NULL,
    description   TEXT,
    created_by    UUID         NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS controllership_finance.checklist_template_version (
    version_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id           UUID         NOT NULL
        REFERENCES controllership_finance.checklist_template (template_id)
        ON DELETE RESTRICT,
    version               INT          NOT NULL,
    status                VARCHAR(12)  NOT NULL DEFAULT 'DRAFT'
        CHECK (status IN ('DRAFT', 'PUBLISHED', 'INACTIVE')),
    revision              INT          NOT NULL DEFAULT 1 CHECK (revision >= 1),
    effective_from_period CHAR(7)
        CHECK (effective_from_period IS NULL
               OR effective_from_period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    published_by          UUID,
    published_at          TIMESTAMPTZ,
    inactivated_by        UUID,
    inactivated_at        TIMESTAMPTZ,
    created_by            UUID         NOT NULL,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (template_id, version)
);

-- Um único DRAFT por template (corrida de criação => 409 draft_already_open).
CREATE UNIQUE INDEX IF NOT EXISTS ck_template_version_one_draft
    ON controllership_finance.checklist_template_version (template_id)
    WHERE status = 'DRAFT';

CREATE TABLE IF NOT EXISTS controllership_finance.checklist_template_item (
    item_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id        UUID         NOT NULL
        REFERENCES controllership_finance.checklist_template_version
        (version_id) ON DELETE RESTRICT,
    item_key          VARCHAR(32)  NOT NULL,
    sort_order        INT          NOT NULL,
    sheet             VARCHAR(16)  NOT NULL
        CHECK (sheet IN ('ELETRONICO', 'FISICO')),
    name              VARCHAR(255) NOT NULL,
    purpose           TEXT,
    origin_kind       VARCHAR(12)  NOT NULL
        CHECK (origin_kind IN ('TOTVS', 'EXTERNAL', 'MIXED')),
    recipient_area    VARCHAR(16)
        CHECK (recipient_area IS NULL
               OR recipient_area IN ('CONTABIL', 'FISCAL')),
    applicability     VARCHAR(12)  NOT NULL DEFAULT 'REQUIRED'
        CHECK (applicability IN ('REQUIRED', 'CONDITIONAL', 'OPTIONAL')),
    branch_scope      VARCHAR(16)  NOT NULL DEFAULT 'BOTH'
        CHECK (branch_scope IN ('MATRIX', 'BRANCH', 'BOTH')),
    totvs_report_ref  VARCHAR(8),
    requirement_notes TEXT,
    UNIQUE (version_id, item_key)
);

CREATE INDEX IF NOT EXISTS ck_template_item_version_idx
    ON controllership_finance.checklist_template_item (version_id);

CREATE TABLE IF NOT EXISTS controllership_finance.monthly_competence (
    competence_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period              CHAR(7)      NOT NULL
        CHECK (period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    template_version_id UUID         NOT NULL
        REFERENCES controllership_finance.checklist_template_version
        (version_id) ON DELETE RESTRICT,
    status              VARCHAR(12)  NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN')),
    opened_by           UUID         NOT NULL,
    opened_at           TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (period)
);

-- Snapshot congelado por cópia: nenhuma referência a conteúdo mutável do
-- template; source_* é proveniência somente (sem FK para imutabilidade).
CREATE TABLE IF NOT EXISTS controllership_finance.competence_checklist_item (
    snapshot_item_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competence_id           UUID         NOT NULL
        REFERENCES controllership_finance.monthly_competence (competence_id)
        ON DELETE RESTRICT,
    item_key                VARCHAR(32)  NOT NULL,
    sort_order              INT          NOT NULL,
    source_template_item_id UUID         NOT NULL,
    source_version_id       UUID         NOT NULL,
    sheet                   VARCHAR(16)  NOT NULL,
    name                    VARCHAR(255) NOT NULL,
    purpose                 TEXT,
    origin_kind             VARCHAR(12)  NOT NULL,
    recipient_area          VARCHAR(16),
    applicability           VARCHAR(12)  NOT NULL,
    branch_scope            VARCHAR(16)  NOT NULL,
    totvs_report_ref        VARCHAR(8),
    requirement_notes       TEXT,
    state                   VARCHAR(16)  NOT NULL DEFAULT 'EXPECTED'
        CHECK (state IN ('EXPECTED')),
    UNIQUE (competence_id, item_key)
);

CREATE INDEX IF NOT EXISTS competence_item_competence_idx
    ON controllership_finance.competence_checklist_item (competence_id);

-- Trilha append-only: sem UPDATE/DELETE por contrato de aplicação.
CREATE TABLE IF NOT EXISTS controllership_finance.closing_audit_event (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type   VARCHAR(40)  NOT NULL,
    entity_id     UUID         NOT NULL,
    competence_id UUID
        REFERENCES controllership_finance.monthly_competence (competence_id)
        ON DELETE RESTRICT,
    event_type    VARCHAR(40)  NOT NULL,
    actor_subject UUID         NOT NULL,
    detail        JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS closing_audit_entity_idx
    ON controllership_finance.closing_audit_event (entity_type, entity_id);

COMMIT;
