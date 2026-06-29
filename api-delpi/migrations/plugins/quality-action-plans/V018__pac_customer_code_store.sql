-- Código e loja do cliente Protheus (SA1) no plano de ação

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS customer_code VARCHAR(20),
    ADD COLUMN IF NOT EXISTS customer_store VARCHAR(10);

CREATE INDEX IF NOT EXISTS ix_quality_action_plans_customer_code_store
    ON quality.quality_action_plans (customer_code, customer_store)
    WHERE customer_code IS NOT NULL AND deleted_at IS NULL;
