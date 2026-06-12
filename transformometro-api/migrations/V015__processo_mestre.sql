-- Transformômetro — processo mestre: remove filial_id/setor_id string de processos
-- Localização operacional fica em processo_instancias (Playbook 18 S4).
BEGIN;

DROP VIEW IF EXISTS transformometro.processo_competencia_snapshot;

ALTER TABLE transformometro.processos DROP COLUMN IF EXISTS filial_id;
ALTER TABLE transformometro.processos DROP COLUMN IF EXISTS setor_id;

DROP INDEX IF EXISTS transformometro.idx_processos_filial;
DROP INDEX IF EXISTS transformometro.idx_processos_setor;

COMMIT;
