-- Planejamento Orçamentário — centros de custo cientes de filial (Fase 3A.1)
-- Identidade externa: (branch, code). Identificador interno: id UUID.
-- Filiais válidas: 01 (Jaraguá do Sul/SC), 02 (Rio Bananal/ES).
-- Não atribui filial padrão arbitrária: unit_code deve ser inequívoco (01|02).

-- 1) Guard de dados existentes (falha clara se ambíguo)
DO $$
DECLARE
    ambiguous_count INTEGER;
    sample_codes TEXT;
BEGIN
    SELECT COUNT(*) INTO ambiguous_count
    FROM planejamento_orcamentario.org_cost_centers
    WHERE unit_code IS NULL
       OR BTRIM(unit_code) NOT IN ('01', '02');

    IF ambiguous_count > 0 THEN
        SELECT string_agg(code, ', ' ORDER BY code) INTO sample_codes
        FROM (
            SELECT code
            FROM planejamento_orcamentario.org_cost_centers
            WHERE unit_code IS NULL
               OR BTRIM(unit_code) NOT IN ('01', '02')
            ORDER BY code
            LIMIT 20
        ) s;

        RAISE EXCEPTION
            'V007 bloqueada: % centro(s) de custo sem filial inequívoca (unit_code deve ser 01 ou 02). Corrija os dados e reaplique somente com up. Amostra de códigos: %',
            ambiguous_count,
            COALESCE(sample_codes, '(nenhum)');
    END IF;
END $$;

-- 2) Remover FKs que apontam para org_cost_centers(code)
ALTER TABLE planejamento_orcamentario.budget_responsibilities
    DROP CONSTRAINT IF EXISTS budget_responsibilities_cost_center_id_fkey;

ALTER TABLE planejamento_orcamentario.capex_investments
    DROP CONSTRAINT IF EXISTS capex_investments_cost_center_id_fkey;

ALTER TABLE planejamento_orcamentario.capex_plans
    DROP CONSTRAINT IF EXISTS capex_plans_cost_center_id_fkey;

ALTER TABLE planejamento_orcamentario.user_org_scopes
    DROP CONSTRAINT IF EXISTS user_org_scopes_cost_center_code_fkey;

-- 3) Nova tabela branch-aware
CREATE TABLE planejamento_orcamentario.org_cost_centers_v007 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch VARCHAR(2) NOT NULL,
    code VARCHAR(40) NOT NULL,
    name VARCHAR(200) NOT NULL,
    unit_code VARCHAR(20) NOT NULL
        REFERENCES planejamento_orcamentario.org_units(code),
    area_code VARCHAR(40)
        REFERENCES planejamento_orcamentario.org_areas(code),
    source VARCHAR(20) NOT NULL DEFAULT 'manual',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_user_id VARCHAR(100),

    CONSTRAINT ck_po_org_cc_branch CHECK (branch IN ('01', '02')),
    CONSTRAINT ck_po_org_cc_branch_eq_unit CHECK (branch = unit_code),
    CONSTRAINT ck_po_org_cc_source CHECK (source IN ('manual', 'erp')),
    CONSTRAINT uq_po_org_cc_branch_code UNIQUE (branch, code)
);

CREATE INDEX IF NOT EXISTS ix_po_org_cc_active
    ON planejamento_orcamentario.org_cost_centers_v007 (active)
    WHERE active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_org_cc_branch
    ON planejamento_orcamentario.org_cost_centers_v007 (branch);

CREATE INDEX IF NOT EXISTS ix_po_org_cc_unit
    ON planejamento_orcamentario.org_cost_centers_v007 (unit_code);

-- 4) Migrar linhas existentes (branch = unit_code inequívoco)
INSERT INTO planejamento_orcamentario.org_cost_centers_v007 (
    id,
    branch,
    code,
    name,
    unit_code,
    area_code,
    source,
    active,
    created_at,
    created_by_user_id
)
SELECT
    gen_random_uuid(),
    BTRIM(unit_code),
    code,
    name,
    BTRIM(unit_code),
    area_code,
    'manual',
    active,
    created_at,
    created_by_user_id
FROM planejamento_orcamentario.org_cost_centers;

DROP TABLE planejamento_orcamentario.org_cost_centers;
ALTER TABLE planejamento_orcamentario.org_cost_centers_v007
    RENAME TO org_cost_centers;

-- 5) FKs compostas: (unit_id|unit_code, cost_center code) → (branch, code)
ALTER TABLE planejamento_orcamentario.budget_responsibilities
    ADD CONSTRAINT budget_responsibilities_unit_cost_center_fkey
    FOREIGN KEY (unit_id, cost_center_id)
    REFERENCES planejamento_orcamentario.org_cost_centers(branch, code);

ALTER TABLE planejamento_orcamentario.capex_investments
    ADD CONSTRAINT capex_investments_unit_cost_center_fkey
    FOREIGN KEY (unit_id, cost_center_id)
    REFERENCES planejamento_orcamentario.org_cost_centers(branch, code);

ALTER TABLE planejamento_orcamentario.capex_plans
    ADD CONSTRAINT capex_plans_unit_cost_center_fkey
    FOREIGN KEY (unit_id, cost_center_id)
    REFERENCES planejamento_orcamentario.org_cost_centers(branch, code);

-- Escopos: MATCH SIMPLE — se cost_center_code IS NULL, FK não é checada
ALTER TABLE planejamento_orcamentario.user_org_scopes
    ADD CONSTRAINT user_org_scopes_unit_cost_center_fkey
    FOREIGN KEY (unit_code, cost_center_code)
    REFERENCES planejamento_orcamentario.org_cost_centers(branch, code);

-- 6) Uniques: identidade inclui filial
DROP INDEX IF EXISTS planejamento_orcamentario.uq_po_budget_resp_active_unique;
CREATE UNIQUE INDEX uq_po_budget_resp_active_unique
    ON planejamento_orcamentario.budget_responsibilities (
        exercise_id, module, user_sub, unit_id, cost_center_id
    )
    WHERE is_active = TRUE;

ALTER TABLE planejamento_orcamentario.capex_plans
    DROP CONSTRAINT IF EXISTS uq_po_capex_plan_exercise_cc;
ALTER TABLE planejamento_orcamentario.capex_plans
    ADD CONSTRAINT uq_po_capex_plan_exercise_unit_cc
    UNIQUE (exercise_id, unit_id, cost_center_id);

CREATE INDEX IF NOT EXISTS ix_po_capex_plan_exercise_unit_cc
    ON planejamento_orcamentario.capex_plans (exercise_id, unit_id, cost_center_id);

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_unit_cc
    ON planejamento_orcamentario.capex_investments (unit_id, cost_center_id);
