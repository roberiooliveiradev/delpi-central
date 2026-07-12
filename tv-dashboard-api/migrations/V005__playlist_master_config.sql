-- Onda 4E.3 — master slide (logo + fundo compartilhados na playlist).
ALTER TABLE tv_dashboard.playlists
  ADD COLUMN IF NOT EXISTS master_config JSONB NOT NULL DEFAULT '{}';
