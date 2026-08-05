-- Planejamento Orçamentário — cargo livre nas linhas de Pessoal (Fase 3B.1.1)
-- Substitui o catálogo personnel_positions por position_name textual na linha.
-- position_name: VARCHAR(200), trim obrigatório, unique ativo por plano
--   em lower(btrim(position_name)) — case-insensitive, ignora espaços nas pontas.
-- Não altera V008.

-- 1) Nova coluna (nullable até o backfill)
ALTER TABLE planejamento_orcamentario.personnel_plan_lines
    ADD COLUMN IF NOT EXISTS position_name VARCHAR(200);

-- 2) Backfill a partir do catálogo
UPDATE planejamento_orcamentario.personnel_plan_lines AS l
SET position_name = BTRIM(p.name)
FROM planejamento_orcamentario.personnel_positions AS p
WHERE l.position_id = p.id
  AND (l.position_name IS NULL OR BTRIM(l.position_name) = '');

-- 3) Guard: nenhuma linha pode ficar sem nome
DO $$
DECLARE
    missing_count INTEGER;
    sample_ids TEXT;
BEGIN
    SELECT COUNT(*) INTO missing_count
    FROM planejamento_orcamentario.personnel_plan_lines
    WHERE position_name IS NULL
       OR BTRIM(position_name) = '';

    IF missing_count > 0 THEN
        SELECT string_agg(id::text, ', ' ORDER BY id) INTO sample_ids
        FROM (
            SELECT id
            FROM planejamento_orcamentario.personnel_plan_lines
            WHERE position_name IS NULL
               OR BTRIM(position_name) = ''
            ORDER BY id
            LIMIT 20
        ) s;

        RAISE EXCEPTION
            'V009 bloqueada: % linha(s) de Pessoal sem position_name após backfill do catálogo. Corrija os dados e reaplique somente com up. Amostra de ids: %',
            missing_count,
            COALESCE(sample_ids, '(nenhum)');
    END IF;
END $$;

-- 4) Normalizar espaços e aplicar NOT NULL + check
UPDATE planejamento_orcamentario.personnel_plan_lines
SET position_name = BTRIM(position_name)
WHERE position_name IS DISTINCT FROM BTRIM(position_name);

ALTER TABLE planejamento_orcamentario.personnel_plan_lines
    ALTER COLUMN position_name SET NOT NULL;

ALTER TABLE planejamento_orcamentario.personnel_plan_lines
    DROP CONSTRAINT IF EXISTS ck_po_personnel_line_position_name;

ALTER TABLE planejamento_orcamentario.personnel_plan_lines
    ADD CONSTRAINT ck_po_personnel_line_position_name
    CHECK (BTRIM(position_name) <> '' AND char_length(position_name) <= 200);

-- 5) Remover dependências de position_id
DROP INDEX IF EXISTS planejamento_orcamentario.uq_po_personnel_plan_line_active_position;
DROP INDEX IF EXISTS planejamento_orcamentario.ix_po_personnel_plan_line_position;

ALTER TABLE planejamento_orcamentario.personnel_plan_lines
    DROP CONSTRAINT IF EXISTS personnel_plan_lines_position_id_fkey;

ALTER TABLE planejamento_orcamentario.personnel_plan_lines
    DROP COLUMN IF EXISTS position_id;

-- 6) Unique ativo por plano + nome normalizado (case-insensitive, trim)
CREATE UNIQUE INDEX IF NOT EXISTS uq_po_personnel_plan_line_active_position_name
    ON planejamento_orcamentario.personnel_plan_lines (
        plan_id,
        lower(BTRIM(position_name))
    )
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_personnel_plan_line_position_name
    ON planejamento_orcamentario.personnel_plan_lines (lower(BTRIM(position_name)));

-- 7) Remover catálogo abandonado
DROP TABLE IF EXISTS planejamento_orcamentario.personnel_positions;
