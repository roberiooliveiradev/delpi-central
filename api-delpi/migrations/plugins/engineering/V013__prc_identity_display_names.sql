-- PRC identity snapshots — apresentação de ator/responsável sem
-- resolução por evento (REF-008/009). Snapshot escrito no momento da
-- ação; linhas legadas sem display_name são resolvidas por lookup
-- batch na leitura pela Engineering API.

ALTER TABLE engineering.product_registration_requests
    ADD COLUMN IF NOT EXISTS assigned_to_display_name VARCHAR(255);

ALTER TABLE engineering.product_registration_events
    ADD COLUMN IF NOT EXISTS actor_display_name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS actor_email VARCHAR(255);
