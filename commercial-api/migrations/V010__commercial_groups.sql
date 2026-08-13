-- Operational groups (M:N) — ≠ RBAC Keycloak and ≠ seller portfolios.
-- Seed four kinds with English ids and Portuguese display names.

CREATE TABLE IF NOT EXISTS commercial.commercial_groups (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kind        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order  INT NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_commercial_groups_active_sort
    ON commercial.commercial_groups (active, sort_order ASC, name ASC);

CREATE TABLE IF NOT EXISTS commercial.commercial_group_members (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id    UUID NOT NULL
        REFERENCES commercial.commercial_groups (id) ON DELETE CASCADE,
    user_id     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (group_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_commercial_group_members_user
    ON commercial.commercial_group_members (user_id);

CREATE INDEX IF NOT EXISTS idx_commercial_group_members_group
    ON commercial.commercial_group_members (group_id);

INSERT INTO commercial.commercial_groups (kind, name, sort_order)
VALUES
    ('sellers', 'Vendedores', 10),
    ('sales_assistants', 'Auxiliares de vendas', 20),
    ('billing', 'Faturamento', 30),
    ('estimators', 'Orçamentistas', 40)
ON CONFLICT (kind) DO NOTHING;
