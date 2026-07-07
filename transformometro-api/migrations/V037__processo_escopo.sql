-- Transformômetro — amarração processo-mestre × unidades × departamentos
BEGIN;

ALTER TABLE transformometro.processos
    ADD COLUMN IF NOT EXISTS todas_filiais_ativas BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS transformometro.processo_filiais (
    processo_id UUID NOT NULL
        REFERENCES transformometro.processos (processo_id) ON DELETE CASCADE,
    filial_id UUID NOT NULL
        REFERENCES transformometro.filiais (filial_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (processo_id, filial_id)
);

CREATE INDEX IF NOT EXISTS idx_processo_filiais_filial
    ON transformometro.processo_filiais (filial_id);

CREATE TABLE IF NOT EXISTS transformometro.processo_setores (
    processo_id UUID NOT NULL
        REFERENCES transformometro.processos (processo_id) ON DELETE CASCADE,
    setor_id UUID NOT NULL
        REFERENCES transformometro.setores (setor_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (processo_id, setor_id)
);

CREATE INDEX IF NOT EXISTS idx_processo_setores_setor
    ON transformometro.processo_setores (setor_id);

-- Backfill a partir das melhorias existentes
UPDATE transformometro.processos p
SET todas_filiais_ativas = TRUE
WHERE EXISTS (
    SELECT 1
    FROM transformometro.processo_instancias pi
    WHERE pi.processo_id = p.processo_id
      AND pi.deletado = FALSE
      AND pi.todas_filiais_ativas = TRUE
);

INSERT INTO transformometro.processo_filiais (processo_id, filial_id)
SELECT DISTINCT pi.processo_id, pi.filial_id
FROM transformometro.processo_instancias pi
WHERE pi.deletado = FALSE
  AND pi.filial_id IS NOT NULL
  AND pi.todas_filiais_ativas = FALSE
ON CONFLICT (processo_id, filial_id) DO NOTHING;

INSERT INTO transformometro.processo_setores (processo_id, setor_id)
SELECT DISTINCT pi.processo_id, pis.setor_id
FROM transformometro.processo_instancias pi
JOIN transformometro.processo_instancia_setores pis
    ON pis.instancia_id = pi.instancia_id
WHERE pi.deletado = FALSE
ON CONFLICT (processo_id, setor_id) DO NOTHING;

COMMIT;
