"""P2.2e: real PostgreSQL journal tests against disposable GitHub-hosted CI DB.

NOT for the application DB. This suite skips without explicit isolated-CI gate.
It must never run via a production API, migration runner or MCP tool.
"""
from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest

try:
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
except ImportError:
    if os.environ.get("ATLAS_DISPOSABLE_PG") == "true":
        raise
    pytest.skip("psycopg is required only for disposable PostgreSQL integration", allow_module_level=True)

from it_portal_app.infrastructure.persistence.atlas_deploy_journal import (
    JournalRejected,
    PrepareIntent,
    issue_challenge,
    store_prepared,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_oci_journal import store_oci_prepared
from it_portal_app.infrastructure.persistence.atlas_deploy_oci_seal import (
    CIReleaseEvidence, HostRuntimeEvidence, OCIProposalIntent,
    REPOSITORY, IMAGE, WORKFLOW, SOURCE_REF, seal_oci_candidate,
)

_SCHEMA = Path(__file__).resolve().parents[3] / (
    "docs/12-roadmap-e-evolucao/mcp-linux-control/05-atlas-p22d-candidate-schema.sql"
)
_OCI_SCHEMA = Path(__file__).resolve().parents[3] / (
    "docs/12-roadmap-e-evolucao/mcp-linux-control/12-atlas-p22h2b-disposable-oci-bindings.sql"
)


@pytest.fixture(scope="module")
def ci_dsn():
    """Only an explicit, loopback CI database with a known disposable identity."""
    dsn = os.environ.get("ATLAS_ISOLATED_PG_DSN")
    if not (os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("ATLAS_DISPOSABLE_PG") == "true" and dsn):
        pytest.skip("PostgreSQL integration requires explicit disposable CI database")
    try:
        data = conninfo_to_dict(dsn)
    except Exception:
        pytest.fail("invalid disposable PostgreSQL DSN")
    if (data.get("host") not in ("127.0.0.1", "localhost")
            or data.get("dbname") != "atlas_ci_disposable"
            or data.get("user") != "atlas_ci"
            or data.get("port", "5432") != "5432"):
        pytest.fail("refusing non-disposable or non-loopback PostgreSQL target")
    return dsn


@pytest.fixture(scope="module")
def schema_ready(ci_dsn):
    """No DROP or migrations. Runner gives this CI service a fresh database."""
    with psycopg.connect(ci_dsn, autocommit=True, connect_timeout=5) as conn:
        result = conn.execute("SELECT 1 FROM pg_namespace WHERE nspname = 'it_portal'").fetchone()
        if result:
            pytest.fail("disposable test DB was not empty; refusing to modify it")
        conn.execute("CREATE SCHEMA it_portal")
        conn.execute(_SCHEMA.read_text(encoding="utf-8"))
        conn.execute(_OCI_SCHEMA.read_text(encoding="utf-8"))
        assert conn.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema='it_portal'"
        ).fetchone()[0] == 4
    return ci_dsn


@pytest.fixture()
def pg(schema_ready):
    with psycopg.connect(schema_ready, autocommit=True, connect_timeout=5) as conn:
        conn.execute(
            "TRUNCATE it_portal.atlas_deploy_oci_bindings, it_portal.atlas_deploy_events, "
            "it_portal.atlas_deploy_proposals, "
            "it_portal.atlas_deploy_challenges"
        )
        yield conn


def intent(**kwargs):
    base = PrepareIntent(
        requester_subject="11111111-2222-4333-8444-555555555555",
        request_id="01234567-89ab-4def-8abc-0123456789ab",
        environment="hml", service_id="it-portal-api",
        target_sha="a" * 40, base_sha="b" * 40, proposal_hash="c" * 64,
    )
    return replace(base, **kwargs)


def _counts(conn):
    return tuple(conn.execute(f"SELECT count(*) FROM it_portal.{table}").fetchone()[0]
                 for table in ("atlas_deploy_challenges", "atlas_deploy_proposals", "atlas_deploy_events"))


def test_real_postgres_create_replay_and_event_once(pg):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="it-portal-api")
    digest = hashlib.sha256(bytes.fromhex(nonce)).hexdigest()
    first = store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    second = store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    assert first.proposal_id == second.proposal_id
    assert first.result == "created_pending_approval"
    assert second.result == "replay_pending_approval"
    assert _counts(pg) == (1, 1, 1)
    used, saved = pg.execute(
        "SELECT consumed_at, challenge_digest FROM it_portal.atlas_deploy_challenges"
    ).fetchone()
    assert used is not None and saved == digest


def test_invalid_nonce_fails_before_insert_and_preserves_database(pg):
    with pytest.raises(JournalRejected, match="CHALLENGE_MISSING_OR_CONSUMED"):
        store_prepared(pg, intent=intent(), signed_receipt_challenge="f" * 64)
    assert _counts(pg) == (0, 0, 0)


def test_replay_payload_conflict_preserves_original(pg):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="it-portal-api")
    store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    with pytest.raises(JournalRejected, match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        store_prepared(pg, intent=intent(target_sha="d" * 40), signed_receipt_challenge=nonce)
    assert _counts(pg) == (1, 1, 1)


def test_one_shot_challenge_for_different_request(pg):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="it-portal-api")
    store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    with pytest.raises(JournalRejected, match="CHALLENGE_MISSING_OR_CONSUMED"):
        store_prepared(pg, intent=intent(request_id=str(uuid4())), signed_receipt_challenge=nonce)
    assert _counts(pg) == (1, 1, 1)


def test_expired_challenge_is_not_consumed(pg):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="it-portal-api")
    # Keep CHECK expiration <= issued +90sec; only a disposable CI DB.
    pg.execute(
        "UPDATE it_portal.atlas_deploy_challenges SET "
        "issued_at=clock_timestamp()-interval '120 seconds', "
        "expires_at=clock_timestamp()-interval '60 seconds'"
    )
    with pytest.raises(JournalRejected, match="CHALLENGE_MISSING_OR_CONSUMED"):
        store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    assert _counts(pg) == (1, 0, 0)


def test_parallel_same_request_serializes_to_one_proposal(pg, schema_ready):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="it-portal-api")
    start = Barrier(2)

    def writer():
        with psycopg.connect(schema_ready, autocommit=True, connect_timeout=5) as conn:
            start.wait(timeout=5)
            return store_prepared(conn, intent=intent(), signed_receipt_challenge=nonce)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(writer) for _ in range(2)]
        outcomes = [f.result(timeout=15) for f in futures]
    assert len({r.proposal_id for r in outcomes}) == 1
    assert {r.result for r in outcomes} == {
        "created_pending_approval", "replay_pending_approval",
    }
    assert _counts(pg) == (1, 1, 1)


def test_partial_invalid_attempt_does_not_leave_event(pg):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="gateway")
    with pytest.raises(JournalRejected, match="CHALLENGE_MISSING_OR_CONSUMED"):
        store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    assert _counts(pg) == (1, 0, 0)



# P2.2h.2b tests: same ephemeral database and schema, never PROD/HML.
def oci_bundle(*, environment="prod", request_id="01234567-89ab-4def-8abc-0123456789ab"):
    now = datetime.now(timezone.utc) - timedelta(seconds=1)
    base = OCIProposalIntent(
        requester_subject="11111111-2222-4333-8444-555555555555",
        request_id=request_id, environment=environment, service_id="public-hub",
        target_commit_sha="f81ddd0075de1e4ef8bb68ca58791e9c43e70759",
        base_commit_sha="03cecb7ed90946c799a66ca9b22b45beb221282e",
        manifest_digest="sha256:" + "a" * 64,
        target_image_id="sha256:" + "b" * 64,
        base_image_id="sha256:" + "c" * 64,
        rollback_image_id="sha256:" + "c" * 64,
        attestation_statement_sha256="d" * 64,
        host_challenge_sha256="e" * 64,
        preview_hash="f" * 64, rollback_ready=True,
    )
    ci = CIReleaseEvidence(
        repository=REPOSITORY, image=IMAGE, workflow=WORKFLOW, source_ref=SOURCE_REF,
        commit_sha=base.target_commit_sha, manifest_digest=base.manifest_digest,
        image_config_id=base.target_image_id, statement_sha256=base.attestation_statement_sha256,
        verified_at=now, signature_verified=True,
    )
    host = HostRuntimeEvidence(
        environment=environment, service_id="public-hub",
        container_name="delpi-public-hub" if environment == "prod" else "delpi-hml-public-hub",
        compose_project="infra" if environment == "prod" else "delpi-hml",
        commit_sha=base.base_commit_sha, running_image_id=base.base_image_id,
        observed_at=now, challenge_verified=True,
        challenge_sha256=base.host_challenge_sha256,
        running=True, healthy=True, checkout_clean=True,
    )
    sealed = seal_oci_candidate(intent=base, ci=ci, host=host, now=now, backend_policy_enabled=True)
    return base, ci, host, sealed


def _oci_store(conn, bundle, nonce):
    i, c, h, s = bundle
    return store_oci_prepared(
        conn, intent=i, ci=c, host=h, candidate=s,
        signed_receipt_challenge=nonce, backend_policy_enabled=True,
    )


def _oci_counts(conn):
    return tuple(conn.execute(
        "SELECT count(*) FROM it_portal." + name
    ).fetchone()[0] for name in (
        "atlas_deploy_challenges", "atlas_deploy_proposals",
        "atlas_deploy_oci_bindings", "atlas_deploy_events",
    ))


def test_oci_binding_atomic_create_and_identical_retry(pg):
    bundle = oci_bundle()
    i, _, _, candidate = bundle
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    first = _oci_store(pg, bundle, nonce)
    again = _oci_store(pg, bundle, nonce)
    assert first.result == "created_pending_approval"
    assert again.result == "replay_pending_approval"
    assert first.proposal_id == again.proposal_id
    assert _oci_counts(pg) == (1, 1, 1, 1)
    saved = pg.execute(
        "SELECT p.proposal_hash, b.sealed_binding_sha256, b.signed_manifest_digest,"
        " b.release_image_id, b.base_image_id, b.rollback_image_id "
        "FROM it_portal.atlas_deploy_proposals p JOIN it_portal.atlas_deploy_oci_bindings b"
        " ON p.id=b.proposal_id",
    ).fetchone()
    assert saved == (
        candidate.binding_sha256, candidate.binding_sha256,
        i.manifest_digest, i.target_image_id, i.base_image_id, i.base_image_id,
    )


@pytest.mark.parametrize("environment", ["hml", "prod"])
def test_oci_binding_has_production_hml_isolation(pg, environment):
    i, c, h, sealed = oci_bundle(environment=environment)
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    assert _oci_store(pg, (i, c, h, sealed), nonce).result == "created_pending_approval"
    env, service = pg.execute(
        "SELECT environment,service_id FROM it_portal.atlas_deploy_oci_bindings"
    ).fetchone()
    assert env == environment and service == "public-hub"


def test_oci_same_request_conflicting_manifest_is_rejected(pg):
    i, ci, host, sealed = bundle = oci_bundle()
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    _oci_store(pg, bundle, nonce)
    changed = replace(i, manifest_digest="sha256:" + "a" * 63 + "b")
    ci2 = replace(ci, manifest_digest=changed.manifest_digest)
    candidate2 = seal_oci_candidate(intent=changed, ci=ci2, host=host,
                                    now=sealed.issued_at, backend_policy_enabled=True)
    with pytest.raises(JournalRejected, match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        _oci_store(pg, (changed, ci2, host, candidate2), nonce)
    assert _oci_counts(pg) == (1, 1, 1, 1)


def test_oci_replay_requires_same_challenge(pg):
    bundle = oci_bundle()
    i = bundle[0]
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    _oci_store(pg, bundle, nonce)
    another = issue_challenge(pg, requester_subject=i.requester_subject,
                              environment=i.environment, service_id=i.service_id)
    with pytest.raises(JournalRejected, match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        _oci_store(pg, bundle, another)
    assert _oci_counts(pg) == (2, 1, 1, 1)


def test_oci_different_request_cannot_reuse_consumed_nonce(pg):
    bundle = oci_bundle()
    i = bundle[0]
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    _oci_store(pg, bundle, nonce)
    other = oci_bundle(request_id=str(uuid4()))
    with pytest.raises(JournalRejected, match="CHALLENGE_MISSING_OR_CONSUMED"):
        _oci_store(pg, other, nonce)
    assert _oci_counts(pg) == (1, 1, 1, 1)


def test_oci_legacy_proposal_without_binding_denied_on_replay(pg):
    i, _, _, sealed = bundle = oci_bundle()
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    store_prepared(pg, intent=PrepareIntent(
        requester_subject=i.requester_subject, request_id=i.request_id,
        environment=i.environment, service_id=i.service_id,
        target_sha=i.target_commit_sha, base_sha=i.base_commit_sha,
        proposal_hash=sealed.binding_sha256,
    ), signed_receipt_challenge=nonce)
    with pytest.raises(JournalRejected, match="OCI_BINDING_MISSING"):
        _oci_store(pg, bundle, nonce)
    assert _oci_counts(pg) == (1, 1, 0, 1)


def test_oci_legacy_proposal_without_binding_cannot_be_approved(pg):
    i, _, _, sealed = oci_bundle()
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    stored = store_prepared(pg, intent=PrepareIntent(
        requester_subject=i.requester_subject, request_id=i.request_id,
        environment=i.environment, service_id=i.service_id,
        target_sha=i.target_commit_sha, base_sha=i.base_commit_sha,
        proposal_hash=sealed.binding_sha256,
    ), signed_receipt_challenge=nonce)
    with pytest.raises(psycopg.errors.CheckViolation):
        pg.execute(
            "UPDATE it_portal.atlas_deploy_proposals SET status='approved' WHERE id=%s",
            (stored.proposal_id,),
        )


def test_oci_binding_and_parent_identity_cannot_be_modified(pg):
    bundle = oci_bundle()
    i = bundle[0]
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    _oci_store(pg, bundle, nonce)
    with pytest.raises(psycopg.errors.CheckViolation):
        pg.execute(
            "UPDATE it_portal.atlas_deploy_oci_bindings SET base_image_id=%s",
            ("sha256:" + "9" * 64,),
        )
    with pytest.raises(psycopg.errors.CheckViolation):
        pg.execute(
            "DELETE FROM it_portal.atlas_deploy_oci_bindings"
        )
    with pytest.raises(psycopg.errors.CheckViolation):
        pg.execute(
            "UPDATE it_portal.atlas_deploy_proposals SET target_sha=%s",
            ("9" * 40,),
        )
    assert _oci_counts(pg) == (1, 1, 1, 1)


def test_oci_invalid_signature_and_stale_host_leave_database_untouched(pg):
    bundle = oci_bundle()
    i, ci, host, sealed = bundle
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    bad_ci = replace(ci, signature_verified=False)
    with pytest.raises(JournalRejected, match="OCI_ATTESTATION_INVALID"):
        _oci_store(pg, (i, bad_ci, host, sealed), nonce)
    bad_host = replace(host, observed_at=host.observed_at-timedelta(seconds=130))
    with pytest.raises(JournalRejected, match="OCI_EVIDENCE_STALE"):
        _oci_store(pg, (i, ci, bad_host, sealed), nonce)
    assert _oci_counts(pg) == (1, 0, 0, 0)
    consumed_at = pg.execute(
        "SELECT consumed_at FROM it_portal.atlas_deploy_challenges"
    ).fetchone()[0]
    assert consumed_at is None


def test_oci_default_policy_disabled_before_sql(pg):
    bundle = oci_bundle()
    i, ci, host, candidate = bundle
    with pytest.raises(JournalRejected, match="OCI_POLICY_DISABLED"):
        store_oci_prepared(
            pg, intent=i, ci=ci, host=host, candidate=candidate,
            signed_receipt_challenge="a" * 64,
        )
    assert _oci_counts(pg) == (0, 0, 0, 0)


def test_oci_event_insert_failure_rolls_back_all_three_writes(pg):
    i, ci, host, candidate = bundle = oci_bundle()
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    pg.execute("""
        CREATE FUNCTION it_portal.atlas_ci_block_event() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'ephemeral injected failure'; END $$;
    """)
    pg.execute("""
        CREATE TRIGGER atlas_ci_block_event BEFORE INSERT
        ON it_portal.atlas_deploy_events FOR EACH ROW
        EXECUTE FUNCTION it_portal.atlas_ci_block_event();
    """)
    try:
        with pytest.raises(JournalRejected, match="OCI_JOURNAL_DATABASE_UNAVAILABLE"):
            _oci_store(pg, bundle, nonce)
        assert _oci_counts(pg) == (1, 0, 0, 0)
        assert pg.execute(
            "SELECT consumed_at IS NULL FROM it_portal.atlas_deploy_challenges"
        ).fetchone()[0] is True
    finally:
        pg.execute("DROP TRIGGER atlas_ci_block_event ON it_portal.atlas_deploy_events")
        pg.execute("DROP FUNCTION it_portal.atlas_ci_block_event()")


def test_oci_concurrent_retry_serializes_one_binding(pg, schema_ready):
    bundle = oci_bundle()
    i = bundle[0]
    nonce = issue_challenge(pg, requester_subject=i.requester_subject,
                            environment=i.environment, service_id=i.service_id)
    barrier = Barrier(2)

    def worker():
        with psycopg.connect(schema_ready, autocommit=True, connect_timeout=5) as connection:
            barrier.wait(timeout=5)
            return _oci_store(connection, bundle, nonce)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [future.result(timeout=15) for future in
                   [pool.submit(worker) for _ in range(2)]]
    assert len({r.proposal_id for r in results}) == 1
    assert {r.result for r in results} == {
        "created_pending_approval", "replay_pending_approval",
    }
    assert _oci_counts(pg) == (1, 1, 1, 1)
