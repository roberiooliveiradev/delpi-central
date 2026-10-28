ALTER TABLE helpdesk.glpi_user_tokens
    ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'provisioned',
    ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMPTZ;
