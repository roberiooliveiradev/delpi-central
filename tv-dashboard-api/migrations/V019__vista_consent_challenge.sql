-- V019 — VISTA consent challenge (SEMANTIC_TOOLS_V1, D-5).
--
-- Human consent is a first-class authorization object emitted by the
-- backend at PREPARE and verifiably bound to: actor (actor_sub),
-- proposal (proposal_id), sealed plan (plan_hash), target identity
-- (target_ref), action, expiry, origin channel and single-use state
-- (PENDING → APPROVED → CONSUMED | EXPIRED | REVOKED).
--
-- Pattern reused from CLARA step-up consent (controllership_finance
-- V014) — adapted to the VISTA bounded context: proposals live in the
-- governed proposal store, so proposal_id is TEXT (no FK); plan
-- integrity is enforced via plan_hash = proposal.content_hash.
-- The approval channel records token_iat so a JWT minted before the
-- challenge cannot authorize it (iat >= created_at). Non-destructive.

BEGIN;

CREATE TABLE IF NOT EXISTS tv_dashboard.vista_consent_challenge (
    challenge_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id        TEXT NOT NULL,
    actor_sub          TEXT NOT NULL,
    plan_hash          TEXT NOT NULL,
    target_ref         TEXT NOT NULL,
    action             TEXT NOT NULL,
    status             TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN (
            'PENDING', 'APPROVED', 'CONSUMED', 'EXPIRED', 'REVOKED'
        )),
    origin             TEXT NOT NULL
        CHECK (origin IN ('gpt_actions', 'mcp', 'portal')),
    correlation_id     TEXT,
    approved_by        TEXT,
    approved_token_jti TEXT,
    approved_token_iat TIMESTAMPTZ,
    consent_record     JSONB,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_at        TIMESTAMPTZ,
    consumed_at        TIMESTAMPTZ,
    expires_at         TIMESTAMPTZ NOT NULL
);

-- One pending challenge per proposal: re-issue returns the existing row.
CREATE UNIQUE INDEX IF NOT EXISTS vista_consent_challenge_pending_idx
    ON tv_dashboard.vista_consent_challenge (proposal_id)
    WHERE status = 'PENDING';

CREATE INDEX IF NOT EXISTS vista_consent_challenge_proposal_idx
    ON tv_dashboard.vista_consent_challenge (proposal_id, created_at DESC);

CREATE INDEX IF NOT EXISTS vista_consent_challenge_actor_idx
    ON tv_dashboard.vista_consent_challenge (actor_sub, created_at DESC);

COMMIT;
