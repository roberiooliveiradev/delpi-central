BEGIN;

CREATE TABLE IF NOT EXISTS cipa.user_signature_profiles (
    user_id UUID PRIMARY KEY,
    display_name VARCHAR(200) NOT NULL,
    signature_path TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMIT;
