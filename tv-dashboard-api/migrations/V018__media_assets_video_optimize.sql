-- Metadados de otimização de vídeo (faststart + poster sidecar).
ALTER TABLE tv_dashboard.media_assets
  ADD COLUMN IF NOT EXISTS poster_stored_name TEXT,
  ADD COLUMN IF NOT EXISTS duration_ms INTEGER,
  ADD COLUMN IF NOT EXISTS width_px INTEGER,
  ADD COLUMN IF NOT EXISTS height_px INTEGER,
  ADD COLUMN IF NOT EXISTS video_optimized_at TIMESTAMPTZ;
