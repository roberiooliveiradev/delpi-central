-- Planejamento Orçamentário — responsabilidades orçamentárias por centro de custo (Fase 2A.1)
-- Schema: planejamento_orcamentario
-- unit_id / area_id / cost_center_id = códigos do catálogo interno (org_*), não UUIDs TOTVS.

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.budget_responsibilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id UUID NOT NULL REFERENCES planejamento_orcamentario.budget_exercises(id),
    module VARCHAR(40) NOT NULL,
    user_sub VARCHAR(100) NOT NULL,
    user_name_snapshot VARCHAR(200),
    user_email_snapshot VARCHAR(320),
    unit_id VARCHAR(20) NOT NULL REFERENCES planejamento_orcamentario.org_units(code),
    area_id VARCHAR(40) REFERENCES planejamento_orcamentario.org_areas(code),
    cost_center_id VARCHAR(40) NOT NULL REFERENCES planejamento_orcamentario.org_cost_centers(code),
    responsibility_type VARCHAR(30) NOT NULL,
    valid_from DATE,
    valid_until DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(100),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deactivated_by VARCHAR(100),
    deactivated_at TIMESTAMPTZ,
    deactivation_reason TEXT,

    CONSTRAINT ck_po_budget_resp_module CHECK (module IN ('capex')),
    CONSTRAINT ck_po_budget_resp_type CHECK (responsibility_type IN ('owner', 'collaborator')),
    CONSTRAINT ck_po_budget_resp_validity CHECK (
        valid_until IS NULL OR valid_from IS NULL OR valid_until >= valid_from
    )
);

-- Duplicidade ativa: um vínculo ativo por exercício + módulo + usuário + CC
CREATE UNIQUE INDEX IF NOT EXISTS uq_po_budget_resp_active_unique
    ON planejamento_orcamentario.budget_responsibilities (
        exercise_id, module, user_sub, cost_center_id
    )
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_budget_resp_exercise
    ON planejamento_orcamentario.budget_responsibilities (exercise_id);

CREATE INDEX IF NOT EXISTS ix_po_budget_resp_user
    ON planejamento_orcamentario.budget_responsibilities (user_sub);

CREATE INDEX IF NOT EXISTS ix_po_budget_resp_module
    ON planejamento_orcamentario.budget_responsibilities (module);

CREATE INDEX IF NOT EXISTS ix_po_budget_resp_unit
    ON planejamento_orcamentario.budget_responsibilities (unit_id);

CREATE INDEX IF NOT EXISTS ix_po_budget_resp_area
    ON planejamento_orcamentario.budget_responsibilities (area_id)
    WHERE area_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_po_budget_resp_cost_center
    ON planejamento_orcamentario.budget_responsibilities (cost_center_id);

CREATE INDEX IF NOT EXISTS ix_po_budget_resp_active
    ON planejamento_orcamentario.budget_responsibilities (is_active)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS ix_po_budget_resp_exercise_user_module
    ON planejamento_orcamentario.budget_responsibilities (exercise_id, user_sub, module)
    WHERE is_active = TRUE;
