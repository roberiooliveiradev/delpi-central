CREATE TABLE IF NOT EXISTS helpdesk.glpi_user_tokens (
    glpi_user_id INTEGER PRIMARY KEY,
    api_token_ciphertext TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
