-- Extensão de perfil de usuário do Portal Comercial (foto + cargo).

CREATE TABLE IF NOT EXISTS commercial.commercial_user_profiles (
    user_id            TEXT PRIMARY KEY,
    job_title          TEXT,
    photo_storage_key  TEXT,
    photo_file_name    TEXT,
    photo_content_type TEXT,
    photo_byte_size    INT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
