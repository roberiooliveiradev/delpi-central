BEGIN;

ALTER TABLE transformometro.audit_logs
    ADD COLUMN IF NOT EXISTS user_name VARCHAR(255);

COMMENT ON COLUMN transformometro.audit_logs.user_name IS
    'Nome de exibição do usuário no momento da ação (JWT / core-api).';

COMMIT;
