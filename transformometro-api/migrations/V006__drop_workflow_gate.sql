-- Remove gate de aprovação: revisões podem ser ativadas direto (como planilha legado).
BEGIN;

UPDATE transformometro.revisoes
SET status_aprovacao = 'aprovada',
    motivo_rejeicao = NULL
WHERE deletado = FALSE
  AND status_aprovacao IN ('rascunho', 'em_analise', 'rejeitada');

ALTER TABLE transformometro.revisoes
    ALTER COLUMN status_aprovacao SET DEFAULT 'aprovada';

COMMENT ON COLUMN transformometro.revisoes.status_aprovacao IS
    'Legado V005 — mantido por compatibilidade; valor efetivo aprovada (sem workflow).';

COMMIT;
