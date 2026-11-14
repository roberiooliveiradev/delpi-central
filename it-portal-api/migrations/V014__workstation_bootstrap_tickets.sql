-- G2-S4-S2b-P1: inert ticket ledger for future HML-only enrollment.
-- No endpoint, Keycloak activation, client secret, S2S grant or remote control.
CREATE TABLE it_portal.workstation_bootstrap_tickets (
    id UUID PRIMARY KEY,
    workstation_id UUID NOT NULL REFERENCES it_portal.workstation_agent_identities(workstation_id) ON DELETE RESTRICT,
    token_digest CHAR(64) NOT NULL UNIQUE,
    issued_by_id UUID NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    state VARCHAR(12) NOT NULL DEFAULT 'pending',
    closed_at TIMESTAMPTZ,
    CONSTRAINT workstation_bootstrap_tickets_digest_chk CHECK (token_digest ~ '^[0-9a-f]{64}$'),
    CONSTRAINT workstation_bootstrap_tickets_ttl_chk CHECK (
        expires_at >= issued_at + INTERVAL '60 seconds'
        AND expires_at <= issued_at + INTERVAL '600 seconds'
    ),
    CONSTRAINT workstation_bootstrap_tickets_state_chk CHECK (state IN ('pending', 'consumed', 'cancelled', 'expired')),
    CONSTRAINT workstation_bootstrap_tickets_closed_chk CHECK (
        (state = 'pending' AND closed_at IS NULL) OR
        (state <> 'pending' AND closed_at IS NOT NULL)
    )
);
-- Stale pending rows must be expired transactionally before a new ticket is issued.
CREATE UNIQUE INDEX workstation_bootstrap_one_pending_idx
    ON it_portal.workstation_bootstrap_tickets(workstation_id)
    WHERE state = 'pending';
CREATE INDEX workstation_bootstrap_tickets_by_expiry_idx
    ON it_portal.workstation_bootstrap_tickets(state, expires_at);

CREATE TABLE it_portal.workstation_bootstrap_ticket_events (
    id UUID PRIMARY KEY,
    ticket_id UUID NOT NULL REFERENCES it_portal.workstation_bootstrap_tickets(id) ON DELETE RESTRICT,
    event_type VARCHAR(12) NOT NULL,
    actor_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT workstation_bootstrap_ticket_event_type_chk CHECK (
        event_type IN ('issued', 'consumed', 'cancelled', 'expired')
    )
);
CREATE INDEX workstation_bootstrap_ticket_events_by_ticket_idx
    ON it_portal.workstation_bootstrap_ticket_events(ticket_id, created_at);
COMMENT ON TABLE it_portal.workstation_bootstrap_tickets IS
    'INERT G2-S4-S2b-P1: SHA-256 digest of high-entropy one-time ticket only; consumption never grants Keycloak/S2S/remote access. No route.';
