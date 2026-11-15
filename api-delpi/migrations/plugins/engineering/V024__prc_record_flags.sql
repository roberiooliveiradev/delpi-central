-- PRC-TRACK — bandeiras de produto acompanhado (record-scoped).
-- ADR-04/CR-07: identidade única por produto+alvo enquanto OPEN;
-- RESOLVED visível somente na revisão do encerramento; REMOVED some da
-- revisão do encerramento em diante; sem reopen — nova ocorrência =
-- novo flagId. Eventos registram a revisão vigente no ato, sem criar Vn.
-- Migration aditiva: nenhuma tabela/coluna existente é alterada.

CREATE TABLE IF NOT EXISTS engineering.product_registration_record_flags (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_id                 UUID NOT NULL
        REFERENCES engineering.product_registration_records (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    title                     VARCHAR(120) NOT NULL,
    description               TEXT         NOT NULL,
    status                    VARCHAR(16)  NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN', 'RESOLVED', 'REMOVED')),
    subject                   VARCHAR(32)  NOT NULL
        CHECK (subject IN ('FIELD', 'SUPPLIER_LINK')),
    target_path               VARCHAR(120),
    target_attribute          VARCHAR(32),
    supplier_key              JSONB,
    target_key                VARCHAR(240) NOT NULL,
    opened_revision_number    INTEGER      NOT NULL
        CHECK (opened_revision_number >= 1),
    closed_status             VARCHAR(16)
        CHECK (closed_status IS NULL
               OR closed_status IN ('RESOLVED', 'REMOVED')),
    closed_revision_number    INTEGER
        CHECK (closed_revision_number IS NULL
               OR closed_revision_number >= 1),
    row_version               BIGINT       NOT NULL DEFAULT 1,
    origin_request_id         UUID
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    created_by_subject        VARCHAR(200) NOT NULL,
    created_by_display_name   VARCHAR(255),
    created_at                TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_by_subject        VARCHAR(200) NOT NULL,
    updated_by_display_name   VARCHAR(255),
    updated_at                TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    closed_by_subject         VARCHAR(200),
    closed_by_display_name    VARCHAR(255),
    closed_at                 TIMESTAMPTZ,
    close_reason              TEXT,

    CONSTRAINT ck_prc_record_flags_title_len
        CHECK (char_length(title) <= 120 AND char_length(title) >= 1),
    CONSTRAINT ck_prc_record_flags_description_len
        CHECK (char_length(description) <= 1000),
    CONSTRAINT ck_prc_record_flags_close_coherence
        CHECK (
            (status = 'OPEN' AND closed_at IS NULL
             AND closed_revision_number IS NULL AND closed_status IS NULL)
            OR (status IN ('RESOLVED', 'REMOVED') AND closed_at IS NOT NULL
                AND closed_revision_number IS NOT NULL
                AND closed_status = status)
        )
);

-- Uma única OPEN por produto+alvo (ADR-03/CR-10).
CREATE UNIQUE INDEX IF NOT EXISTS uq_prc_record_flags_open_target
    ON engineering.product_registration_record_flags (record_id, target_key)
    WHERE status = 'OPEN';

CREATE INDEX IF NOT EXISTS ix_prc_record_flags_record_status
    ON engineering.product_registration_record_flags
        (record_id, status, opened_revision_number, created_at DESC, id);

CREATE INDEX IF NOT EXISTS ix_prc_record_flags_target
    ON engineering.product_registration_record_flags
        (record_id, target_key);

-- Eventos auditáveis por revisão de contexto (não criam revisão técnica).
CREATE TABLE IF NOT EXISTS engineering.product_registration_record_flag_events (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    flag_id          UUID NOT NULL
        REFERENCES engineering.product_registration_record_flags (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    record_id        UUID NOT NULL
        REFERENCES engineering.product_registration_records (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    event_type       VARCHAR(32) NOT NULL
        CHECK (event_type IN ('flag.created', 'flag.updated',
                              'flag.resolved', 'flag.removed')),
    revision_number  INTEGER NOT NULL CHECK (revision_number >= 1),
    actor_subject    VARCHAR(200) NOT NULL,
    actor_display_name VARCHAR(255),
    occurred_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    note             TEXT
);

CREATE INDEX IF NOT EXISTS ix_prc_record_flag_events_flag
    ON engineering.product_registration_record_flag_events
        (flag_id, occurred_at, id);

CREATE INDEX IF NOT EXISTS ix_prc_record_flag_events_record_rev
    ON engineering.product_registration_record_flag_events
        (record_id, revision_number, occurred_at, id);
