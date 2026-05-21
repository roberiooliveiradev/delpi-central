-- RH e Qualidade: IDD consolidado = média das notas das filiais 01 e 02.

BEGIN;

UPDATE strategic_indicators.departments
SET
    aggregation_mode = 'average_of_units',
    updated_at = NOW()
WHERE department_id IN ('hr', 'quality');

COMMIT;
