-- D16 — bandeiras de acompanhamento do atendimento PRC.
-- Soft-delete auditável; CAS por row_version; FK para a solicitação.
-- Não altera SB1/SA5/revisões técnicas.

CREATE TABLE IF NOT EXISTS engineering.product_registration_flags (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id                UUID NOT NULL
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    title                     VARCHAR(120) NOT NULL,
    description               TEXT         NOT NULL,
    status                    VARCHAR(16)  NOT NULL DEFAULT 'OPEN'
        CHECK (status IN ('OPEN', 'RESOLVED')),
    subject                   VARCHAR(32)  NOT NULL DEFAULT 'GENERAL'
        CHECK (subject IN ('GENERAL', 'FIELD', 'SUPPLIER_LINK')),
    target_path               VARCHAR(120),
    supplier_key              JSONB,
    row_version               BIGINT       NOT NULL DEFAULT 1,
    created_by_subject        VARCHAR(200) NOT NULL,
    created_by_display_name   VARCHAR(255),
    created_at                TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_by_subject        VARCHAR(200) NOT NULL,
    updated_by_display_name   VARCHAR(255),
    updated_at                TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    resolved_by_subject       VARCHAR(200),
    resolved_by_display_name  VARCHAR(255),
    resolved_at               TIMESTAMPTZ,
    deleted_by_subject        VARCHAR(200),
    deleted_by_display_name   VARCHAR(255),
    deleted_at                TIMESTAMPTZ,

    CONSTRAINT ck_prc_flags_description_len
        CHECK (char_length(description) <= 1000),
    CONSTRAINT ck_prc_flags_title_len
        CHECK (char_length(title) <= 120 AND char_length(title) >= 1)
);

CREATE INDEX IF NOT EXISTS ix_prc_flags_request_status_created
    ON engineering.product_registration_flags
        (request_id, status, created_at DESC, id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS ix_prc_flags_request_all
    ON engineering.product_registration_flags
        (request_id, created_at DESC, id);

COMMENT ON TABLE engineering.product_registration_flags IS
    'D16: bandeiras operacionais de acompanhamento do atendimento PRC; soft-delete.';
