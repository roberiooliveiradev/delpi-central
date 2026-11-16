"""ATLAS P2.2h.2p–2r: bounded read-only challenge + real CI reader contract.

No production DB, network, Docker, grants, migrations or PREPARE mutations.
The GitHub CLI/GHCR composition is already covered by separate hermetic
tests; this file validates the DB boundary, two-read TOCTOU behavior and
guaranteed blocked output.
"""
from __future__ import annotations

import asyncio
from contextlib import nullcontext
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from it_portal_app.infrastructure.persistence.atlas_deploy_challenge_inspection import (
    ChallengeInspectionError, ExplicitChallengeReadOnlyReader,
    UnreservedChallengeSnapshot, inspect_active_challenge,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_readiness_review import (
    BlockedReadinessReport, ReadinessReviewError,
    ReadOnlyReleaseReadinessReviewer, TargetReleaseReview,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_oci_seal import (
    CIReleaseEvidence, IMAGE, REPOSITORY, SOURCE_REF, WORKFLOW,
)

NOW = datetime(2026, 11, 16, 22, 45, tzinfo=timezone.utc)
USER = "11111111-2222-4333-8444-555555555555"
NONCE = "a" * 64
SHA = "b" * 40
MANIFEST = "sha256:" + "c" * 64
IMAGE_ID = "sha256:" + "d" * 64
STATEMENT = "e" * 64
SCOPE = {
    "requester_subject": USER, "environment": "hml",
    "service_id": "public-hub", "nonce": NONCE,
}


def review_target(**changes):
    return replace(TargetReleaseReview(
        requester_subject=USER, environment="hml", service_id="public-hub",
        target_commit_sha=SHA, manifest_digest=MANIFEST,
        target_image_id=IMAGE_ID, statement_sha256=STATEMENT,
    ), **changes)


def ci_evidence(**changes):
    return replace(CIReleaseEvidence(
        repository=REPOSITORY, image=IMAGE, workflow=WORKFLOW,
        source_ref=SOURCE_REF, commit_sha=SHA, manifest_digest=MANIFEST,
        image_config_id=IMAGE_ID, statement_sha256=STATEMENT,
        verified_at=NOW-timedelta(seconds=10), signature_verified=True,
    ), **changes)


def db_snapshot(*, now=NOW, issued=None, expires=None):
    issued = issued or NOW-timedelta(seconds=30)
    expires = expires or NOW+timedelta(seconds=60)
    return UnreservedChallengeSnapshot(
        environment="hml", service_id="public-hub",
        issued_at=issued, expires_at=expires, observed_at=now,
    )


class FakeChallenge:
    def __init__(self, results=None):
        self.results = list(results or [db_snapshot(), db_snapshot(now=NOW+timedelta(seconds=1))])
        self.calls = []

    def read(self, **kw):
        self.calls.append(kw)
        item = self.results[len(self.calls)-1]
        if isinstance(item, Exception):
            raise item
        return item


class FakeCI:
    def __init__(self, result=None):
        self.result = result if result is not None else ci_evidence()
        self.calls = []

    async def read(self, **kw):
        self.calls.append(kw)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def reviewer(*, challenges=None, release=None, enabled=True):
    a = challenges or FakeChallenge()
    b = release or FakeCI()
    return ReadOnlyReleaseReadinessReviewer(
        challenge_reader=a, release_reader=b, diagnostics_enabled=enabled,
    ), a, b


def run(target=None, *, challenge=NONCE, challenges=None, release=None, enabled=True):
    obj, c, b = reviewer(challenges=challenges, release=release, enabled=enabled)
    return asyncio.run(obj.read(
        target=target if target is not None else review_target(),
        challenge=challenge,
    )), c, b


def reject(code, *, target=None, challenge=NONCE, challenges=None, release=None, enabled=True):
    obj, c, b = reviewer(challenges=challenges, release=release, enabled=enabled)
    with pytest.raises(ReadinessReviewError) as exc:
        asyncio.run(obj.read(
            target=target if target is not None else review_target(),
            challenge=challenge,
        ))
    assert exc.value.code == code
    assert NONCE not in str(exc.value)
    assert USER not in str(exc.value)
    return c, b


def test_default_disabled_does_not_reach_db_or_ghcr():
    a, b = reject("ATLAS_READINESS_DISABLED", enabled=False)
    assert not a.calls and not b.calls


def test_consistent_realistic_snapshots_still_block_prepare_and_act():
    report, ch, ci = run()
    assert type(report) is BlockedReadinessReport
    assert report.status == "blocked"
    assert ch.calls == [SCOPE, SCOPE]
    assert ci.calls == [{"manifest_digest": MANIFEST, "commit_sha": SHA}]
    assert report.target_commit_sha == SHA
    assert report.target_image_id == IMAGE_ID
    assert report.release_verified_at == NOW-timedelta(seconds=10)
    assert report.challenge_checked_at == NOW+timedelta(seconds=1)
    assert report.challenge_expires_at == NOW+timedelta(seconds=60)
    assert report.challenge_issued_at == NOW-timedelta(seconds=30)
    assert report.ci_signature_verified is True
    assert not report.challenge_consumed
    assert not report.challenge_reserved
    assert not report.host_authenticated
    assert not report.rollback_ready
    assert not report.migrations_safe
    assert not report.core_permission_verified
    assert not report.prepare_eligible
    assert not report.can_execute
    assert set(("PREPARE_DISABLED", "ACT_DISABLED",
                "CHALLENGE_OBSERVED_NOT_CONSUMED",
                "HOST_COLLECTOR_IDENTITY_NOT_ATTESTED",
                "CORE_HUMAN_PERMISSION_NOT_CHECKED")).issubset(report.blocks)
    assert not hasattr(report, "proposal_id")


@pytest.mark.parametrize("field,value", [
    ("requester_subject", "not-uuid"),
    ("requester_subject", "11111111-2222-3333-8444-555555555555"),
    ("environment", "dev"), ("service_id", "it-portal-api"),
    ("target_commit_sha", "main"), ("target_commit_sha", "B"*40),
    ("manifest_digest", "latest"), ("target_image_id", "sha256:short"),
    ("statement_sha256", "X"*64),
])
def test_bad_target_denied_without_any_db_or_external_call(field, value):
    a, b = reject(
        "ATLAS_READINESS_TARGET_INVALID",
        target=review_target(**{field:value}),
    )
    assert not a.calls and not b.calls


def test_absent_or_expired_challenge_skips_ci_release_verification():
    challenge = FakeChallenge(results=[ChallengeInspectionError("CHALLENGE_INSPECTION_UNAVAILABLE")])
    a, b = reject("ATLAS_READINESS_CHALLENGE_UNAVAILABLE", challenges=challenge)
    assert len(a.calls) == 1 and not b.calls


def test_unexpected_challenge_object_is_not_treated_as_reservation():
    a, b = reject(
        "ATLAS_READINESS_CHALLENGE_INVALID",
        challenges=FakeChallenge(results=[{"status": "available"}]),
    )
    assert a.calls and not b.calls


def test_signature_and_digest_are_compared_with_the_authoritative_target():
    for field, value in [
        ("repository", "other/org"), ("image", "ghcr.io/other/release"),
        ("workflow", "workflow.yml"), ("source_ref", "refs/heads/staging"),
        ("commit_sha", "0"*40), ("manifest_digest", "sha256:"+"f"*64),
        ("image_config_id", "sha256:"+"f"*64),
        ("statement_sha256", "f"*64),
    ]:
        a, b = reject(
            "ATLAS_READINESS_RELEASE_DRIFT",
            release=FakeCI(ci_evidence(**{field:value})),
        )
        assert len(a.calls) == 1 and len(b.calls) == 1


def test_unverified_or_malformed_ci_result_denied_before_db_recheck():
    for evidence, code in [
        (ci_evidence(signature_verified=False), "ATLAS_READINESS_RELEASE_UNTRUSTED"),
        ({"signature_verified": True}, "ATLAS_READINESS_RELEASE_INVALID"),
    ]:
        a, b = reject(code, release=FakeCI(evidence))
        assert len(a.calls) == 1 and len(b.calls) == 1


def test_external_verifier_failure_does_not_surface_any_credentials():
    a, b = reject(
        "ATLAS_READINESS_RELEASE_UNAVAILABLE",
        release=FakeCI(RuntimeError("secret-token=private-source")),
    )
    assert len(a.calls) == 1 and b.calls


def test_challenge_consumed_while_external_ci_runs_is_detected():
    a, b = reject(
        "ATLAS_READINESS_CHALLENGE_UNAVAILABLE",
        challenges=FakeChallenge(results=[
            db_snapshot(),
            ChallengeInspectionError("CHALLENGE_INSPECTION_UNAVAILABLE"),
        ]),
    )
    assert len(a.calls) == 2 and len(b.calls) == 1


def test_db_row_replaced_or_clock_went_back_after_ci_is_fail_closed():
    for first, second in [
        (db_snapshot(), db_snapshot(issued=NOW-timedelta(seconds=20))),
        (db_snapshot(), db_snapshot(now=NOW-timedelta(seconds=1))),
        (db_snapshot(), db_snapshot(expires=NOW+timedelta(seconds=90))),
    ]:
        a, b = reject(
            "ATLAS_READINESS_CHALLENGE_DRIFT",
            challenges=FakeChallenge(results=[first, second]),
        )
        assert len(a.calls) == 2 and len(b.calls) == 1


def test_second_challenge_snapshot_cannot_promote_to_consumed_status():
    a, b = reject(
        "ATLAS_READINESS_CHALLENGE_DRIFT",
        challenges=FakeChallenge(results=[
            db_snapshot(), replace(db_snapshot(), one_shot_consumed=True),
        ]),
    )
    assert len(a.calls) == 2 and len(b.calls) == 1


@pytest.mark.parametrize("date", [
    NOW-timedelta(seconds=121),
    NOW+timedelta(seconds=7),
    NOW.replace(tzinfo=None),
])
def test_release_timestamp_checked_against_postgres_clock(date):
    code = "ATLAS_READINESS_CLOCK_INVALID" if date.tzinfo is None else "ATLAS_READINESS_RELEASE_STALE"
    a, b = reject(code, release=FakeCI(ci_evidence(verified_at=date)))
    assert len(a.calls) == 2 and len(b.calls) == 1


class FakeConn:
    def __init__(self, row):
        self.row = row
        self.statements = []
        self.params = []
    def transaction(self):
        return nullcontext()
    def execute(self, sql, params=None):
        self.statements.append(sql)
        self.params.append(params)
        return self
    def fetchone(self):
        return self.row
    def close(self):
        self.closed = True


def inspect(row, nonce=NONCE, **scope):
    db = FakeConn(row)
    return inspect_active_challenge(
        db, requester_subject=scope.get("requester_subject", USER),
        environment=scope.get("environment", "hml"),
        service_id=scope.get("service_id", "public-hub"), nonce=nonce,
    ), db


def test_db_inspection_is_parameterized_and_read_only():
    snap, db = inspect((
        NOW-timedelta(seconds=30), NOW+timedelta(seconds=60), None, NOW,
    ))
    assert snap.status == "observed_not_reserved"
    assert not snap.one_shot_consumed and not snap.prepare_eligible
    assert len(db.statements) == 2
    assert db.statements[0] == "SET TRANSACTION ISOLATION LEVEL READ COMMITTED READ ONLY"
    assert db.statements[1].strip().startswith("SELECT issued_at")
    assert "UPDATE" not in db.statements[1] and "INSERT" not in db.statements[1]
    assert db.params[1][0:3] == (USER, "hml", "public-hub")
    assert db.params[1][3] != NONCE
    assert len(db.params[1][3]) == 64


@pytest.mark.parametrize("row,code", [
    (None, "CHALLENGE_INSPECTION_UNAVAILABLE"),
    ((NOW, NOW+timedelta(seconds=90), NOW, NOW), "CHALLENGE_INSPECTION_UNAVAILABLE"),
    ((NOW-timedelta(seconds=91), NOW-timedelta(seconds=1), None, NOW), "CHALLENGE_INSPECTION_UNAVAILABLE"),
    ((NOW, NOW+timedelta(seconds=91), None, NOW), "CHALLENGE_INSPECTION_ROW_INVALID"),
    ((NOW+timedelta(seconds=10), NOW+timedelta(seconds=30), None, NOW), "CHALLENGE_INSPECTION_ROW_INVALID"),
    ((NOW.replace(tzinfo=None), NOW+timedelta(seconds=40), None, NOW), "CHALLENGE_INSPECTION_ROW_INVALID"),
    (("bad",), "CHALLENGE_INSPECTION_ROW_INVALID"),
])
def test_malformed_expired_consumed_or_future_row_denied(row, code):
    with pytest.raises(ChallengeInspectionError) as exc:
        inspect(row)
    assert exc.value.code == code


@pytest.mark.parametrize("changes", [
    {"requester_subject": "wrong"},
    {"environment": "dev"},
    {"service_id": "another-service"},
    {"nonce": "sha256:"+"b"*64},
    {"nonce": "A"*64},
])
def test_db_input_validation_runs_before_any_sql(changes):
    opts = dict(SCOPE)
    opts.update(changes)
    db = FakeConn(None)
    with pytest.raises(ChallengeInspectionError, match="CHALLENGE_INSPECTION_SCOPE_INVALID"):
        inspect_active_challenge(db, **opts)
    assert not db.statements


def test_disabled_connection_factory_is_not_invoked():
    calls = []
    reader = ExplicitChallengeReadOnlyReader(
        connect=lambda: calls.append("connected"),
    )
    with pytest.raises(ChallengeInspectionError, match="CHALLENGE_INSPECTION_DISABLED"):
        reader.read(**SCOPE)
    assert not calls


def test_explicit_reader_closes_connection_and_refuses_no_row():
    db = FakeConn(None)
    reader = ExplicitChallengeReadOnlyReader(connect=lambda:db, enabled=lambda:True)
    with pytest.raises(ChallengeInspectionError, match="CHALLENGE_INSPECTION_UNAVAILABLE"):
        reader.read(**SCOPE)
    assert db.closed
    assert len(db.statements) == 2


def test_readiness_modules_have_no_route_mcp_write_or_deploy_executor():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "it_portal_app/infrastructure/persistence"
    for filename in (
        "atlas_deploy_challenge_inspection.py",
        "atlas_deploy_readiness_review.py",
    ):
        text = (root / filename).read_text(encoding="utf-8")
        for forbidden in (
            "@router.", "@mcp.", "docker compose", "subprocess.run",
            "psycopg.connect(", "UPDATE it_portal", "DELETE FROM it_portal",
            "INSERT INTO it_portal",
        ):
            assert forbidden not in text
