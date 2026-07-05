CREATE SCHEMA IF NOT EXISTS tv_dashboard;

CREATE TABLE IF NOT EXISTS tv_dashboard.playlists (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  public_token      TEXT NOT NULL UNIQUE,
  name              TEXT NOT NULL,
  description       TEXT,
  viewport_profile  TEXT NOT NULL DEFAULT '1080p',
  transition_style  TEXT NOT NULL DEFAULT 'fade',
  default_duration_sec INTEGER NOT NULL DEFAULT 30,
  global_refresh_sec   INTEGER NOT NULL DEFAULT 300,
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  view_count        INTEGER NOT NULL DEFAULT 0,
  last_presented_at TIMESTAMPTZ,
  created_by        TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tv_dashboard.slides (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  playlist_id       UUID NOT NULL REFERENCES tv_dashboard.playlists(id) ON DELETE CASCADE,
  sort_order        INTEGER NOT NULL,
  slide_type        TEXT NOT NULL,
  duration_sec      INTEGER,
  title             TEXT NOT NULL,
  native_screen_key TEXT,
  native_config     JSONB NOT NULL DEFAULT '{}',
  external_url      TEXT,
  external_sandbox  TEXT DEFAULT 'allow-scripts allow-same-origin allow-presentation',
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT slides_type_check CHECK (
    (slide_type = 'native' AND native_screen_key IS NOT NULL AND external_url IS NULL)
    OR (slide_type = 'external' AND external_url IS NOT NULL AND native_screen_key IS NULL)
  )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_slides_playlist_order
  ON tv_dashboard.slides (playlist_id, sort_order);

CREATE INDEX IF NOT EXISTS idx_playlists_active
  ON tv_dashboard.playlists (is_active)
  WHERE is_active = TRUE;
