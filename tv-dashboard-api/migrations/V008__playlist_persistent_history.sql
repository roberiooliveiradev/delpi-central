ALTER TABLE tv_dashboard.playlists
  ADD COLUMN IF NOT EXISTS revision BIGINT NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS tv_dashboard.playlist_history (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  playlist_id    UUID NOT NULL REFERENCES tv_dashboard.playlists(id) ON DELETE CASCADE,
  revision       BIGINT NOT NULL,
  actor_user_id  TEXT NOT NULL,
  reason         TEXT NOT NULL,
  snapshot       JSONB NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT playlist_history_actor_nonempty CHECK (BTRIM(actor_user_id) <> ''),
  CONSTRAINT playlist_history_reason_nonempty CHECK (BTRIM(reason) <> ''),
  CONSTRAINT playlist_history_revision_nonnegative CHECK (revision >= 0),
  CONSTRAINT playlist_history_snapshot_object CHECK (jsonb_typeof(snapshot) = 'object'),
  CONSTRAINT playlist_history_playlist_revision_unique UNIQUE (playlist_id, revision)
);

CREATE INDEX IF NOT EXISTS idx_playlist_history_playlist_created
  ON tv_dashboard.playlist_history (playlist_id, created_at DESC, id DESC);

-- O limite de 500 versões por programação é lógico e aplicado na mesma
-- transação de captura, para não introduzir trigger com custo em toda escrita.
