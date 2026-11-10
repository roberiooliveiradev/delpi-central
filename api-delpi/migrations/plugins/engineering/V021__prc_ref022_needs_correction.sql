-- PRC-REF-022 — status needs_correction + ciclos de devolução para correção.
-- Forward-only. Não altera V018–V020 nem apaga rodadas REF-019.

DO $$
DECLARE
    cname text;
BEGIN
    SELECT con.conname INTO cname
    FROM pg_constraint con
    WHERE con.conrelid = 'engineering.product_registration_requests'::regclass
      AND con.contype = 'c'
      AND pg_get_constraintdef(con.oid) ILIKE '%status%'
      AND pg_get_constraintdef(con.oid) ILIKE '%submitted%'
    LIMIT 1;
    IF cname IS NOT NULL THEN
        EXECUTE format(
            'ALTER TABLE engineering.product_registration_requests DROP CONSTRAINT %I',
            cname
        );
    END IF;
END $$;

ALTER TABLE engineering.product_registration_requests
    ADD CONSTRAINT ck_prc_requests_status
    CHECK (status IN (
        'submitted',
        'in_progress',
        'needs_information',
        'needs_correction',
        'under_review',
        'completed',
        'rejected'
    ));

CREATE TABLE IF NOT EXISTS engineering.product_registration_correction_returns (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id                  UUID NOT NULL
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    sequence                    INT NOT NULL,
    status                      VARCHAR(32) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'resubmitted', 'superseded')),
    origin_case_version         BIGINT NOT NULL,
    returned_by_subject         VARCHAR(200) NOT NULL,
    returned_by_display_name    VARCHAR(255),
    requester_subject           VARCHAR(200) NOT NULL,
    draft_snapshot              JSONB,
    row_version                 BIGINT NOT NULL DEFAULT 1,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resubmitted_at              TIMESTAMPTZ,
    resubmitted_by_subject      VARCHAR(200),

    CONSTRAINT uq_prc_correction_returns_request_seq
        UNIQUE (request_id, sequence),
    CONSTRAINT ck_prc_correction_returns_sequence_pos
        CHECK (sequence >= 1)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_prc_correction_returns_open
    ON engineering.product_registration_correction_returns (request_id)
    WHERE status = 'open';

CREATE TABLE IF NOT EXISTS engineering.product_registration_correction_targets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    return_id           UUID NOT NULL
        REFERENCES engineering.product_registration_correction_returns (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    request_id          UUID NOT NULL
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ordinal             INT NOT NULL,
    target_type         VARCHAR(32) NOT NULL
        CHECK (target_type IN ('FIELD', 'SUPPLIER_LINK')),
    target_path         VARCHAR(120),
    target_attribute    VARCHAR(32),
    supplier_key        JSONB,
    target_key          VARCHAR(240) NOT NULL,
    target_label        VARCHAR(255) NOT NULL,
    reason              TEXT NOT NULL,
    baseline_value      JSONB,
    addressed_at        TIMESTAMPTZ,
    addressed_by_subject VARCHAR(200),
    addressed_mode      VARCHAR(32)
        CHECK (
            addressed_mode IS NULL
            OR addressed_mode IN ('changed', 'confirmed')
        ),
    addressed_value     JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_prc_correction_targets_return_ordinal
        UNIQUE (return_id, ordinal),
    CONSTRAINT uq_prc_correction_targets_return_key
        UNIQUE (return_id, target_key),
    CONSTRAINT ck_prc_correction_targets_reason_len
        CHECK (char_length(reason) >= 3 AND char_length(reason) <= 1000),
    CONSTRAINT ck_prc_correction_targets_ordinal_pos
        CHECK (ordinal >= 1)
);

CREATE INDEX IF NOT EXISTS ix_prc_correction_returns_request
    ON engineering.product_registration_correction_returns (request_id, sequence DESC);

CREATE INDEX IF NOT EXISTS ix_prc_correction_targets_request
    ON engineering.product_registration_correction_targets (request_id);

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eng_prc') THEN
        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_correction_returns TO eng_prc;
        GRANT SELECT, INSERT, UPDATE
            ON engineering.product_registration_correction_targets TO eng_prc;
        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_correction_returns FROM eng_prc;
        REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
            ON engineering.product_registration_correction_targets FROM eng_prc;
    END IF;
END $$;

COMMENT ON TABLE engineering.product_registration_correction_returns IS
    'PRC-REF-022: ciclos de devolução para correção da ficha (não apaga REF-019).';
COMMENT ON TABLE engineering.product_registration_correction_targets IS
    'PRC-REF-022: alvos FIELD/SUPPLIER_LINK devolvidos com motivo.';
