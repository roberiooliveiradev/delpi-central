-- ================================================================
-- SUPPLIES-ENRICHMENT-01 / S2
-- Reviews, field proposals, decisions and audit events for the
-- assisted supplier cadastral enrichment flow.
--
-- Scope rules enforced by this schema:
--   - actor ownership (resource scope) via actor_subject
--   - optimistic concurrency via reviews.revision
--   - idempotent decisions via UNIQUE(review_id, idempotency_key)
--   - append-only audit events
--   - tax_id is NEVER stored in proposals (protected identity field)
--   - no external provider payloads, tokens or SA2 mirroring
-- ================================================================

CREATE TABLE supplies.supplier_enrichment_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    supplier_code VARCHAR(6) NOT NULL,
    supplier_store VARCHAR(2) NOT NULL,
    unit_context VARCHAR(2),
    actor_subject UUID NOT NULL,
    source_id VARCHAR(64),
    source_reference VARCHAR(255),
    source_retrieved_at TIMESTAMPTZ,
    mapping_version VARCHAR(32) NOT NULL,
    normalization_version VARCHAR(32) NOT NULL,
    baseline_reference VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'IN_REVIEW'
        CHECK (status IN ('IN_REVIEW', 'DECIDED', 'EXPIRED', 'CANCELLED', 'STALE')),
    revision INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE supplies.supplier_enrichment_proposals (
    proposal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL
        REFERENCES supplies.supplier_enrichment_reviews (review_id) ON DELETE RESTRICT,
    field_key VARCHAR(64) NOT NULL,
    section_key VARCHAR(32) NOT NULL,
    comparison_state VARCHAR(24) NOT NULL,
    eligibility_state VARCHAR(40) NOT NULL,
    eligibility_reason VARCHAR(64),
    source_field VARCHAR(128),
    source_reference VARCHAR(255),
    current_value TEXT,
    suggested_value TEXT,
    decision_state VARCHAR(24) NOT NULL DEFAULT 'PENDING'
        CHECK (decision_state IN (
            'PENDING', 'ACCEPTED_FOR_DRAFT', 'REJECTED_SUGGESTION'
        )),
    UNIQUE (review_id, field_key)
);

CREATE TABLE supplies.supplier_enrichment_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL
        REFERENCES supplies.supplier_enrichment_reviews (review_id) ON DELETE RESTRICT,
    proposal_id UUID NOT NULL
        REFERENCES supplies.supplier_enrichment_proposals (proposal_id) ON DELETE RESTRICT,
    actor_subject UUID NOT NULL,
    decision VARCHAR(8) NOT NULL CHECK (decision IN ('ACCEPT', 'REJECT')),
    reason_code VARCHAR(64),
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    review_revision INTEGER NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    request_hash VARCHAR(64) NOT NULL,
    UNIQUE (review_id, idempotency_key)
);

CREATE TABLE supplies.supplier_enrichment_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL
        REFERENCES supplies.supplier_enrichment_reviews (review_id) ON DELETE RESTRICT,
    actor_subject UUID,
    event_type VARCHAR(48) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_enrichment_reviews_supplier
    ON supplies.supplier_enrichment_reviews (supplier_code, supplier_store, created_at DESC);

CREATE INDEX idx_enrichment_reviews_actor
    ON supplies.supplier_enrichment_reviews (actor_subject, created_at DESC);

CREATE INDEX idx_enrichment_reviews_expiry
    ON supplies.supplier_enrichment_reviews (status, expires_at);

CREATE INDEX idx_enrichment_proposals_review
    ON supplies.supplier_enrichment_proposals (review_id);

CREATE INDEX idx_enrichment_decisions_review
    ON supplies.supplier_enrichment_decisions (review_id, decided_at);

CREATE INDEX idx_enrichment_events_review
    ON supplies.supplier_enrichment_events (review_id, created_at);
