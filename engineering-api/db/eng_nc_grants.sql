-- ============================================================================
-- ENGINEERING.NC.T7 — Principal PostgreSQL dedicado para Não Conformidades
-- Alvo: plugins_hub (delpi-postgres-plugins), schema engineering.
--
-- Uso (operador/DBA — senha NUNCA em arquivo versionado):
--   psql -d plugins_hub \
--     -v eng_nc_password='<senha-gerada-no-servidor>' \
--     -f eng_nc_grants.sql
--
-- Idempotente: reaplicar é seguro (CREATE OR REPLACE / GRANT idempotentes).
-- Grants mínimos — somente tabelas do domínio NC; sem privilégio sobre o
-- database, outros schemas ou outras tabelas do schema engineering.
-- ============================================================================

\set ON_ERROR_STOP on

BEGIN;

-- 1) Role dedicada (login próprio do bounded context NC).
--    A senha chega via variável psql e é transportada pela GUC de sessão
--    (interpolação :'var' não funciona dentro de blocos DO).
SET app.nc_role_password = :'eng_nc_password';

DO $$
DECLARE
    role_password text := current_setting('app.nc_role_password');
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'eng_nc') THEN
        EXECUTE format('CREATE ROLE eng_nc LOGIN PASSWORD %L', role_password);
    ELSE
        EXECUTE format('ALTER ROLE eng_nc WITH LOGIN PASSWORD %L', role_password);
    END IF;
END $$;

RESET app.nc_role_password;

-- 2) Uso do schema — sem CREATE (schema e objetos pertencem ao owner/migrations).
GRANT USAGE ON SCHEMA engineering TO eng_nc;

-- 3) Grants mínimos por tabela.
--    NC principal: CRUD completo (create/update/delete operacionais).
GRANT SELECT, INSERT, UPDATE, DELETE
    ON engineering.lmp_nonconformities TO eng_nc;

--    Histórico append-only: INSERT via writes da NC pai; DELETE somente em
--    cascata da exclusão da NC pai, protegida pela trigger V008 +
--    app.allow_lmp_nc_history_delete (GUC escopo transação).
GRANT SELECT, INSERT, DELETE
    ON engineering.lmp_nonconformity_history TO eng_nc;

--    Produtos vinculados: substituição transacional por update (delete+insert).
GRANT SELECT, INSERT, DELETE
    ON engineering.lmp_nonconformity_products TO eng_nc;

--    Vínculo NC ↔ tag: idem.
GRANT SELECT, INSERT, DELETE
    ON engineering.lmp_nonconformity_problem_tags TO eng_nc;

--    Catálogo de tags: auto-catálogo em write (select+insert); sem update/delete.
GRANT SELECT, INSERT
    ON engineering.lmp_problem_tags TO eng_nc;

-- 4) Função da trigger append-only (SECURITY INVOKER padrão — precisa EXECUTE).
GRANT EXECUTE
    ON FUNCTION engineering.prevent_lmp_nc_history_mutation() TO eng_nc;

-- 5) Revogações explícitas de hardening — garante que nenhum privilégio a
--    mais persista de aplicações anteriores do script.
REVOKE TRUNCATE, TRIGGER, REFERENCES
    ON engineering.lmp_nonconformities FROM eng_nc;
REVOKE TRUNCATE, TRIGGER, REFERENCES
    ON engineering.lmp_nonconformity_history FROM eng_nc;
REVOKE TRUNCATE, TRIGGER, REFERENCES
    ON engineering.lmp_nonconformity_products FROM eng_nc;
REVOKE TRUNCATE, TRIGGER, REFERENCES
    ON engineering.lmp_nonconformity_problem_tags FROM eng_nc;
REVOKE UPDATE, DELETE, TRUNCATE, TRIGGER, REFERENCES
    ON engineering.lmp_problem_tags FROM eng_nc;

COMMIT;

-- Pós-condições esperadas (validação manual):
--   eng_nc consegue SELECT/INSERT/UPDATE/DELETE nas 4 tabelas NC;
--   eng_nc consegue SELECT/INSERT no catálogo de tags e INSERT no histórico;
--   eng_nc NÃO consegue: TRUNCATE, DDL, acesso a outros schemas
--   (quality, planejamento_orcamentario, etc.) ou a
--   engineering.metallographic_* (outro domínio).
