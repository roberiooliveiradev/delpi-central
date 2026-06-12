BEGIN;

ALTER TABLE maintenance.motivos
    ADD COLUMN IF NOT EXISTS excluir_preventiva BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN maintenance.motivos.excluir_preventiva IS
    'Quando TRUE, reposições com este motivo não entram no cálculo preventivo.';

COMMIT;
