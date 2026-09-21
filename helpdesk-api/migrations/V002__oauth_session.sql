CREATE TABLE IF NOT EXISTS helpdesk.oauth_states (
    state_hash VARCHAR(64) PRIMARY KEY,
    subject TEXT NOT NULL,
    code_verifier_ciphertext TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS helpdesk.oauth_sessions (
    subject TEXT PRIMARY KEY,
    access_token_ciphertext TEXT NOT NULL,
    refresh_token_ciphertext TEXT NOT NULL,
    access_expires_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
