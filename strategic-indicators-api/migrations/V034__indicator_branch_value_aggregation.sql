-- branch_value_aggregation: rollup entre filiais 01/02 na visão consolidado.

BEGIN;

ALTER TABLE strategic_indicators.department_indicators
    ADD COLUMN IF NOT EXISTS branch_value_aggregation VARCHAR(32) NOT NULL DEFAULT 'auto';

ALTER TABLE strategic_indicators.department_indicators
    DROP CONSTRAINT IF EXISTS ck_si_department_indicators_branch_value_aggregation;

ALTER TABLE strategic_indicators.department_indicators
    ADD CONSTRAINT ck_si_department_indicators_branch_value_aggregation
    CHECK (
        branch_value_aggregation IN (
            'auto',
            'sum',
            'average',
            'source_consolidated'
        )
    );

COMMENT ON COLUMN strategic_indicators.department_indicators.branch_value_aggregation IS
'Rollup entre filiais na visão consolidado: auto (por value_unit), sum, average ou source_consolidated.';

UPDATE strategic_indicators.department_indicators
SET branch_value_aggregation = 'sum'
WHERE indicator_id IN (
    'commercial-rol',
    'commercial-rol-weg',
    'commercial-rol-new-business',
    'supplies-negotiation-savings'
);

UPDATE strategic_indicators.department_indicators
SET branch_value_aggregation = 'average'
WHERE indicator_id IN (
    'commercial-closing-rate',
    'commercial-sales-order-otd',
    'commercial-new-business-rol-pct'
);

UPDATE strategic_indicators.department_indicators
SET branch_value_aggregation = 'source_consolidated'
WHERE is_active = TRUE
  AND value_unit = 'ppm';

COMMIT;
