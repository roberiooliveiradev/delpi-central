-- Transformômetro — documentação textual do processo (Markdown source)
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.process_documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processo_id UUID NOT NULL
        REFERENCES transformometro.processos (processo_id),
    title VARCHAR(200) NOT NULL,
    content_md TEXT NOT NULL DEFAULT '',
    created_by_user_id VARCHAR(100) NOT NULL,
    updated_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_process_documents_processo_updated
    ON transformometro.process_documents (processo_id, updated_at DESC)
    WHERE deleted_at IS NULL;

COMMIT;
