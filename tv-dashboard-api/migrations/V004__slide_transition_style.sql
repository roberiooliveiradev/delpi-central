ALTER TABLE tv_dashboard.slides
  ADD COLUMN IF NOT EXISTS transition_style TEXT;

ALTER TABLE tv_dashboard.slides
  DROP CONSTRAINT IF EXISTS slides_transition_style_check;

ALTER TABLE tv_dashboard.slides
  ADD CONSTRAINT slides_transition_style_check
  CHECK (transition_style IS NULL OR transition_style IN ('fade', 'slide', 'none'));
