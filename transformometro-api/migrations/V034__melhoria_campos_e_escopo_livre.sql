-- Transformômetro — melhorias: campos de implantação + múltiplas por unidade/dept (jul/2026)
BEGIN;

ALTER TABLE transformometro.processo_instancias
    ADD COLUMN IF NOT EXISTS resumo_melhoria TEXT,
    ADD COLUMN IF NOT EXISTS responsavel_local VARCHAR(255),
    ADD COLUMN IF NOT EXISTS fase_melhoria VARCHAR(32) NOT NULL DEFAULT 'planejado',
    ADD COLUMN IF NOT EXISTS data_alvo_go_live DATE,
    ADD COLUMN IF NOT EXISTS prioridade VARCHAR(16) NOT NULL DEFAULT 'media';

COMMENT ON COLUMN transformometro.processo_instancias.resumo_melhoria IS
    'Resumo da oportunidade ou foco desta melhoria no processo.';
COMMENT ON COLUMN transformometro.processo_instancias.responsavel_local IS
    'Gestor ou patrocinador local da melhoria.';
COMMENT ON COLUMN transformometro.processo_instancias.fase_melhoria IS
    'Fase de rollout: planejado, piloto, implantado, encerrado.';
COMMENT ON COLUMN transformometro.processo_instancias.data_alvo_go_live IS
    'Data-alvo de go-live (planejamento).';
COMMENT ON COLUMN transformometro.processo_instancias.prioridade IS
    'Prioridade operacional: baixa, media, alta.';

DROP INDEX IF EXISTS transformometro.uq_processo_instancias_processo_filial;
DROP INDEX IF EXISTS transformometro.uq_processo_instancias_processo_todas_filiais;

CREATE INDEX IF NOT EXISTS idx_processo_instancias_processo_filial
    ON transformometro.processo_instancias (processo_id, filial_id)
    WHERE deletado = FALSE AND filial_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_processo_instancias_processo_todas_filiais
    ON transformometro.processo_instancias (processo_id)
    WHERE deletado = FALSE AND todas_filiais_ativas = TRUE;

COMMIT;
