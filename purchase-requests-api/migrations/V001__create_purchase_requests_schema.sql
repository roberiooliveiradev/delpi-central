BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS purchase_requests;

COMMENT ON SCHEMA purchase_requests IS 'Painel de solicitações de compras — escopos CC e mappings Protheus.';

CREATE TABLE IF NOT EXISTS purchase_requests.schema_migrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS purchase_requests.visibility_scopes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by_user_id TEXT,
    updated_by_user_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_purchase_requests_visibility_scopes_active
    ON purchase_requests.visibility_scopes (active);

CREATE TABLE IF NOT EXISTS purchase_requests.visibility_scope_users (
    scope_id UUID NOT NULL
        REFERENCES purchase_requests.visibility_scopes (id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (scope_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_purchase_requests_visibility_scope_users_user
    ON purchase_requests.visibility_scope_users (user_id);

CREATE TABLE IF NOT EXISTS purchase_requests.visibility_scope_cost_centers (
    scope_id UUID NOT NULL
        REFERENCES purchase_requests.visibility_scopes (id) ON DELETE CASCADE,
    branch CHAR(2) NOT NULL CHECK (branch IN ('01', '02')),
    cost_center_code TEXT NOT NULL CHECK (length(trim(cost_center_code)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (scope_id, branch, cost_center_code)
);

CREATE INDEX IF NOT EXISTS idx_purchase_requests_visibility_scope_cc_branch
    ON purchase_requests.visibility_scope_cost_centers (branch, cost_center_code);

CREATE TABLE IF NOT EXISTS purchase_requests.user_protheus_mappings (
    user_id TEXT PRIMARY KEY,
    protheus_user_id TEXT,
    protheus_user_code TEXT,
    mapping_status TEXT NOT NULL DEFAULT 'unmapped'
        CHECK (mapping_status IN ('mapped', 'unmapped', 'ambiguous')),
    mapping_source TEXT
        CHECK (mapping_source IS NULL OR mapping_source IN ('manual', 'email_match', 'login_match')),
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_purchase_requests_user_protheus_mappings_protheus_user
    ON purchase_requests.user_protheus_mappings (protheus_user_id)
    WHERE protheus_user_id IS NOT NULL AND mapping_status = 'mapped';

COMMIT;
