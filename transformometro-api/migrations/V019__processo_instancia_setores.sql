-- Transformômetro — amarração instância × setores (Playbook 18+)
-- Instância = processo × filial (ou todas filiais ativas); setores via N:N; revisões na instância.
BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.processo_instancia_setores (
    instancia_id UUID NOT NULL
        REFERENCES transformometro.processo_instancias (instancia_id) ON DELETE CASCADE,
    setor_id UUID NOT NULL
        REFERENCES transformometro.setores (setor_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (instancia_id, setor_id)
);

CREATE INDEX IF NOT EXISTS idx_processo_instancia_setores_setor
    ON transformometro.processo_instancia_setores (setor_id);

-- Backfill vínculos a partir da coluna legada setor_id
INSERT INTO transformometro.processo_instancia_setores (instancia_id, setor_id)
SELECT pi.instancia_id, pi.setor_id
FROM transformometro.processo_instancias pi
WHERE pi.deletado = FALSE
ON CONFLICT (instancia_id, setor_id) DO NOTHING;

-- Consolidar setores das duplicatas na instância canônica
WITH grouped AS (
    SELECT
        processo_id,
        filial_id,
        (MIN(instancia_id::text))::uuid AS canonical_id,
        ARRAY_AGG(instancia_id) AS all_ids
    FROM transformometro.processo_instancias
    WHERE deletado = FALSE
    GROUP BY processo_id, filial_id
    HAVING COUNT(*) > 1
)
INSERT INTO transformometro.processo_instancia_setores (instancia_id, setor_id)
SELECT DISTINCT g.canonical_id, pis.setor_id
FROM grouped g
CROSS JOIN LATERAL UNNEST(g.all_ids) AS u(instancia_id)
JOIN transformometro.processo_instancia_setores pis ON pis.instancia_id = u.instancia_id
ON CONFLICT (instancia_id, setor_id) DO NOTHING;

-- Consolidar instâncias duplicadas (mesmo processo × filial, setores distintos)
WITH grouped AS (
    SELECT
        processo_id,
        filial_id,
        (MIN(instancia_id::text))::uuid AS canonical_id,
        ARRAY_AGG(instancia_id) AS all_ids
    FROM transformometro.processo_instancias
    WHERE deletado = FALSE
    GROUP BY processo_id, filial_id
    HAVING COUNT(*) > 1
),
duplicates AS (
    SELECT
        g.canonical_id,
        u.instancia_id AS duplicate_id
    FROM grouped g
    CROSS JOIN LATERAL UNNEST(g.all_ids) AS u(instancia_id)
    WHERE u.instancia_id <> g.canonical_id
)
UPDATE transformometro.revisoes r
SET instancia_id = d.canonical_id
FROM duplicates d
WHERE r.instancia_id = d.duplicate_id;

WITH grouped AS (
    SELECT
        processo_id,
        filial_id,
        (MIN(instancia_id::text))::uuid AS canonical_id,
        ARRAY_AGG(instancia_id) AS all_ids
    FROM transformometro.processo_instancias
    WHERE deletado = FALSE
    GROUP BY processo_id, filial_id
    HAVING COUNT(*) > 1
),
duplicates AS (
    SELECT
        g.canonical_id,
        u.instancia_id AS duplicate_id
    FROM grouped g
    CROSS JOIN LATERAL UNNEST(g.all_ids) AS u(instancia_id)
    WHERE u.instancia_id <> g.canonical_id
)
UPDATE transformometro.dashboard_calculos dc
SET instancia_id = d.canonical_id
FROM duplicates d
WHERE dc.instancia_id = d.duplicate_id;

WITH grouped AS (
    SELECT
        processo_id,
        filial_id,
        (MIN(instancia_id::text))::uuid AS canonical_id,
        ARRAY_AGG(instancia_id) AS all_ids
    FROM transformometro.processo_instancias
    WHERE deletado = FALSE
    GROUP BY processo_id, filial_id
    HAVING COUNT(*) > 1
),
duplicates AS (
    SELECT
        g.canonical_id,
        u.instancia_id AS duplicate_id
    FROM grouped g
    CROSS JOIN LATERAL UNNEST(g.all_ids) AS u(instancia_id)
    WHERE u.instancia_id <> g.canonical_id
)
UPDATE transformometro.processo_instancias pi
SET deletado = TRUE,
    updated_at = NOW()
FROM duplicates d
WHERE pi.instancia_id = d.duplicate_id;

ALTER TABLE transformometro.processo_instancias
    ADD COLUMN IF NOT EXISTS todas_filiais_ativas BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE transformometro.processo_instancias
    DROP CONSTRAINT IF EXISTS uq_processo_instancias_par;

DROP INDEX IF EXISTS transformometro.idx_processo_instancias_filial_setor;

ALTER TABLE transformometro.processo_instancias
    DROP COLUMN IF EXISTS setor_id;

ALTER TABLE transformometro.processo_instancias
    ALTER COLUMN filial_id DROP NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_processo_instancias_processo_filial
    ON transformometro.processo_instancias (processo_id, filial_id)
    WHERE deletado = FALSE AND filial_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_processo_instancias_processo_todas_filiais
    ON transformometro.processo_instancias (processo_id)
    WHERE deletado = FALSE AND todas_filiais_ativas = TRUE;

COMMIT;
