BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS my_requests;

COMMENT ON SCHEMA my_requests IS 'Minhas Solicitações — Request Engine transversal.';

CREATE TABLE IF NOT EXISTS my_requests.schema_migrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMIT;
