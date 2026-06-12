BEGIN;

CREATE INDEX IF NOT EXISTS idx_audit_logs_filial_ferramenta_data
    ON maintenance.audit_logs (filial, entidade_id, data_criacao DESC)
    WHERE entidade = 'ferramenta';

COMMIT;
