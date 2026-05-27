BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.recurso_custos (
    recurso_custo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recurso_compartilhado_id UUID NOT NULL
        REFERENCES transformometro.recursos_compartilhados (recurso_compartilhado_id),
    valor_mensal NUMERIC(14, 2) NOT NULL,
    data_inicio_vigencia DATE NOT NULL,
    data_fim_vigencia DATE,
    observacoes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deletado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT chk_recurso_custo_vigencia
        CHECK (data_fim_vigencia IS NULL OR data_fim_vigencia >= data_inicio_vigencia)
);

CREATE INDEX IF NOT EXISTS idx_recurso_custos_recurso
    ON transformometro.recurso_custos (recurso_compartilhado_id)
    WHERE deletado = FALSE;

CREATE INDEX IF NOT EXISTS idx_recurso_custos_vigencia
    ON transformometro.recurso_custos (recurso_compartilhado_id, data_inicio_vigencia)
    WHERE deletado = FALSE;

-- Histórico inicial: um período por recurso com o valor e vigência já cadastrados
INSERT INTO transformometro.recurso_custos (
    recurso_compartilhado_id,
    valor_mensal,
    data_inicio_vigencia,
    data_fim_vigencia
)
SELECT
    r.recurso_compartilhado_id,
    r.valor_total_recorrente,
    COALESCE(r.data_inicio_vigencia, DATE '2000-01-01'),
    r.data_fim_vigencia
FROM transformometro.recursos_compartilhados r
WHERE r.deletado = FALSE
  AND NOT EXISTS (
      SELECT 1
      FROM transformometro.recurso_custos c
      WHERE c.recurso_compartilhado_id = r.recurso_compartilhado_id
        AND c.deletado = FALSE
  );

COMMIT;
