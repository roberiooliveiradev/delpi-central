BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS maintenance;

COMMENT ON SCHEMA maintenance IS 'Manutenção industrial — mini-aplicadores e extensões futuras.';

COMMIT;
