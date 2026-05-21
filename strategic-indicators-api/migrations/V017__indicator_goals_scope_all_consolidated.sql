-- Garante metas por filial para todos os indicadores consolidated (idempotente pós-V016).

UPDATE strategic_indicators.department_indicators
SET
    supports_branch_goals = (scope_type = 'consolidated'),
    updated_at = NOW()
WHERE is_active = TRUE;
