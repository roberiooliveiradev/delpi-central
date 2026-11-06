-- ============================================================================
-- ENGINEERING.PRC.C1 — Principal PostgreSQL dedicado para Product Registration
-- Alvo: plugins_hub (delpi-postgres-plugins), schema engineering.
--
-- Uso (operador/DBA — senha NUNCA em arquivo versionado):
--   psql -d plugins_hub \
--     -v eng_prc_password='<senha-gerada-no-servidor>' \
--     -f eng_prc_grants.sql
--
-- Idempotente. Grants mínimos — somente tabelas product_registration_*;
-- sem privilégio sobre o database, outros schemas ou outras tabelas.
-- ============================================================================

\set ON_ERROR_STOP on

BEGIN;

SET app.prc_role_password = :'eng_prc_password';

DO $$
DECLARE
    role_password text := current_setting('app.prc_role_password');
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eng_prc') THEN
        EXECUTE format('CREATE ROLE eng_prc LOGIN PASSWORD %L', role_password);
    ELSE
        EXECUTE format('ALTER ROLE eng_prc WITH LOGIN PASSWORD %L', role_password);
    END IF;
END $$;

RESET app.prc_role_password;

GRANT USAGE ON SCHEMA engineering TO eng_prc;

-- Requests/drafts: CRUD operacional (CAS via row_version em UPDATE).
GRANT SELECT, INSERT, UPDATE
    ON engineering.product_registration_requests TO eng_prc;
GRANT SELECT, INSERT, UPDATE
    ON engineering.product_registration_drafts TO eng_prc;

-- Records: SELECT/INSERT/UPDATE — ponteiro de revisão vigente é atualizado
-- somente na conclusão verificada (mesma transação).
GRANT SELECT, INSERT, UPDATE
    ON engineering.product_registration_records TO eng_prc;

-- Revisões/eventos/verificações/idempotência: append-only (sem UPDATE/DELETE).
GRANT SELECT, INSERT
    ON engineering.product_registration_revisions TO eng_prc;
GRANT SELECT, INSERT
    ON engineering.product_registration_events TO eng_prc;
GRANT SELECT, INSERT
    ON engineering.product_registration_verifications TO eng_prc;
GRANT SELECT, INSERT
    ON engineering.product_registration_idempotency TO eng_prc;

REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES
    ON engineering.product_registration_revisions FROM eng_prc;
REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES
    ON engineering.product_registration_events FROM eng_prc;
REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES
    ON engineering.product_registration_verifications FROM eng_prc;
REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
    ON engineering.product_registration_idempotency FROM eng_prc;
REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
    ON engineering.product_registration_requests FROM eng_prc;
REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
    ON engineering.product_registration_drafts FROM eng_prc;
REVOKE DELETE, TRUNCATE, TRIGGER, REFERENCES
    ON engineering.product_registration_records FROM eng_prc;

COMMIT;

-- Pós-condições esperadas (validação manual):
--   eng_prc faz SELECT/INSERT/UPDATE em requests/drafts/records;
--   eng_prc faz SELECT/INSERT (sem UPDATE/DELETE) em revisions/events/
--   verifications/idempotency; nenhum acesso a outros schemas/tabelas
--   (lmp_*, metallographic_*, quality, etc.).
