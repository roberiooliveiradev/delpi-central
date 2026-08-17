CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS mural_acessos.hub_settings (
    id SMALLINT PRIMARY KEY DEFAULT 1,
    title VARCHAR(80) NOT NULL DEFAULT 'Acessos DELPI',
    subtitle TEXT NOT NULL DEFAULT 'Toque no ícone para abrir',
    CONSTRAINT ck_mural_acessos_hub_singleton CHECK (id = 1),
    CONSTRAINT ck_mural_acessos_hub_title_not_blank
        CHECK (char_length(btrim(title)) >= 1)
);

INSERT INTO mural_acessos.hub_settings (id)
VALUES (1)
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS mural_acessos.links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(80) NOT NULL,
    url TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    order_index INT NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    image_stored_name TEXT,
    image_mime_type TEXT,
    image_size_bytes INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_user_id TEXT,
    created_by_name TEXT,
    updated_by_user_id TEXT,
    updated_by_name TEXT,
    CONSTRAINT ck_mural_acessos_title_not_blank
        CHECK (char_length(btrim(title)) >= 1),
    CONSTRAINT ck_mural_acessos_url_not_blank
        CHECK (char_length(btrim(url)) >= 8)
);

CREATE INDEX IF NOT EXISTS ix_mural_acessos_links_order
    ON mural_acessos.links (order_index ASC, title ASC);
