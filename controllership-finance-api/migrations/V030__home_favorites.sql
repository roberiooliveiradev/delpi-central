-- Favoritos do hub Início (por usuário JWT).
-- Home-hub H2 — espelho do commercial.home_favorites (V006).

CREATE TABLE IF NOT EXISTS controllership_finance.home_favorites (
    user_id    TEXT PRIMARY KEY,
    items      JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
