-- Playbook 22 — default e backfill de beneficio_calculo_categoria → automatico
-- Não altera V039/V040 (imutáveis). Linhas com categoria explícita distinta de
-- economia_tempo (legado/default anterior) são preservadas.

BEGIN;

ALTER TABLE transformometro.revisoes
  ALTER COLUMN beneficio_calculo_categoria SET DEFAULT 'automatico';

ALTER TABLE transformometro.dashboard_calculos
  ALTER COLUMN beneficio_calculo_categoria SET DEFAULT 'automatico';

UPDATE transformometro.revisoes
SET beneficio_calculo_categoria = 'automatico'
WHERE beneficio_calculo_categoria = 'economia_tempo';

UPDATE transformometro.dashboard_calculos
SET beneficio_calculo_categoria = 'automatico'
WHERE beneficio_calculo_categoria = 'economia_tempo';

COMMENT ON COLUMN transformometro.revisoes.beneficio_calculo_categoria IS
  'Categoria de interpretação do benefício vs. referência. Default automatico (não classificado); economia_tempo permanece opção explícita.';

COMMIT;
