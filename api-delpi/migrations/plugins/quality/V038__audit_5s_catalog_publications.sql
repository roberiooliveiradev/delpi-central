-- Histórico de publicações do catálogo de critérios 5S por filial.

CREATE TABLE IF NOT EXISTS quality.audit_5s_catalog_publications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_code VARCHAR(2) NOT NULL,
    catalog_version INTEGER NOT NULL,
    published_by_user_id UUID,
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    criteria_count SMALLINT NOT NULL,
    notes TEXT NULL,

    CONSTRAINT ck_audit_5s_catalog_pub_branch CHECK (branch_code IN ('01', '02')),
    CONSTRAINT ck_audit_5s_catalog_pub_version CHECK (catalog_version >= 1),
    CONSTRAINT ck_audit_5s_catalog_pub_count CHECK (criteria_count >= 1),
    CONSTRAINT uq_audit_5s_catalog_pub_branch_version UNIQUE (branch_code, catalog_version)
);

CREATE INDEX IF NOT EXISTS idx_audit_5s_catalog_pub_branch_published
    ON quality.audit_5s_catalog_publications (branch_code, published_at DESC);
