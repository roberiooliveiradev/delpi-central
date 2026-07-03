-- Transformômetro — DEFAULT gen_random_uuid() em setores.setor_id (alinhado a filiais)
-- V012 migrou PK para UUID sem default; INSERT via CRUD omitia setor_id → NOT NULL violation.
BEGIN;

ALTER TABLE transformometro.setores
    ALTER COLUMN setor_id SET DEFAULT gen_random_uuid();

COMMIT;
