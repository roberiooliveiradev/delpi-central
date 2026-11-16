-- ATLAS P2.2h.2b. REVIEW/CI ONLY, NOT A VERSIONED PRODUCTION MIGRATION.
-- Apply ONLY after 05-atlas-p22d-candidate-schema.sql in a fresh, disposable
-- PostgreSQL test database. Do NOT run on HML or PROD.
-- No endpoint, grant, migration runner, approval or ACT is enabled.
-- The Portal TI/PostgreSQL owners must review schema, grants and triggers.
CREATE TABLE it_portal.atlas_deploy_oci_bindings (
  proposal_id uuid PRIMARY KEY
    REFERENCES it_portal.atlas_deploy_proposals(id) ON DELETE RESTRICT,
  requester_subject uuid NOT NULL,
  request_id uuid NOT NULL,
  environment varchar(4) NOT NULL
    CHECK (environment IN ('prod','hml')),
  service_id varchar(64) NOT NULL
    CHECK (service_id = 'public-hub'),
  target_sha char(40) NOT NULL CHECK (target_sha ~ '^[0-9a-f]{40}$'),
  base_sha char(40) NOT NULL CHECK (base_sha ~ '^[0-9a-f]{40}$'),
  signed_manifest_digest varchar(71) NOT NULL
    CHECK (signed_manifest_digest ~ '^sha256:[0-9a-f]{64}$'),
  release_image_id varchar(71) NOT NULL
    CHECK (release_image_id ~ '^sha256:[0-9a-f]{64}$'),
  base_image_id varchar(71) NOT NULL
    CHECK (base_image_id ~ '^sha256:[0-9a-f]{64}$'),
  rollback_image_id varchar(71) NOT NULL
    CHECK (rollback_image_id = base_image_id),
  ci_statement_sha256 char(64) NOT NULL
    CHECK (ci_statement_sha256 ~ '^[0-9a-f]{64}$'),
  host_challenge_sha256 char(64) NOT NULL
    CHECK (host_challenge_sha256 ~ '^[0-9a-f]{64}$'),
  preview_hash char(64) NOT NULL
    CHECK (preview_hash ~ '^[0-9a-f]{64}$'),
  sealed_binding_sha256 char(64) NOT NULL
    CHECK (sealed_binding_sha256 ~ '^[0-9a-f]{64}$'),
  issued_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  CONSTRAINT atlas_oci_different_image_ids CHECK (release_image_id <> base_image_id),
  CONSTRAINT atlas_oci_rollback_identical CHECK (rollback_image_id = base_image_id),
  CONSTRAINT atlas_oci_ttl CHECK (
    expires_at > issued_at AND expires_at <= issued_at + interval '10 minutes'
  )
);

-- Prevent a binding with mismatching owner, request or generic proposal hash.
-- PostgreSQL locks the parent row inside the same transaction as the INSERT.
CREATE FUNCTION it_portal.atlas_oci_guard_binding()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p it_portal.atlas_deploy_proposals%ROWTYPE;
BEGIN
  IF TG_OP <> 'INSERT' THEN
    RAISE EXCEPTION 'immutable OCI binding' USING ERRCODE = '23514';
  END IF;
  SELECT * INTO p FROM it_portal.atlas_deploy_proposals
    WHERE id = NEW.proposal_id FOR UPDATE;
  IF NOT FOUND
    OR p.requester_subject <> NEW.requester_subject
    OR p.request_id <> NEW.request_id
    OR p.environment <> NEW.environment
    OR p.service_id <> NEW.service_id
    OR p.target_sha <> NEW.target_sha
    OR p.base_sha <> NEW.base_sha
    OR p.proposal_hash <> NEW.sealed_binding_sha256
    OR p.created_at <> NEW.issued_at
    OR p.expires_at <> NEW.expires_at
    OR p.status <> 'pending_approval'
  THEN
    RAISE EXCEPTION 'OCI proposal/binding mismatch' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER atlas_oci_binding_immutable
BEFORE INSERT OR UPDATE OR DELETE ON it_portal.atlas_deploy_oci_bindings
FOR EACH ROW EXECUTE FUNCTION it_portal.atlas_oci_guard_binding();

-- Guard high-value parent identity fields and refuse approval/execution for
-- public-hub without a matching immutable binding. This is NOT approval logic:
-- the future backend still needs Core/RBAC, signature, quorum and fresh host.
CREATE FUNCTION it_portal.atlas_oci_guard_proposal_update()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.service_id <> 'public-hub' AND NEW.service_id <> 'public-hub' THEN
    RETURN NEW;
  END IF;
  IF OLD.requester_subject IS DISTINCT FROM NEW.requester_subject
    OR OLD.request_id IS DISTINCT FROM NEW.request_id
    OR OLD.environment IS DISTINCT FROM NEW.environment
    OR OLD.service_id IS DISTINCT FROM NEW.service_id
    OR OLD.target_sha IS DISTINCT FROM NEW.target_sha
    OR OLD.base_sha IS DISTINCT FROM NEW.base_sha
    OR OLD.proposal_hash IS DISTINCT FROM NEW.proposal_hash
    OR OLD.challenge_digest IS DISTINCT FROM NEW.challenge_digest
    OR OLD.created_at IS DISTINCT FROM NEW.created_at
    OR OLD.expires_at IS DISTINCT FROM NEW.expires_at
  THEN
    RAISE EXCEPTION 'OCI proposal identity is immutable' USING ERRCODE = '23514';
  END IF;
  IF NEW.status IN ('approved', 'executing', 'verified')
    AND NOT EXISTS (
      SELECT 1 FROM it_portal.atlas_deploy_oci_bindings b
      WHERE b.proposal_id = NEW.id
        AND b.sealed_binding_sha256 = NEW.proposal_hash
    )
  THEN
    RAISE EXCEPTION 'OCI binding required for state transition'
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER atlas_oci_proposal_identity_guard
BEFORE UPDATE ON it_portal.atlas_deploy_proposals
FOR EACH ROW EXECUTE FUNCTION it_portal.atlas_oci_guard_proposal_update();

-- Future owner must enforce role grants, row ownership, rejection/revocation
-- audit, approval concurrency and immutability after approval; do not grant
-- this candidate schema to public, MCP, ChatGPT or a deployment executor.
