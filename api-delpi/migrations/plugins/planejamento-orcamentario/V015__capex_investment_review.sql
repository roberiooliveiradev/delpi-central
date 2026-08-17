-- Planejamento Orçamentário — decisão CAPEX por investimento (não só pelo plano).
-- review_status: pending | approved | rejected. Independente de status draft/archived.
-- Histórico do plano ganha ações investment_approved / investment_rejected.

ALTER TABLE planejamento_orcamentario.capex_investments
    ADD COLUMN IF NOT EXISTS review_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS review_comment TEXT,
    ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100),
    ADD COLUMN IF NOT EXISTS reviewed_by_name VARCHAR(200),
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ;

ALTER TABLE planejamento_orcamentario.capex_investments
    DROP CONSTRAINT IF EXISTS ck_po_capex_inv_review_status;

ALTER TABLE planejamento_orcamentario.capex_investments
    ADD CONSTRAINT ck_po_capex_inv_review_status CHECK (
        review_status IN ('pending', 'approved', 'rejected')
    );

CREATE INDEX IF NOT EXISTS ix_po_capex_inv_review_status
    ON planejamento_orcamentario.capex_investments (review_status);

COMMENT ON COLUMN planejamento_orcamentario.capex_investments.review_status IS
    'Decisão do aprovador sobre este investimento: pending, approved ou rejected.';
COMMENT ON COLUMN planejamento_orcamentario.capex_investments.review_comment IS
    'Justificativa da reprovação (ou comentário opcional da aprovação).';

-- Planos já encerrados: replica a decisão do conjunto nos itens ativos.
UPDATE planejamento_orcamentario.capex_investments i
SET review_status = 'approved'
FROM planejamento_orcamentario.capex_plans p
WHERE i.exercise_id = p.exercise_id
  AND i.unit_id = p.unit_id
  AND i.cost_center_id = p.cost_center_id
  AND i.status = 'draft'
  AND p.status = 'approved'
  AND i.review_status = 'pending';

UPDATE planejamento_orcamentario.capex_investments i
SET review_status = 'rejected'
FROM planejamento_orcamentario.capex_plans p
WHERE i.exercise_id = p.exercise_id
  AND i.unit_id = p.unit_id
  AND i.cost_center_id = p.cost_center_id
  AND i.status = 'draft'
  AND p.status = 'rejected'
  AND i.review_status = 'pending';

ALTER TABLE planejamento_orcamentario.capex_plan_history
    ADD COLUMN IF NOT EXISTS investment_id UUID
        REFERENCES planejamento_orcamentario.capex_investments(id);

ALTER TABLE planejamento_orcamentario.capex_plan_history
    DROP CONSTRAINT IF EXISTS ck_po_capex_plan_hist_action;

ALTER TABLE planejamento_orcamentario.capex_plan_history
    ADD CONSTRAINT ck_po_capex_plan_hist_action CHECK (action IN (
        'created',
        'submitted',
        'request_changes',
        'rejected',
        'approved',
        'investment_approved',
        'investment_rejected'
    ));

COMMENT ON COLUMN planejamento_orcamentario.capex_plan_history.investment_id IS
    'Investimento alvo quando a ação é investment_approved ou investment_rejected.';
