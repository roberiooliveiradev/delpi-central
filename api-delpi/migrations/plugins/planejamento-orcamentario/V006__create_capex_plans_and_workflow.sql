-- Planejamento Orçamentário — planejamento CAPEX por CC + histórico (Fase 2C.1)
-- Schema: planejamento_orcamentario
-- Aprovação sobre o conjunto de investimentos do exercício+centro (não linha a linha).
-- Histórico append-only (sem UPDATE/DELETE de linhas de histórico).

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.capex_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id UUID NOT NULL REFERENCES planejamento_orcamentario.budget_exercises(id),
    unit_id VARCHAR(20) NOT NULL REFERENCES planejamento_orcamentario.org_units(code),
    area_id VARCHAR(40) REFERENCES planejamento_orcamentario.org_areas(code),
    cost_center_id VARCHAR(40) NOT NULL REFERENCES planejamento_orcamentario.org_cost_centers(code),
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    version INTEGER NOT NULL DEFAULT 1,
    submitted_by VARCHAR(100),
    submitted_at TIMESTAMPTZ,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMPTZ,
    decision_comment TEXT,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(100),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_po_capex_plan_exercise_cc UNIQUE (exercise_id, cost_center_id),
    CONSTRAINT ck_po_capex_plan_status CHECK (status IN (
        'draft',
        'submitted',
        'changes_requested',
        'rejected',
        'approved'
    )),
    CONSTRAINT ck_po_capex_plan_version CHECK (version >= 1)
);

CREATE INDEX IF NOT EXISTS ix_po_capex_plan_exercise
    ON planejamento_orcamentario.capex_plans (exercise_id);

CREATE INDEX IF NOT EXISTS ix_po_capex_plan_cost_center
    ON planejamento_orcamentario.capex_plans (cost_center_id);

CREATE INDEX IF NOT EXISTS ix_po_capex_plan_status
    ON planejamento_orcamentario.capex_plans (status);

CREATE INDEX IF NOT EXISTS ix_po_capex_plan_unit_area
    ON planejamento_orcamentario.capex_plans (unit_id, area_id);

CREATE INDEX IF NOT EXISTS ix_po_capex_plan_submitted_by
    ON planejamento_orcamentario.capex_plans (submitted_by)
    WHERE submitted_by IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_po_capex_plan_updated
    ON planejamento_orcamentario.capex_plans (updated_at DESC);

CREATE TABLE IF NOT EXISTS planejamento_orcamentario.capex_plan_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES planejamento_orcamentario.capex_plans(id),
    action VARCHAR(40) NOT NULL,
    previous_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    comment TEXT,
    actor_sub VARCHAR(100) NOT NULL,
    actor_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_po_capex_plan_hist_action CHECK (action IN (
        'created',
        'submitted',
        'request_changes',
        'rejected',
        'approved'
    ))
);

CREATE INDEX IF NOT EXISTS ix_po_capex_plan_hist_plan_created
    ON planejamento_orcamentario.capex_plan_history (plan_id, created_at DESC);

-- Append-only no histórico
CREATE OR REPLACE FUNCTION planejamento_orcamentario.prevent_capex_plan_history_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'capex_plan_history is append-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_po_capex_plan_hist_no_update
    ON planejamento_orcamentario.capex_plan_history;
CREATE TRIGGER trg_po_capex_plan_hist_no_update
    BEFORE UPDATE OR DELETE ON planejamento_orcamentario.capex_plan_history
    FOR EACH ROW EXECUTE PROCEDURE planejamento_orcamentario.prevent_capex_plan_history_mutation();
