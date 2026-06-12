-- Transformômetro — revisão única por instância × versão (Playbook 18 S8)
BEGIN;

ALTER TABLE transformometro.revisoes
    DROP CONSTRAINT IF EXISTS uq_revisoes_processo_versao;

UPDATE transformometro.revisoes r
SET chave_unica_processo_revisao = pi.instancia_id::text || '|' || r.versao_revisao
FROM transformometro.processo_instancias pi
WHERE r.instancia_id = pi.instancia_id
  AND r.chave_unica_processo_revisao IS DISTINCT FROM (pi.instancia_id::text || '|' || r.versao_revisao);

ALTER TABLE transformometro.revisoes
    ADD CONSTRAINT uq_revisoes_instancia_versao UNIQUE (instancia_id, versao_revisao);

COMMENT ON CONSTRAINT uq_revisoes_instancia_versao ON transformometro.revisoes IS
'Cada instância operacional possui timeline própria de versões.';

COMMIT;
