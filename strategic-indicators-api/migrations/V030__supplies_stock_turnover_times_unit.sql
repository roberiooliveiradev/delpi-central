-- Giro de Estoque: indicador em vezes (CPV total ÷ estoque), não em meses.

BEGIN;

UPDATE strategic_indicators.department_indicators
SET
    indicator_name = 'Giro de Estoque',
    strategic_description = 'Giro de estoque em vezes (CPV total ÷ valor de estoque) no período.',
    source_key = 'supplies_inventory_turnover',
    value_unit = 'times',
    value_suffix = ' x',
    value_decimals = 2,
    updated_at = NOW()
WHERE indicator_id = 'supplies-stock-turnover';

COMMIT;
