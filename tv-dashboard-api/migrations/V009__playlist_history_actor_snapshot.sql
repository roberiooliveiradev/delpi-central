ALTER TABLE tv_dashboard.playlist_history
  ADD COLUMN IF NOT EXISTS actor_name TEXT,
  ADD COLUMN IF NOT EXISTS actor_email TEXT;
