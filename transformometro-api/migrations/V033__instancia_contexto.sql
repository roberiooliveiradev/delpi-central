-- Transformômetro — contexto operacional extra por instância (Playbook 20 S3)

BEGIN;

ALTER TABLE transformometro.processo_instancias
    ADD COLUMN IF NOT EXISTS contexto JSONB;

COMMENT ON COLUMN transformometro.processo_instancias.contexto IS
    'Metadados operacionais instancia_contexto_v1 — rollout, responsáveis, node_notes.';

COMMIT;
