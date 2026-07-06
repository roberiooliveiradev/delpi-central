-- Revisão de referência para comparação (substitui baseline fixo em revisões cotidianas)
ALTER TABLE transformometro.revisoes
    ADD COLUMN IF NOT EXISTS revisao_referencia_id UUID NULL
        REFERENCES transformometro.revisoes (revisao_id);

CREATE INDEX IF NOT EXISTS idx_revisoes_referencia
    ON transformometro.revisoes (revisao_referencia_id)
    WHERE deletado = FALSE;

COMMENT ON COLUMN transformometro.revisoes.revisao_referencia_id IS
    'Revisão contra a qual esta revisão é comparada (economia, diff). NULL na baseline ou legado (auto-baseline).';

-- Revisões existentes (não baseline) passam a referenciar a baseline da mesma instância
UPDATE transformometro.revisoes AS r
SET revisao_referencia_id = baseline.revisao_id
FROM (
    SELECT DISTINCT ON (instancia_id)
        revisao_id,
        instancia_id
    FROM transformometro.revisoes
    WHERE deletado = FALSE
      AND lower(coalesce(cenario_tipo, '')) = 'baseline'
    ORDER BY instancia_id, data_inicio_vigencia ASC, versao_revisao ASC
) AS baseline
WHERE r.deletado = FALSE
  AND lower(coalesce(r.cenario_tipo, '')) <> 'baseline'
  AND r.revisao_referencia_id IS NULL
  AND r.instancia_id = baseline.instancia_id;
