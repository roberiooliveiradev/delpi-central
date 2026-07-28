-- Seções da programação (agrupamento + defaults/master por seção).
CREATE TABLE IF NOT EXISTS tv_dashboard.playlist_sections (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  playlist_id            UUID NOT NULL REFERENCES tv_dashboard.playlists(id) ON DELETE CASCADE,
  name                   TEXT NOT NULL,
  sort_order             INTEGER NOT NULL,
  is_collapsed           BOOLEAN NOT NULL DEFAULT FALSE,
  is_active              BOOLEAN NOT NULL DEFAULT TRUE,
  default_duration_sec   INTEGER NULL,
  transition_style       TEXT NULL,
  master_config          JSONB NOT NULL DEFAULT '{}',
  created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT playlist_sections_transition_style_chk
    CHECK (
      transition_style IS NULL
      OR transition_style IN ('fade', 'slide', 'none')
    ),
  CONSTRAINT playlist_sections_duration_chk
    CHECK (
      default_duration_sec IS NULL
      OR (default_duration_sec >= 5 AND default_duration_sec <= 600)
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_playlist_sections_playlist_order
  ON tv_dashboard.playlist_sections (playlist_id, sort_order);

CREATE INDEX IF NOT EXISTS idx_playlist_sections_playlist
  ON tv_dashboard.playlist_sections (playlist_id);

ALTER TABLE tv_dashboard.slides
  ADD COLUMN IF NOT EXISTS section_id UUID
    REFERENCES tv_dashboard.playlist_sections(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_slides_section_id
  ON tv_dashboard.slides (section_id)
  WHERE section_id IS NOT NULL;
