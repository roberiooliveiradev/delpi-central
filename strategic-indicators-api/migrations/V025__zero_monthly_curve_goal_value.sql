-- goal_value em monthly_curve não é usado; a meta vive em indicator_goal_monthly_targets.
UPDATE strategic_indicators.indicator_goals
SET goal_value = 0
WHERE goal_mode = 'monthly_curve'
  AND goal_value IS DISTINCT FROM 0;
