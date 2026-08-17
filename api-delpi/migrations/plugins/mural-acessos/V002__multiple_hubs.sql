CREATE TABLE IF NOT EXISTS mural_acessos.hubs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(80) NOT NULL,
    subtitle TEXT NOT NULL DEFAULT '',
    public_token VARCHAR(40) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_mural_acessos_hubs_title_not_blank
        CHECK (char_length(btrim(title)) >= 1),
    CONSTRAINT ck_mural_acessos_hubs_token_format
        CHECK (public_token ~ '^[a-z0-9]([a-z0-9-]{0,38}[a-z0-9])?$'),
    CONSTRAINT uq_mural_acessos_hubs_public_token UNIQUE (public_token)
);

INSERT INTO mural_acessos.hubs (title, subtitle, public_token)
SELECT
    COALESCE(NULLIF(btrim(title), ''), 'Acessos DELPI'),
    COALESCE(subtitle, ''),
    'mural'
FROM mural_acessos.hub_settings
WHERE id = 1
  AND NOT EXISTS (
      SELECT 1 FROM mural_acessos.hubs WHERE public_token = 'mural'
  );

INSERT INTO mural_acessos.hubs (title, subtitle, public_token)
SELECT 'Acessos DELPI', 'Toque no ícone para abrir', 'mural'
WHERE NOT EXISTS (SELECT 1 FROM mural_acessos.hubs);

ALTER TABLE mural_acessos.links
    ADD COLUMN IF NOT EXISTS hub_id UUID;

UPDATE mural_acessos.links
SET hub_id = (
    SELECT id FROM mural_acessos.hubs WHERE public_token = 'mural' LIMIT 1
)
WHERE hub_id IS NULL;

ALTER TABLE mural_acessos.links
    ALTER COLUMN hub_id SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_mural_acessos_links_hub'
    ) THEN
        ALTER TABLE mural_acessos.links
            ADD CONSTRAINT fk_mural_acessos_links_hub
            FOREIGN KEY (hub_id)
            REFERENCES mural_acessos.hubs(id)
            ON DELETE CASCADE;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_mural_acessos_links_hub_order
    ON mural_acessos.links (hub_id, order_index ASC, title ASC);

DROP TABLE IF EXISTS mural_acessos.hub_settings;
