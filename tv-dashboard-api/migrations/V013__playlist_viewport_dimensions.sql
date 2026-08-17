-- Dimensões custom do canvas (px). NULL quando viewport_profile é preset nomeado.
ALTER TABLE tv_dashboard.playlists
  ADD COLUMN IF NOT EXISTS viewport_width INTEGER,
  ADD COLUMN IF NOT EXISTS viewport_height INTEGER;

ALTER TABLE tv_dashboard.playlists
  DROP CONSTRAINT IF EXISTS playlists_viewport_dims_check;

ALTER TABLE tv_dashboard.playlists
  ADD CONSTRAINT playlists_viewport_dims_check CHECK (
    (
      viewport_width IS NULL
      AND viewport_height IS NULL
    )
    OR (
      viewport_width IS NOT NULL
      AND viewport_height IS NOT NULL
      AND viewport_width BETWEEN 64 AND 7680
      AND viewport_height BETWEEN 64 AND 7680
    )
  );
