BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS comite_etica;

COMMENT ON SCHEMA comite_etica IS 'CEC — atas, assinaturas e extensões futuras.';

COMMIT;
