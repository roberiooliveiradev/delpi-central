CREATE TABLE IF NOT EXISTS tv_dashboard.media_assets (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  playlist_id       UUID NOT NULL REFERENCES tv_dashboard.playlists(id) ON DELETE CASCADE,
  stored_name       TEXT NOT NULL,
  original_name     TEXT,
  mime_type         TEXT NOT NULL,
  media_kind        TEXT NOT NULL,
  file_size_bytes   INTEGER NOT NULL,
  created_by        TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT media_assets_kind_check CHECK (media_kind IN ('image', 'video'))
);

CREATE INDEX IF NOT EXISTS idx_media_assets_playlist
  ON tv_dashboard.media_assets (playlist_id);
