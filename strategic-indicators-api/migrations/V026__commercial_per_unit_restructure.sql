-- Comercial: departamento por unidade (average_of_units), ROL único (commercial-rol) com metas 01/02.
-- Substitui indicadores legados commercial-rol-matrix / commercial-rol-branch.

BEGIN;

UPDATE strategic_indicators.departments
SET
    aggregation_mode = 'average_of_units',
    weight_pct = 17.00,
    updated_at = NOW()
WHERE department_id = 'commercial';

UPDATE strategic_indicators.department_indicators
SET
    is_active = FALSE,
    updated_at = NOW()
WHERE indicator_id IN ('commercial-rol-matrix', 'commercial-rol-branch');

INSERT INTO strategic_indicators.department_indicators (
    indicator_id,
    department_id,
    indicator_name,
    weight_pct,
    scope_type,
    performance_direction,
    strategic_description,
    source_key,
    value_unit,
    value_prefix,
    value_suffix,
    value_decimals,
    supports_branch_goals,
    is_active,
    display_order
)
VALUES
    (
        'commercial-rol',
        'commercial',
        'ROL',
        40.00,
        'per_unit',
        'higher_is_better',
        '',
        'commercial_rol',
        'currency',
        NULL,
        NULL,
        2,
        TRUE,
        TRUE,
        0
    )
ON CONFLICT (indicator_id) DO UPDATE
SET
    department_id = EXCLUDED.department_id,
    indicator_name = EXCLUDED.indicator_name,
    weight_pct = EXCLUDED.weight_pct,
    scope_type = EXCLUDED.scope_type,
    performance_direction = EXCLUDED.performance_direction,
    strategic_description = EXCLUDED.strategic_description,
    source_key = EXCLUDED.source_key,
    value_unit = EXCLUDED.value_unit,
    value_prefix = EXCLUDED.value_prefix,
    value_suffix = EXCLUDED.value_suffix,
    value_decimals = EXCLUDED.value_decimals,
    supports_branch_goals = EXCLUDED.supports_branch_goals,
    is_active = TRUE,
    display_order = EXCLUDED.display_order,
    updated_at = NOW();

UPDATE strategic_indicators.department_indicators
SET
    scope_type = 'per_unit',
    supports_branch_goals = TRUE,
    weight_pct = CASE indicator_id
        WHEN 'commercial-closing-rate' THEN 15.00
        WHEN 'commercial-sales-order-otd' THEN 30.00
        WHEN 'commercial-new-business-rol' THEN 15.00
        ELSE weight_pct
    END,
    display_order = CASE indicator_id
        WHEN 'commercial-closing-rate' THEN 3
        WHEN 'commercial-sales-order-otd' THEN 4
        WHEN 'commercial-new-business-rol' THEN 5
        ELSE display_order
    END,
    updated_at = NOW()
WHERE department_id = 'commercial'
  AND indicator_id IN (
      'commercial-closing-rate',
      'commercial-sales-order-otd',
      'commercial-new-business-rol'
  );

COMMIT;
