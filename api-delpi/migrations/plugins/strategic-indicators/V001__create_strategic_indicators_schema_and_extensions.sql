-- ==========================================================
-- Strategic Indicators
-- V001__create_strategic_indicators_schema_and_extensions.sql
-- Base estrutural do plugin no banco postgres-plugins
-- ==========================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS strategic_indicators;

COMMENT ON SCHEMA strategic_indicators IS
'Schema do plugin Strategic Indicators dentro do postgres-plugins. Responsável por persistência administrativa, catálogo estrutural, metas analíticas versionadas, auditoria e workflows administrativos do módulo.';

COMMIT;