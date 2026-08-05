-- Planejamento Orçamentário — base Orçamento de Pessoal (Fase 3B.1)
-- Schema: planejamento_orcamentario
-- Modelo: exercício + filial + centro de custo + linhas por cargo (catálogo interno).
-- Status de plano nesta fase: apenas draft (sem workflow).
-- Headcounts âncora da planilha: Dez/2025, Out/2026, Previsto, Dez/2027.
-- "Previsto" (headcount_forecast) mantém a nomenclatura original — sem mensalização.

-- 1) Módulo personnel nas responsabilidades (mesmo mecanismo do CAPEX)
ALTER TABLE planejamento_orcamentario.budget_responsibilities
    DROP CONSTRAINT IF EXISTS ck_po_budget_resp_module;

ALTER TABLE planejamento_orcamentario.budget_responsibilities
    ADD CONSTRAINT ck_po_budget_resp_module
    CHECK (module IN ('capex', 'personnel'));

-- 2) Catálogo interno de cargos (não vem do ERP)
CREATE TABLE IF NOT EXISTS planejamento_orcamentario.personnel_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(80) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(100),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deactivated_by VARCHAR(100),
    deactivated_at TIMESTAMPTZ,

    CONSTRAINT uq_po_personnel_position_code UNIQUE (code)
);

CREATE INDEX IF NOT EXISTS ix_po_personnel_position_active
    ON planejamento_orcamentario.personnel_positions (is_active)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_personnel_position_name
    ON planejamento_orcamentario.personnel_positions (name);

-- 3) Plano de Pessoal por exercício + filial + centro de custo
CREATE TABLE IF NOT EXISTS planejamento_orcamentario.personnel_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id UUID NOT NULL
        REFERENCES planejamento_orcamentario.budget_exercises(id),
    unit_id VARCHAR(20) NOT NULL
        REFERENCES planejamento_orcamentario.org_units(code),
    area_id VARCHAR(40)
        REFERENCES planejamento_orcamentario.org_areas(code),
    cost_center_id VARCHAR(40) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(100),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_po_personnel_plan_exercise_unit_cc
        UNIQUE (exercise_id, unit_id, cost_center_id),
    CONSTRAINT ck_po_personnel_plan_status CHECK (status IN ('draft')),
    CONSTRAINT ck_po_personnel_plan_version CHECK (version >= 1),
    CONSTRAINT personnel_plans_unit_cost_center_fkey
        FOREIGN KEY (unit_id, cost_center_id)
        REFERENCES planejamento_orcamentario.org_cost_centers(branch, code)
);

CREATE INDEX IF NOT EXISTS ix_po_personnel_plan_exercise
    ON planejamento_orcamentario.personnel_plans (exercise_id);

CREATE INDEX IF NOT EXISTS ix_po_personnel_plan_unit_cc
    ON planejamento_orcamentario.personnel_plans (unit_id, cost_center_id);

CREATE INDEX IF NOT EXISTS ix_po_personnel_plan_status
    ON planejamento_orcamentario.personnel_plans (status);

CREATE INDEX IF NOT EXISTS ix_po_personnel_plan_updated
    ON planejamento_orcamentario.personnel_plans (updated_at DESC);

-- 4) Linhas de headcount por cargo
CREATE TABLE IF NOT EXISTS planejamento_orcamentario.personnel_plan_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL
        REFERENCES planejamento_orcamentario.personnel_plans(id),
    position_id UUID NOT NULL
        REFERENCES planejamento_orcamentario.personnel_positions(id),
    -- Âncoras da planilha (inteiros ≥ 0; NULL = rascunho parcial)
    headcount_dec_2025 INTEGER,
    headcount_oct_2026 INTEGER,
    headcount_forecast INTEGER,  -- coluna "Previsto" (nomenclatura original)
    headcount_dec_2027 INTEGER,
    observations TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_po_personnel_line_version CHECK (version >= 1),
    CONSTRAINT ck_po_personnel_line_hc_dec_2025
        CHECK (headcount_dec_2025 IS NULL OR headcount_dec_2025 >= 0),
    CONSTRAINT ck_po_personnel_line_hc_oct_2026
        CHECK (headcount_oct_2026 IS NULL OR headcount_oct_2026 >= 0),
    CONSTRAINT ck_po_personnel_line_hc_forecast
        CHECK (headcount_forecast IS NULL OR headcount_forecast >= 0),
    CONSTRAINT ck_po_personnel_line_hc_dec_2027
        CHECK (headcount_dec_2027 IS NULL OR headcount_dec_2027 >= 0)
);

-- Um cargo ativo por plano (código de cargo não se repete no mesmo plano)
CREATE UNIQUE INDEX IF NOT EXISTS uq_po_personnel_plan_line_active_position
    ON planejamento_orcamentario.personnel_plan_lines (plan_id, position_id)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_personnel_plan_line_plan
    ON planejamento_orcamentario.personnel_plan_lines (plan_id)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_personnel_plan_line_position
    ON planejamento_orcamentario.personnel_plan_lines (position_id);
