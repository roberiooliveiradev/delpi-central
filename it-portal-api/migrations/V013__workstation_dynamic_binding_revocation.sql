-- G2-S4-S2a: dynamic binding fail-closed + revocation, no token or bootstrap material.
-- Applies after V012. No existing prepared identity is activated by this migration.
ALTER TABLE it_portal.workstation_agent_identities
    ADD COLUMN ingest_authorized BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN revocation_status VARCHAR(16) NOT NULL DEFAULT 'none',
    ADD COLUMN revoked_at TIMESTAMPTZ,
    ADD COLUMN revoked_by_id UUID;

ALTER TABLE it_portal.workstation_agent_identities
    ADD CONSTRAINT workstation_agent_revocation_status_chk
        CHECK (revocation_status IN ('none', 'pending', 'failed', 'confirmed')),
    ADD CONSTRAINT workstation_agent_ingest_enabled_chk
        CHECK (
            ingest_authorized = FALSE
            OR (state = 'prepared' AND revocation_status = 'none')
        ),
    ADD CONSTRAINT workstation_agent_confirmed_revocation_chk
        CHECK (revocation_status <> 'confirmed' OR state = 'revoked');

ALTER TABLE it_portal.workstation_agent_identity_events
    DROP CONSTRAINT workstation_agent_identity_event_chk;

ALTER TABLE it_portal.workstation_agent_identity_events
    ADD CONSTRAINT workstation_agent_identity_event_chk
        CHECK (event_type IN (
            'identity_reserved',
            'identity_prepared',
            'identity_prepare_failed',
            'identity_revocation_requested',
            'identity_revocation_failed',
            'identity_revoked'
        ));

COMMENT ON COLUMN it_portal.workstation_agent_identities.ingest_authorized IS
    'False by default. Dynamic S2S requests require this flag and a valid signed per-device Keycloak JWT; G2-S4-S2a provides no activation path.';
COMMENT ON COLUMN it_portal.workstation_agent_identities.revocation_status IS
    'Revocation is locally denied before Keycloak disable. pending/failed remain denied and require manual reconciliation.';
