BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS supplies;

COMMENT ON SCHEMA supplies IS 'Portal Suprimentos — estado Minha DELPI (não espelho TOTVS).';

CREATE TABLE IF NOT EXISTS supplies.schema_migrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS supplies.supply_user_preferences (
    user_id UUID PRIMARY KEY,
    keycloak_sub TEXT,
    default_branch TEXT,
    table_density TEXT NOT NULL DEFAULT 'comfortable'
        CHECK (table_density IN ('comfortable', 'compact')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_supply_user_preferences_keycloak_sub
    ON supplies.supply_user_preferences (keycloak_sub)
    WHERE keycloak_sub IS NOT NULL;

COMMIT;
