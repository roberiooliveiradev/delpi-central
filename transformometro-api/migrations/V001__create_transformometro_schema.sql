-- Transformômetro — schema base no postgres-plugins
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS transformometro;

COMMENT ON SCHEMA transformometro IS
'Schema do plugin Transformômetro: processos, revisões, medições, investimentos, recursos compartilhados e dashboard derivado.';

COMMIT;
