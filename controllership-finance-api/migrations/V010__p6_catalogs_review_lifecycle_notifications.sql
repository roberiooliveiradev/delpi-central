-- V010 — F1/F4: lifecycle REVIEW intermediário, catálogos governados P6
-- e estados de entrega da notification outbox.
--
-- Lifecycle P6 aprovado: DRAFT → REVIEW → PUBLISHED → INACTIVE
-- (effective_from_period já existente = EFFECTIVE_FROM).
-- Catálogos (E01/E05/E06/T02/P5-H/T05-binding): modelo configurável
-- aprovado; seeds ficam pendentes de decisão G1 — catálogo vazio NÃO
-- inventa semântica (fallbacks explícitos e auditados no consumo).

BEGIN;

-- 1) Lifecycle: novo estado REVIEW entre DRAFT e PUBLISHED --------------

ALTER TABLE controllership_finance.checklist_template_version
    DROP CONSTRAINT checklist_template_version_status_check;
ALTER TABLE controllership_finance.checklist_template_version
    ADD CONSTRAINT checklist_template_version_status_check
    CHECK (status IN ('DRAFT', 'REVIEW', 'PUBLISHED', 'INACTIVE'));

-- Um único draft/em-revisão aberto por template.
DROP INDEX IF EXISTS controllership_finance.ck_template_version_one_draft;
CREATE UNIQUE INDEX IF NOT EXISTS ck_template_version_one_open
    ON controllership_finance.checklist_template_version (template_id)
    WHERE status IN ('DRAFT', 'REVIEW');

-- 2) Catálogos governados P6 ---------------------------------------------
-- Configurável, sem hardcode, nunca destrutivo: desativação prospectiva
-- com auditoria; codes permanecem referenciáveis por históricos.

CREATE TABLE IF NOT EXISTS controllership_finance.closing_catalog_entry (
    entry_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    catalog_key           VARCHAR(32) NOT NULL CHECK (catalog_key IN (
        'BANK_ACCOUNT',
        'REJECTION_REASON',
        'ATTACHMENT_ROLE',
        'NOTIFICATION_TARGET',
        'PACKAGE_REQUIRED_AREA',
        'REVIEW_ELIGIBILITY'
    )),
    code                  VARCHAR(64) NOT NULL,
    label                 VARCHAR(255) NOT NULL,
    attributes            JSONB NOT NULL DEFAULT '{}'::jsonb,
    effective_from_period CHAR(7)
        CHECK (effective_from_period IS NULL
               OR effective_from_period ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    active                BOOLEAN NOT NULL DEFAULT true,
    revision              INT NOT NULL DEFAULT 1 CHECK (revision >= 1),
    created_by            UUID NOT NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by            UUID,
    updated_at            TIMESTAMPTZ,
    deactivated_by        UUID,
    deactivated_at        TIMESTAMPTZ,
    UNIQUE (catalog_key, code)
);

CREATE INDEX IF NOT EXISTS closing_catalog_key_idx
    ON controllership_finance.closing_catalog_entry (catalog_key, active);

-- 3) Notification outbox: estados de entrega reais ------------------------
-- EMITTED (registrado) → DISPATCHED (Core aceitou) | FAILED (tentativa
-- recusada/indisponível) | UNAVAILABLE (marcada manualmente).
-- Entrega nunca é critério de negócio (RQ-P5-07).

ALTER TABLE controllership_finance.closing_notification_event
    DROP CONSTRAINT closing_notification_event_delivery_state_check;
ALTER TABLE controllership_finance.closing_notification_event
    ADD CONSTRAINT closing_notification_event_delivery_state_check
    CHECK (delivery_state IN (
        'EMITTED', 'DISPATCHED', 'FAILED', 'UNAVAILABLE'
    ));

ALTER TABLE controllership_finance.closing_notification_event
    ADD COLUMN IF NOT EXISTS dispatched_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS dispatch_error VARCHAR(255);

COMMIT;
