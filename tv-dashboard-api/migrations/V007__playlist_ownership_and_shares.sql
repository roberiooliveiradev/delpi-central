-- Isolamento por dono + compartilhamento por user_id (não e-mail).
-- Link de edição: invite token que, ao ser resgatado com JWT, cria share com target_user_id.

ALTER TABLE tv_dashboard.playlists
  ADD COLUMN IF NOT EXISTS owner_user_id TEXT;

UPDATE tv_dashboard.playlists
SET owner_user_id = created_by
WHERE owner_user_id IS NULL
  AND created_by IS NOT NULL
  AND BTRIM(created_by) <> '';

CREATE INDEX IF NOT EXISTS idx_playlists_owner_user_id
  ON tv_dashboard.playlists (owner_user_id);

CREATE TABLE IF NOT EXISTS tv_dashboard.playlist_shares (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  playlist_id     UUID NOT NULL REFERENCES tv_dashboard.playlists(id) ON DELETE CASCADE,
  target_user_id  TEXT NOT NULL,
  role            TEXT NOT NULL DEFAULT 'editor',
  created_by      TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT playlist_shares_role_check CHECK (role IN ('viewer', 'editor')),
  CONSTRAINT playlist_shares_target_unique UNIQUE (playlist_id, target_user_id)
);

CREATE INDEX IF NOT EXISTS idx_playlist_shares_target
  ON tv_dashboard.playlist_shares (target_user_id);

CREATE TABLE IF NOT EXISTS tv_dashboard.playlist_edit_invites (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  playlist_id     UUID NOT NULL REFERENCES tv_dashboard.playlists(id) ON DELETE CASCADE,
  token           TEXT NOT NULL UNIQUE,
  role            TEXT NOT NULL DEFAULT 'editor',
  created_by      TEXT NOT NULL,
  expires_at      TIMESTAMPTZ,
  revoked_at      TIMESTAMPTZ,
  redeemed_at     TIMESTAMPTZ,
  redeemed_by     TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT playlist_edit_invites_role_check CHECK (role IN ('viewer', 'editor'))
);

CREATE INDEX IF NOT EXISTS idx_playlist_edit_invites_playlist
  ON tv_dashboard.playlist_edit_invites (playlist_id)
  WHERE revoked_at IS NULL;
