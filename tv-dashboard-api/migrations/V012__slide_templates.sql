-- Biblioteca de templates de slide (custom_message / comunicado).
CREATE TABLE IF NOT EXISTS tv_dashboard.slide_templates (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key                 TEXT NOT NULL,
  label               TEXT NOT NULL,
  description         TEXT,
  native_screen_key   TEXT NOT NULL DEFAULT 'custom_message',
  native_config       JSONB NOT NULL DEFAULT '{}'::jsonb,
  duration_sec        INTEGER,
  status              TEXT NOT NULL DEFAULT 'draft',
  is_system           BOOLEAN NOT NULL DEFAULT FALSE,
  version             INTEGER NOT NULL DEFAULT 1,
  thumbnail_json      JSONB,
  owner_user_id       TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by          TEXT,
  CONSTRAINT slide_templates_key_unique UNIQUE (key),
  CONSTRAINT slide_templates_status_check CHECK (status IN ('draft', 'published', 'archived')),
  CONSTRAINT slide_templates_version_check CHECK (version >= 1)
);

CREATE INDEX IF NOT EXISTS idx_slide_templates_status
  ON tv_dashboard.slide_templates (status);

CREATE INDEX IF NOT EXISTS idx_slide_templates_label
  ON tv_dashboard.slide_templates (label);

CREATE INDEX IF NOT EXISTS idx_slide_templates_is_system
  ON tv_dashboard.slide_templates (is_system);
