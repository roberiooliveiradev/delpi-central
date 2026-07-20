-- Playbook 22 — categorias de cálculo de benefício (somente DDL)
-- Default economia_tempo: cadastros existentes herdam via DEFAULT da coluna (sem DML de backfill).

BEGIN;

ALTER TABLE transformometro.revisoes
  ADD COLUMN IF NOT EXISTS beneficio_calculo_categoria VARCHAR(32)
    NOT NULL DEFAULT 'economia_tempo';

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'chk_revisao_beneficio_calculo_categoria'
      AND conrelid = 'transformometro.revisoes'::regclass
  ) THEN
    ALTER TABLE transformometro.revisoes
      ADD CONSTRAINT chk_revisao_beneficio_calculo_categoria
      CHECK (
        beneficio_calculo_categoria IN (
          'economia_tempo',
          'reducao_volume',
          'ganho_capacidade',
          'economia_qualidade',
          'misto',
          'automatico'
        )
      );
  END IF;
END $$;

COMMENT ON COLUMN transformometro.revisoes.beneficio_calculo_categoria IS
  'Categoria de interpretação do benefício vs. referência. Default economia_tempo (legado).';

ALTER TABLE transformometro.dashboard_calculos
  ADD COLUMN IF NOT EXISTS beneficio_calculo_categoria VARCHAR(32)
    NOT NULL DEFAULT 'economia_tempo',
  ADD COLUMN IF NOT EXISTS ganho_capacidade NUMERIC(14, 2)
    NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS economia_reducao_volume NUMERIC(14, 2)
    NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS delta_volume NUMERIC(14, 4)
    NOT NULL DEFAULT 0;

COMMENT ON COLUMN transformometro.dashboard_calculos.ganho_capacidade IS
  'Benefício de capacidade (vol_rev > vol_ref); soma em economia_bruta e entra no ROI.';

COMMENT ON COLUMN transformometro.dashboard_calculos.economia_reducao_volume IS
  'Sinal informativo quando vol_rev < vol_ref (parcela analítica; sem double-count na bruta).';

COMMIT;
