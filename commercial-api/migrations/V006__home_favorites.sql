-- Favoritos do hub Início (por usuário JWT).

CREATE TABLE IF NOT EXISTS commercial.home_favorites (
    user_id    TEXT PRIMARY KEY,
    items      JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
