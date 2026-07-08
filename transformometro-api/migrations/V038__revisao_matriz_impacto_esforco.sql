-- Transformômetro — overrides matriz impacto×esforço por revisão (Playbook 21 S2)

BEGIN;

ALTER TABLE transformometro.revisoes
    ADD COLUMN IF NOT EXISTS matriz_impacto_esforco JSONB;

COMMENT ON COLUMN transformometro.revisoes.matriz_impacto_esforco IS
    'Overrides e inputs manuais da matriz impacto×esforço (schema revisao_matriz_impacto_esforco_v1). Scores auto são calculados; não persistir auto-only.';

COMMIT;
