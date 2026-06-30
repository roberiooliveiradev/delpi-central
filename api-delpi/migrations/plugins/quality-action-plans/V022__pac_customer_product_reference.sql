-- Referência do cliente do material (SB1010.B1_REFEREN), distinta da referência do canal de origem.

ALTER TABLE quality.quality_action_plans
    ADD COLUMN IF NOT EXISTS customer_product_reference VARCHAR(100);

COMMENT ON COLUMN quality.quality_action_plans.customer_product_reference IS
    'Referência do cliente do produto/material (TOTVS SB1010.B1_REFEREN).';
