CREATE TABLE IF NOT EXISTS quality.document_sequences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence_key VARCHAR(100) NOT NULL UNIQUE,
    prefix VARCHAR(20) NOT NULL,
    current_value BIGINT NOT NULL DEFAULT 0,
    padding_length INTEGER NOT NULL DEFAULT 6,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_document_sequences_padding_length
        CHECK (padding_length >= 1 AND padding_length <= 20),
    CONSTRAINT ck_document_sequences_current_value
        CHECK (current_value >= 0)
);

INSERT INTO quality.document_sequences (
    sequence_key,
    prefix,
    current_value,
    padding_length,
    active
)
VALUES
    ('external_nonconformity', 'ENC', 0, 6, TRUE)
ON CONFLICT (sequence_key) DO NOTHING;