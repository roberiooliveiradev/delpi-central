-- Transformômetro — escopo híbrido de recursos compartilhados (Playbook 18 S5)
BEGIN;

ALTER TABLE transformometro.recursos_compartilhados
    ADD COLUMN IF NOT EXISTS escopo_recurso VARCHAR(32) NOT NULL DEFAULT 'empresa';

COMMIT;
