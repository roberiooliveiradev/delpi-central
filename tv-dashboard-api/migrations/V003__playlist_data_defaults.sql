ALTER TABLE tv_dashboard.playlists
  ADD COLUMN IF NOT EXISTS data_defaults JSONB NOT NULL DEFAULT '{}';
