-- ATLAS P2.2d - REVIEW-ONLY DDL, NOT A VERSIONED PRODUCTION MIGRATION.
-- Do NOT put in it-portal-api/migrations until DB owner/migration coordination.
-- Safe to test only in an isolated, disposable PostgreSQL database.
-- No API route, Core grant or deployment capability is activated by this file.

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
