-- Cultura DELPI — conteúdo institucional editável (singleton)

CREATE TABLE IF NOT EXISTS cultura_delpi.content (
    id SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    proposito TEXT NOT NULL DEFAULT '',
    missao TEXT NOT NULL DEFAULT '',
    visao TEXT NOT NULL DEFAULT '',
    valores JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by_user_id VARCHAR(100),
    updated_by_name VARCHAR(200)
);

INSERT INTO cultura_delpi.content (id)
VALUES (1)
ON CONFLICT (id) DO NOTHING;
