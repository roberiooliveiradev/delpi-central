-- V016: ATLAS OCI journal. VERSIONED, BUT EXPLICITLY GATED.
-- Never apply on startup without IT_PORTAL_ATLAS_JOURNAL_SCHEMA_APPLY_ENABLED=true
-- set under owner-approved migration procedure, independently of ordinary
-- IT_PORTAL_RUN_MIGRATIONS_ON_STARTUP=true in the production Compose file.
-- This DDL changes only it_portal storage, not Core RBAC or deploy authority.
-- Prepared from reviewed draft schema 05 + OCI binding draft 12.
-- Before running in production: backup, DB owner review, least-privilege
-- reader role, checksums, rollback plan, CI PostgreSQL proof and approval.
-- No implicit permission grant for a Core user, MCP, ChatGPT or executor.

CREATE TABLE it_portal.atlas_deploy_challenges (
  id uuid PRIMARY KEY,
  requester_subject uuid NOT NULL,
  environment varchar(4) NOT NULL CHECK (environment IN ('hml','prod')),
  service_id varchar(64) NOT NULL CHECK (service_id ~ '^[a-z][a-z0-9-]{1,63}$'),
  challenge_digest char(64) NOT NULL UNIQUE
    CHECK (challenge_digest ~ '^[0-9a-f]{64}$'),
  issued_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  CONSTRAINT atlas_challenge_ttl CHECK (
    expires_at > issued_at AND expires_at <= issued_at + interval '90 seconds'
  ),
  CONSTRAINT atlas_challenge_consumed CHECK (
    consumed_at IS NULL OR consumed_at >= issued_at
  )
);
CREATE INDEX atlas_deploy_challenges_expiry_idx
  ON it_portal.atlas_deploy_challenges(expires_at)
  WHERE consumed_at IS NULL;

CREATE TABLE it_portal.atlas_deploy_proposals (
  id uuid PRIMARY KEY,
  requester_subject uuid NOT NULL,
  request_id uuid NOT NULL,
  environment varchar(4) NOT NULL CHECK (environment IN ('hml','prod')),
  service_id varchar(64) NOT NULL CHECK (service_id ~ '^[a-z][a-z0-9-]{1,63}$'),
  target_sha char(40) NOT NULL CHECK (target_sha ~ '^[0-9a-f]{40}$'),
  base_sha char(40) NOT NULL CHECK (base_sha ~ '^[0-9a-f]{40}$'),
  proposal_hash char(64) NOT NULL CHECK (proposal_hash ~ '^[0-9a-f]{64}$'),
  challenge_digest char(64) NOT NULL UNIQUE
    REFERENCES it_portal.atlas_deploy_challenges(challenge_digest) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL,
  expires_at timestamptz NOT NULL,
  status varchar(32) NOT NULL DEFAULT 'pending_approval',
  approved_by uuid,
  approved_at timestamptz,
  execution_id uuid UNIQUE,
  revision integer NOT NULL DEFAULT 1 CHECK (revision > 0),
  UNIQUE (requester_subject, request_id),
  CONSTRAINT atlas_proposal_sha_distinct CHECK (target_sha <> base_sha),
  CONSTRAINT atlas_proposal_ttl CHECK (
    expires_at > created_at AND expires_at <= created_at + interval '10 minutes'
  ),
  CONSTRAINT atlas_proposal_status CHECK (status IN (
    'pending_approval','approved','revoked','expired','executing',
    'verified','failed_needs_operator','rolled_back'
  )),
  CONSTRAINT atlas_proposal_approval_pair CHECK (
    (approved_by IS NULL AND approved_at IS NULL) OR
    (approved_by IS NOT NULL AND approved_at IS NOT NULL)
  )
);
CREATE UNIQUE INDEX atlas_one_executing_per_target_idx
  ON it_portal.atlas_deploy_proposals(environment,service_id)
  WHERE status = 'executing';
CREATE INDEX atlas_proposal_pending_idx
  ON it_portal.atlas_deploy_proposals(requester_subject,expires_at)
  WHERE status = 'pending_approval';

CREATE TABLE it_portal.atlas_deploy_events (
  id uuid PRIMARY KEY,
  proposal_id uuid NOT NULL REFERENCES it_portal.atlas_deploy_proposals(id) ON DELETE RESTRICT,
  event_seq integer NOT NULL CHECK (event_seq > 0),
  event_type varchar(32) NOT NULL CHECK (event_type IN (
    'prepared','expired','approved','revoked','cancelled',
    'execution_started','verified','failed_needs_operator','rolled_back'
  )),
  actor_subject uuid,
  occurred_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  UNIQUE (proposal_id,event_seq)
);
CREATE INDEX atlas_deploy_events_by_proposal_idx
  ON it_portal.atlas_deploy_events(proposal_id, occurred_at);

-- Role policy to enforce at activation:
-- * no ChatGPT/MCP access to Postgres, only governed backend;
-- * no UPDATE/DELETE grants on atlas_deploy_events;
-- * transaction-level permissions and audit events for approvals and ACT;
-- * migration role separate from application role;
-- * future migration must lock mutable hashes, target and version on approval.

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

-- PostgreSQL default FUNCTION privileges include EXECUTE for PUBLIC.
-- Explicitly revoke access; triggers themselves continue to run on table
-- writes authorized to a trusted backend role.
REVOKE ALL ON FUNCTION it_portal.atlas_oci_guard_binding() FROM PUBLIC;
REVOKE ALL ON FUNCTION it_portal.atlas_oci_guard_proposal_update() FROM PUBLIC;
-- No role is created and no GRANT is issued by this migration. DB owner
-- must grant SELECT on exactly proposals, bindings and events to a dedicated
-- read-only login. Never grant SELECT on challenges to the reader.
REVOKE ALL ON TABLE
  it_portal.atlas_deploy_challenges,
  it_portal.atlas_deploy_proposals,
  it_portal.atlas_deploy_events,
  it_portal.atlas_deploy_oci_bindings
FROM PUBLIC;
