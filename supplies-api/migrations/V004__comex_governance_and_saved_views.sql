-- ================================================================
-- PROC-0076.COMEX.S2/S3 — Configurable Comex analysis
-- NCM homologation governance (Portal workflow state + append-only
-- audit) and personal saved market views.
--
-- Ownership rules enforced by this schema:
--   - governance state lives here; the operational allowlist stays in
--     external_data.comex_ncm_allowlist and is synced via the
--     external-data-api S2S write — no cross-schema writes.
--   - one governance row per NCM (UNIQUE ncm_code) — the full history
--     is in the events table.
--   - views are owned by owner_user_id; ownership is enforced
--     server-side in every read/write.
--   - product codes / NCM references are selection refs only — no
--     SB1010 mirror, no MDIC observation copy.
-- ================================================================

CREATE TABLE supplies.comex_ncm_governance (
    governance_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ncm_code        VARCHAR(8) NOT NULL UNIQUE
        CHECK (ncm_code ~ '^[0-9]{8}$'),
    ncm_version     VARCHAR(40),
    description     TEXT,
    family_code     VARCHAR(64),
    product_codes   JSONB NOT NULL DEFAULT '[]'::jsonb,
    status          VARCHAR(24) NOT NULL DEFAULT 'candidate'
        CHECK (status IN (
            'candidate', 'pending_fiscal_review', 'approved',
            'rejected', 'inactive'
        )),
    notes           TEXT,
    requested_by    UUID NOT NULL,
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    decided_by      UUID,
    decided_at      TIMESTAMPTZ,
    decision_notes  TEXT,
    deactivated_by  UUID,
    deactivated_at  TIMESTAMPTZ,
    revision        INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_comex_ncm_governance_status
    ON supplies.comex_ncm_governance (status, updated_at DESC);

CREATE TABLE supplies.comex_ncm_governance_events (
    event_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    governance_id UUID NOT NULL
        REFERENCES supplies.comex_ncm_governance (governance_id)
        ON DELETE RESTRICT,
    actor_subject UUID,
    event_type    VARCHAR(48) NOT NULL,
    from_status   VARCHAR(24),
    to_status     VARCHAR(24),
    notes         TEXT,
    metadata      JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_comex_ncm_governance_events_gov
    ON supplies.comex_ncm_governance_events (governance_id, created_at);

CREATE TABLE supplies.comex_market_views (
    view_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id            UUID NOT NULL,
    unit_scope               VARCHAR(2),
    name                     VARCHAR(120) NOT NULL,
    selected_product_codes   JSONB NOT NULL DEFAULT '[]'::jsonb,
    selected_materials       JSONB NOT NULL DEFAULT '[]'::jsonb,
    approved_ncm_references  JSONB NOT NULL DEFAULT '[]'::jsonb,
    selected_metrics         JSONB NOT NULL DEFAULT '[]'::jsonb,
    date_range               JSONB,
    granularity              VARCHAR(16) NOT NULL DEFAULT 'month'
        CHECK (granularity IN ('month', 'year')),
    view_mode                VARCHAR(16) NOT NULL DEFAULT 'chart'
        CHECK (view_mode IN ('chart', 'table')),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_comex_market_views_owner
    ON supplies.comex_market_views (owner_user_id, updated_at DESC);
