BEGIN;

ALTER TABLE maintenance.audit_logs
    ADD COLUMN IF NOT EXISTS usuario_nome VARCHAR(200);

COMMENT ON COLUMN maintenance.audit_logs.usuario_nome IS
    'Nome de exibição do usuário autenticado no momento da mutação (JWT / RBAC).';

COMMIT;
