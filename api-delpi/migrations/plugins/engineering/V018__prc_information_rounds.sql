-- PRC-REF-019 — rodadas de esclarecimento com o solicitante.
-- Perguntas tipadas + respostas versionadas; histórico append-only.
-- Não altera SB1/SA5/revisões técnicas nem escreve no TOTVS.
-- Independente de product_registration_flags (D16).

CREATE TABLE IF NOT EXISTS engineering.product_registration_info_rounds (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id                  UUID NOT NULL
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    sequence                    INT NOT NULL,
    origin_status               VARCHAR(32) NOT NULL,
    status                      VARCHAR(32) NOT NULL DEFAULT 'awaiting_requester'
        CHECK (status IN (
            'awaiting_requester',
            'awaiting_review',
            'resolved'
        )),
    parent_round_id             UUID
        REFERENCES engineering.product_registration_info_rounds (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    requested_by_subject        VARCHAR(200) NOT NULL,
    requested_by_display_name   VARCHAR(255),
    requester_subject           VARCHAR(200) NOT NULL,
    message                     TEXT,
    row_version                 BIGINT NOT NULL DEFAULT 1,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at                 TIMESTAMPTZ,
    resolved_by_subject         VARCHAR(200),
    resolved_by_display_name    VARCHAR(255),

    CONSTRAINT uq_prc_info_rounds_request_seq
        UNIQUE (request_id, sequence),
    CONSTRAINT ck_prc_info_rounds_message_len
        CHECK (message IS NULL OR char_length(message) <= 1000),
    CONSTRAINT ck_prc_info_rounds_sequence_pos
        CHECK (sequence >= 1)
);

CREATE TABLE IF NOT EXISTS engineering.product_registration_info_questions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    round_id            UUID NOT NULL
        REFERENCES engineering.product_registration_info_rounds (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    request_id          UUID NOT NULL
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    ordinal             INT NOT NULL,
    target_type         VARCHAR(32) NOT NULL
        CHECK (target_type IN ('FIELD', 'SUPPLIER_LINK', 'GENERAL')),
    target_path         VARCHAR(120),
    target_attribute    VARCHAR(32),
    supplier_key        JSONB,
    target_key          VARCHAR(240) NOT NULL,
    target_label        VARCHAR(255) NOT NULL,
    question_text       TEXT NOT NULL,
    status              VARCHAR(32) NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending',
            'drafted',
            'submitted',
            'accepted',
            'follow_up_requested'
        )),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_prc_info_questions_round_ordinal
        UNIQUE (round_id, ordinal),
    CONSTRAINT ck_prc_info_questions_text_len
        CHECK (
            char_length(question_text) >= 1
            AND char_length(question_text) <= 1000
        ),
    CONSTRAINT ck_prc_info_questions_ordinal_pos
        CHECK (ordinal >= 1),
    CONSTRAINT ck_prc_info_questions_attribute
        CHECK (
            target_attribute IS NULL
            OR target_attribute IN ('partNumber', 'catalogNumber')
        )
);

CREATE TABLE IF NOT EXISTS engineering.product_registration_info_answers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id         UUID NOT NULL
        REFERENCES engineering.product_registration_info_questions (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    round_id            UUID NOT NULL
        REFERENCES engineering.product_registration_info_rounds (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    request_id          UUID NOT NULL
        REFERENCES engineering.product_registration_requests (id)
        ON UPDATE RESTRICT ON DELETE RESTRICT,
    author_subject      VARCHAR(200) NOT NULL,
    text                TEXT NOT NULL DEFAULT '',
    status              VARCHAR(16) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'submitted')),
    row_version         BIGINT NOT NULL DEFAULT 1,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    submitted_at        TIMESTAMPTZ,

    CONSTRAINT uq_prc_info_answers_question
        UNIQUE (question_id),
    CONSTRAINT ck_prc_info_answers_text_len
        CHECK (char_length(text) <= 4000)
);

CREATE INDEX IF NOT EXISTS ix_prc_info_rounds_request_status
    ON engineering.product_registration_info_rounds
        (request_id, status, sequence DESC);

CREATE INDEX IF NOT EXISTS ix_prc_info_rounds_requester
    ON engineering.product_registration_info_rounds
        (requester_subject, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS ix_prc_info_questions_request
    ON engineering.product_registration_info_questions
        (request_id, status, ordinal);

CREATE INDEX IF NOT EXISTS ix_prc_info_questions_round
    ON engineering.product_registration_info_questions
        (round_id, ordinal);

CREATE INDEX IF NOT EXISTS ix_prc_info_answers_request
    ON engineering.product_registration_info_answers
        (request_id, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS ix_prc_info_answers_round
    ON engineering.product_registration_info_answers
        (round_id, status);

COMMENT ON TABLE engineering.product_registration_info_rounds IS
    'PRC-REF-019: rodadas de solicitação de informações ao solicitante.';
COMMENT ON TABLE engineering.product_registration_info_questions IS
    'PRC-REF-019: perguntas tipadas (FIELD/SUPPLIER_LINK/GENERAL) por rodada.';
COMMENT ON TABLE engineering.product_registration_info_answers IS
    'PRC-REF-019: respostas do solicitante (rascunho/enviado) por pergunta.';
