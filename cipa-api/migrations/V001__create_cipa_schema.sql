BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS cipa;

COMMENT ON SCHEMA cipa IS 'CIPA — atas, assinaturas e extensões futuras.';

COMMIT;
