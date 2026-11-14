-- G2-S4-S2b-P3. Inert signed challenge ledger, no automatic trust enrollment.
-- No route or Keycloak grant. Existing V014 tickets remain legacy/unbound.
CREATE TABLE it_portal.workstation_trusted_device_keys (
    id UUID PRIMARY KEY,
    workstation_id UUID NOT NULL REFERENCES it_portal.workstation_agent_identities(workstation_id) ON DELETE RESTRICT,
    public_key BYTEA NOT NULL,
    state VARCHAR(12) NOT NULL DEFAULT 'pending',
    approved_by_id UUID,
    approved_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT workstation_device_key_length_chk CHECK(octet_length(public_key) = 32),
    CONSTRAINT workstation_device_key_state_chk CHECK(state IN ('pending','trusted','revoked')),
    CONSTRAINT workstation_device_key_approval_chk CHECK (
      (state = 'pending' AND approved_by_id IS NULL AND approved_at IS NULL AND revoked_at IS NULL)
      OR (state = 'trusted' AND approved_by_id IS NOT NULL AND approved_at IS NOT NULL AND revoked_at IS NULL)
      OR (state = 'revoked' AND approved_by_id IS NOT NULL AND approved_at IS NOT NULL AND revoked_at IS NOT NULL)
    ),
    CONSTRAINT workstation_device_key_unique UNIQUE (id, workstation_id)
);
CREATE INDEX workstation_trusted_device_key_status_idx ON it_portal.workstation_trusted_device_keys(workstation_id, state);
ALTER TABLE it_portal.workstation_bootstrap_tickets
  ADD COLUMN trusted_key_id UUID,
  ADD COLUMN challenge_nonce VARCHAR(43),
  ADD COLUMN challenge_issued_at TIMESTAMPTZ,
  ADD COLUMN challenge_expires_at TIMESTAMPTZ,
  ADD CONSTRAINT workstation_signed_ticket_key_fk
      FOREIGN KEY (trusted_key_id, workstation_id)
      REFERENCES it_portal.workstation_trusted_device_keys(id, workstation_id),
  ADD CONSTRAINT workstation_signed_ticket_bundle_chk CHECK (
      (trusted_key_id IS NULL AND challenge_nonce IS NULL AND challenge_issued_at IS NULL AND challenge_expires_at IS NULL)
      OR (trusted_key_id IS NOT NULL AND challenge_nonce IS NOT NULL
          AND challenge_issued_at IS NOT NULL AND challenge_expires_at IS NOT NULL
          AND challenge_expires_at > challenge_issued_at
          AND challenge_expires_at <= expires_at
          AND challenge_expires_at <= challenge_issued_at + INTERVAL '600 seconds'
          AND challenge_nonce ~ '^[A-Za-z0-9_-]{43}$')
  );
COMMENT ON TABLE it_portal.workstation_trusted_device_keys IS
  'P3 inert key registry. No registration/approval route. DB migration alone creates no trusted key.';
COMMENT ON COLUMN it_portal.workstation_bootstrap_tickets.trusted_key_id IS
  'If non-null, legacy spend(token-only) MUST reject. Signed verification remains unexposed.';
