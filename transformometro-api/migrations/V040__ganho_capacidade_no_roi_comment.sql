-- Playbook 22 — capacidade entra no ROI (atualiza comentário de coluna)
BEGIN;

COMMENT ON COLUMN transformometro.dashboard_calculos.ganho_capacidade IS
  'Benefício de capacidade (vol_rev > vol_ref); soma em economia_bruta e entra no ROI.';

COMMIT;
