-- Alinha aggregation_mode com regra de negócio (sem alterar V009 já aplicada em produção).
-- Comercial e Engenharia: consolidado. Produção e Suprimentos: média das unidades.

BEGIN;

UPDATE strategic_indicators.departments
SET
    aggregation_mode = 'consolidated',
    updated_at = NOW()
WHERE department_id IN ('commercial', 'engineering');

UPDATE strategic_indicators.departments
SET
    aggregation_mode = 'average_of_units',
    updated_at = NOW()
WHERE department_id IN ('production', 'supplies');

COMMIT;
