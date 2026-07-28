-- Seção principal (única por playlist); chrome oculto no editor quando é a única seção.
ALTER TABLE tv_dashboard.playlist_sections
  ADD COLUMN IF NOT EXISTS is_main BOOLEAN NOT NULL DEFAULT FALSE;

CREATE UNIQUE INDEX IF NOT EXISTS idx_playlist_sections_one_main
  ON tv_dashboard.playlist_sections (playlist_id)
  WHERE is_main;
