-- ==========================================================
-- Strategic Indicators
-- V001__create_strategic_indicators_schema_and_extensions.sql
-- Base estrutural do plugin no banco postgres-plugins
-- ==========================================================

BEGIN;

-- ==========================================================
-- EXTENSÕES NECESSÁRIAS
-- ==========================================================
-- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ==========================================================
-- SCHEMA DO PLUGIN
-- ==========================================================
CREATE SCHEMA IF NOT EXISTS strategic_indicators;

-- ==========================================================
-- DOCUMENTAÇÃO DO SCHEMA
-- ==========================================================
COMMENT ON SCHEMA strategic_indicators IS
'Schema do plugin Strategic Indicators dentro do postgres-plugins. Responsável por persistência administrativa, configurações, pesos, metas e parâmetros do módulo.';

COMMIT;