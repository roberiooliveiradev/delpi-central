-- Planejamento Orçamentário — workflow do Orçamento de Pessoal (Fase 3C.1)
-- Expande status de personnel_plans, colunas de submissão/revisão e histórico append-only.
-- Não altera V008/V009.

-- 1) Colunas de workflow (já podem existir parcialmente em ambientes futuros)
ALTER TABLE planejamento_orcamentario.personnel_plans
    ADD COLUMN IF NOT EXISTS submitted_by VARCHAR(100);

ALTER TABLE planejamento_orcamentario.personnel_plans
    ADD COLUMN IF NOT EXISTS submitted_at TIMESTAMPTZ;

ALTER TABLE planejamento_orcamentario.personnel_plans
    ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100);

ALTER TABLE planejamento_orcamentario.personnel_plans
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

ALTER TABLE planejamento_orcamentario.personnel_plans
    ADD COLUMN IF NOT EXISTS decision_comment TEXT;

-- version já existe na V008; garante check mínimo
ALTER TABLE planejamento_orcamentario.personnel_plans
    DROP CONSTRAINT IF EXISTS ck_po_personnel_plan_version;

ALTER TABLE planejamento_orcamentario.personnel_plans
    ADD CONSTRAINT ck_po_personnel_plan_version CHECK (version >= 1);

-- 2) Expandir status permitidos
ALTER TABLE planejamento_orcamentario.personnel_plans
    DROP CONSTRAINT IF EXISTS ck_po_personnel_plan_status;

ALTER TABLE planejamento_orcamentario.personnel_plans
    ADD CONSTRAINT ck_po_personnel_plan_status CHECK (status IN (
        'draft',
        'submitted',
        'changes_requested',
        'rejected',
        'approved'
    ));

CREATE INDEX IF NOT EXISTS ix_po_personnel_plan_submitted_by
    ON planejamento_orcamentario.personnel_plans (submitted_by)
    WHERE submitted_by IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_po_personnel_plan_unit_area
    ON planejamento_orcamentario.personnel_plans (unit_id, area_id);

-- 3) Histórico append-only
CREATE TABLE IF NOT EXISTS planejamento_orcamentario.personnel_plan_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL
        REFERENCES planejamento_orcamentario.personnel_plans(id),
    action VARCHAR(40) NOT NULL,
    previous_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    comment TEXT,
    actor_sub VARCHAR(100) NOT NULL,
    actor_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_po_personnel_plan_hist_action CHECK (action IN (
        'created',
        'submitted',
        'request_changes',
        'rejected',
        'approved'
    ))
);

CREATE INDEX IF NOT EXISTS ix_po_personnel_plan_hist_plan_created
    ON planejamento_orcamentario.personnel_plan_history (plan_id, created_at DESC);

CREATE OR REPLACE FUNCTION planejamento_orcamentario.prevent_personnel_plan_history_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'personnel_plan_history is append-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_po_personnel_plan_hist_no_update
    ON planejamento_orcamentario.personnel_plan_history;
CREATE TRIGGER trg_po_personnel_plan_hist_no_update
    BEFORE UPDATE OR DELETE ON planejamento_orcamentario.personnel_plan_history
    FOR EACH ROW EXECUTE PROCEDURE planejamento_orcamentario.prevent_personnel_plan_history_mutation();
