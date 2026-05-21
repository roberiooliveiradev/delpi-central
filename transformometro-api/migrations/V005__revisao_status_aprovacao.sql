-- Workflow de aprovação de revisões (Fase 4+)
BEGIN;

ALTER TABLE transformometro.revisoes
    ADD COLUMN IF NOT EXISTS status_aprovacao VARCHAR(32) NOT NULL DEFAULT 'aprovada',
    ADD COLUMN IF NOT EXISTS aprovado_em TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS aprovado_por_email VARCHAR(255),
    ADD COLUMN IF NOT EXISTS motivo_rejeicao TEXT;

COMMENT ON COLUMN transformometro.revisoes.status_aprovacao IS
    'rascunho | em_analise | aprovada | rejeitada';

CREATE INDEX IF NOT EXISTS idx_revisoes_status_aprovacao
    ON transformometro.revisoes (status_aprovacao)
    WHERE deletado = FALSE;

COMMIT;
