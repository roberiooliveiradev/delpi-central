-- Canal de Denúncia — denúncias anônimas (MVP)

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS canal_denuncia.denuncias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_canal_denuncia_description_not_blank
        CHECK (char_length(btrim(description)) >= 10)
);

CREATE INDEX IF NOT EXISTS idx_canal_denuncia_denuncias_created_at
    ON canal_denuncia.denuncias (created_at DESC);
