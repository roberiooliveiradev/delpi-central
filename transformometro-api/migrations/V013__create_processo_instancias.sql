-- Transformômetro — instâncias operacionais (processo × filial × setor)
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.processo_instancias (
    instancia_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processo_id UUID NOT NULL REFERENCES transformometro.processos (processo_id) ON DELETE CASCADE,
    filial_id UUID NOT NULL REFERENCES transformometro.filiais (filial_id),
    setor_id UUID NOT NULL REFERENCES transformometro.setores (setor_id),
    rotulo_instancia VARCHAR(255),
    status_instancia VARCHAR(32) NOT NULL DEFAULT 'ativo',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_processo_instancias_par UNIQUE (processo_id, filial_id, setor_id)
);

CREATE INDEX IF NOT EXISTS idx_processo_instancias_processo
    ON transformometro.processo_instancias (processo_id)
    WHERE deletado = FALSE;

CREATE INDEX IF NOT EXISTS idx_processo_instancias_filial_setor
    ON transformometro.processo_instancias (filial_id, setor_id)
    WHERE deletado = FALSE;

COMMIT;
