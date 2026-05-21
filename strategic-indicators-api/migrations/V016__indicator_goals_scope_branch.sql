-- Metas por escopo: consolidado ('') e filiais ('01', '02').
-- standard ou monthly_curve em cada escopo, independentemente.

ALTER TABLE strategic_indicators.indicator_goals
    ADD COLUMN IF NOT EXISTS goal_scope_branch VARCHAR(20) NOT NULL DEFAULT '';

ALTER TABLE strategic_indicators.department_indicators
    ADD COLUMN IF NOT EXISTS supports_branch_goals BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN strategic_indicators.indicator_goals.goal_scope_branch IS
'Escopo da meta: vazio = consolidado; 01/02 = filial TOTVS. Uma meta ativa por indicador/ano/escopo.';

COMMENT ON COLUMN strategic_indicators.department_indicators.supports_branch_goals IS
'Derivado de scope_type: TRUE para indicadores consolidated (metas por filial 01/02). FALSE para per_unit.';

UPDATE strategic_indicators.indicator_goals
SET goal_scope_branch = ''
WHERE goal_scope_branch IS NULL;

DROP INDEX IF EXISTS strategic_indicators.uq_si_indicator_goals_one_active_per_year;

CREATE UNIQUE INDEX IF NOT EXISTS uq_si_indicator_goals_one_active_per_scope
    ON strategic_indicators.indicator_goals (indicator_id, goal_year, goal_scope_branch)
    WHERE is_active = TRUE;

-- Todos os indicadores consolidated aceitam meta consolidada + filiais 01/02.
UPDATE strategic_indicators.department_indicators
SET
    supports_branch_goals = (scope_type = 'consolidated'),
    updated_at = NOW()
WHERE is_active = TRUE;
