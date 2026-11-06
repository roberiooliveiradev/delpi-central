-- ============================================================================
-- ENGINEERING.PRC.C1 — Product Registration (Controle e Cadastro de Produtos)
-- Alvo: plugins_hub (delpi-postgres-plugins), schema engineering.
--
-- Contrato: PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md §6 (7 tabelas).
-- Append-only ledger de eventos; revisões imutáveis; CAS por row_version;
-- idempotência por (actor, operation, key).
-- ============================================================================

CREATE TABLE IF NOT EXISTS engineering.product_registration_requests (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_type             VARCHAR(16)  NOT NULL
        CHECK (request_type IN ('create', 'update')),
    product_type             VARCHAR(64)  NOT NULL,
    source                   VARCHAR(100) NOT NULL,
    external_request_id      VARCHAR(200),
    external_item_id         VARCHAR(200),
    requester_subject        VARCHAR(200) NOT NULL,
    requester_display_name   VARCHAR(255),
    official_product_code    VARCHAR(100),
    base_revision_number     INTEGER,
    requested_payload        JSONB        NOT NULL,
    payload_schema_version   INTEGER      NOT NULL CHECK (payload_schema_version >= 1),
    status                   VARCHAR(32)  NOT NULL DEFAULT 'submitted'
        CHECK (status IN ('submitted', 'in_progress', 'needs_information',
                          'under_review', 'completed', 'rejected')),
    assigned_to_subject      VARCHAR(200),
    row_version              BIGINT       NOT NULL DEFAULT 1,
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at             TIMESTAMPTZ,
    rejected_at              TIMESTAMPTZ,
    completed_record_id      UUID
);

-- Referência externa única por origem — NULLs tratados como distintos
-- apenas quando ambos os lados são NULL (permite múltiplas solicitações
-- sem external ids; colisão de origem+id externo é deduplicação).
CREATE UNIQUE INDEX IF NOT EXISTS uq_prc_requests_external
    ON engineering.product_registration_requests
        (source, external_request_id, COALESCE(external_item_id, ''))
    WHERE external_request_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_prc_requests_status_created
    ON engineering.product_registration_requests (status, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_prc_requests_requester
    ON engineering.product_registration_requests
        (requester_subject, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_prc_requests_assignee
    ON engineering.product_registration_requests (assigned_to_subject, status);
CREATE INDEX IF NOT EXISTS ix_prc_requests_official_code
    ON engineering.product_registration_requests (official_product_code)
    WHERE official_product_code IS NOT NULL;

CREATE TABLE IF NOT EXISTS engineering.product_registration_drafts (
    request_id          UUID PRIMARY KEY
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    schema_version      INTEGER      NOT NULL CHECK (schema_version >= 1),
    technical_data      JSONB        NOT NULL,
    changed_paths       JSONB        NOT NULL DEFAULT '[]'::jsonb,
    row_version         BIGINT       NOT NULL DEFAULT 1,
    updated_by_subject  VARCHAR(200) NOT NULL,
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS engineering.product_registration_records (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_type              VARCHAR(64)  NOT NULL,
    official_product_code     VARCHAR(100) NOT NULL,
    current_revision_number   INTEGER      NOT NULL DEFAULT 0,
    last_official_verified_at TIMESTAMPTZ  NOT NULL,
    official_source           VARCHAR(100) NOT NULL,
    created_at                TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_prc_records_official
        UNIQUE (official_source, official_product_code)
);

CREATE TABLE IF NOT EXISTS engineering.product_registration_revisions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id             UUID NOT NULL
        REFERENCES engineering.product_registration_records (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    revision_number       INTEGER NOT NULL CHECK (revision_number >= 1),
    request_id            UUID NOT NULL
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    schema_version        INTEGER NOT NULL,
    technical_snapshot    JSONB   NOT NULL,
    changes               JSONB   NOT NULL,
    official_evidence_id  UUID    NOT NULL,
    approved_by_subject   VARCHAR(200) NOT NULL,
    approved_at           TIMESTAMPTZ  NOT NULL,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_prc_revisions_record_number
        UNIQUE (record_id, revision_number)
);

CREATE TABLE IF NOT EXISTS engineering.product_registration_events (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id       UUID NOT NULL
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    sequence_number  BIGINT NOT NULL,
    event_type       VARCHAR(100) NOT NULL,
    actor_subject    VARCHAR(200) NOT NULL,
    occurred_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    reason           TEXT,
    metadata         JSONB        NOT NULL DEFAULT '{}'::jsonb,
    previous_status  VARCHAR(32),
    next_status      VARCHAR(32),

    CONSTRAINT uq_prc_events_request_seq
        UNIQUE (request_id, sequence_number)
);

CREATE TABLE IF NOT EXISTS engineering.product_registration_verifications (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id             UUID NOT NULL
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    official_product_code  VARCHAR(100) NOT NULL,
    requested_by_subject   VARCHAR(200) NOT NULL,
    checked_at             TIMESTAMPTZ  NOT NULL,
    official_source        VARCHAR(100) NOT NULL,
    result                 VARCHAR(40)  NOT NULL
        CHECK (result IN ('matched', 'mismatched', 'not_found',
                          'unavailable', 'unverifiable', 'timeout',
                          'forbidden', 'contract_error')),
    expected_fields        JSONB NOT NULL,
    observed_fields        JSONB,
    field_results          JSONB NOT NULL,
    evidence_fingerprint   VARCHAR(128),
    correlation_id         VARCHAR(128) NOT NULL,
    error_code             VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS ix_prc_verifications_request
    ON engineering.product_registration_verifications
        (request_id, checked_at DESC);

CREATE TABLE IF NOT EXISTS engineering.product_registration_idempotency (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_or_source     VARCHAR(200) NOT NULL,
    operation           VARCHAR(100) NOT NULL,
    idempotency_key     VARCHAR(200) NOT NULL,
    request_fingerprint VARCHAR(128) NOT NULL,
    request_id          UUID
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE SET NULL,
    response_status     INTEGER,
    response_payload    JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at          TIMESTAMPTZ NOT NULL,

    CONSTRAINT uq_prc_idempotency
        UNIQUE (actor_or_source, operation, idempotency_key)
);

-- FK tardia: completed_record_id → records (deferred/nullable).
ALTER TABLE engineering.product_registration_requests
    ADD CONSTRAINT fk_prc_requests_completed_record
    FOREIGN KEY (completed_record_id)
    REFERENCES engineering.product_registration_records (id)
    ON UPDATE RESTRICT ON DELETE RESTRICT;
