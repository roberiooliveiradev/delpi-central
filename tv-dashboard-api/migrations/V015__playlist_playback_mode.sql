-- Playback mode: presentation (auto-advance) | meeting (manual).
ALTER TABLE tv_dashboard.playlists
  ADD COLUMN IF NOT EXISTS playback_mode TEXT NOT NULL DEFAULT 'presentation';

ALTER TABLE tv_dashboard.playlists
  DROP CONSTRAINT IF EXISTS playlists_playback_mode_check;

ALTER TABLE tv_dashboard.playlists
  ADD CONSTRAINT playlists_playback_mode_check
  CHECK (playback_mode IN ('presentation', 'meeting'));
