-- Transformômetro — catálogo de filiais (UUID + codigo_filial de negócio)
-- Sem seed: dados vêm de CRUD ou import JSON (Playbook 18 S1).
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.filiais (
    filial_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo_filial VARCHAR(16) NOT NULL,
    nome_filial VARCHAR(255) NOT NULL,
    status_filial VARCHAR(32) NOT NULL DEFAULT 'ativo',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_filiais_codigo_filial UNIQUE (codigo_filial)
);

CREATE INDEX IF NOT EXISTS idx_filiais_status
    ON transformometro.filiais (status_filial)
    WHERE deletado = FALSE;

CREATE INDEX IF NOT EXISTS idx_filiais_codigo
    ON transformometro.filiais (codigo_filial)
    WHERE deletado = FALSE;

COMMIT;
