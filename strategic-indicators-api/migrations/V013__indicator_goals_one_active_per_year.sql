BEGIN;

-- Garante no máximo uma meta ativa por indicador/ano antes do índice único.
WITH ranked AS (
    SELECT
        id,
        ROW_NUMBER() OVER (
            PARTITION BY indicator_id, goal_year
            ORDER BY version DESC, updated_at DESC, created_at DESC
        ) AS rn
    FROM strategic_indicators.indicator_goals
    WHERE is_active = TRUE
)
UPDATE strategic_indicators.indicator_goals ig
SET
    is_active = FALSE,
    updated_at = NOW()
FROM ranked r
WHERE ig.id = r.id
  AND r.rn > 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_si_indicator_goals_one_active_per_year
    ON strategic_indicators.indicator_goals (indicator_id, goal_year)
    WHERE is_active = TRUE;

COMMENT ON INDEX strategic_indicators.uq_si_indicator_goals_one_active_per_year IS
'Garante uma única meta ativa por indicador e ano civil.';

COMMIT;
