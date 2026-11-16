"""ATLAS P2.2h.2s-u: strict signed Linux->BFF wire and blocked E2E review.

Hermetic synthetic keys and payloads. The real Linux signer compatibility
is tested separately with actual host signer code in the disposable Docker CI.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from it_portal_app.infrastructure.persistence.atlas_deploy_challenge_inspection import (
    UnreservedChallengeSnapshot,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_host_receipt_bridge import (
    ExpectedBaseRelease, HostReceiptBridgeError, PinnedHostTarget,
    SignedReceiptWire, verify_host_receipt_pair,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_full_readiness import (
    FullReadOnlyReadinessReviewer, FullReadinessBlocked, FullReadinessError,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_readiness_review import (
    BlockedReadinessReport, TargetReleaseReview,
)

NOW = datetime(2026, 11, 16, 22, 45, tzinfo=timezone.utc)
NONCE = "a"*64
NONCE_SHA = hashlib.sha256(bytes.fromhex(NONCE)).hexdigest()
REPO = "roberiooliveiradev/delpi-central"
BASE_SHA = "b"*40
TARGET_SHA = "c"*40
BASE_IMAGE = "sha256:"+"d"*64
TARGET_IMAGE = "sha256:"+"e"*64
MANIFEST = "sha256:"+"f"*64
STATEMENT = "1"*64
HOST_KEY = b"disposable-runtime-test-key-00112233445566778899"
GIT_KEY = b"disposable-git-test-key-99887766554433221100"
RUNTIME_DOMAIN = b"atlas:host-runtime-receipt:v2:\x00"
GIT_DOMAIN = b"atlas:git-checkout-observation:v1:\x00"
HOST = PinnedHostTarget(
    host_id="srv-api-pilot", environment="hml", service_id="public-hub",
    container_name="delpi-hml-public-hub", compose_project="delpi-hml",
)
BASE = ExpectedBaseRelease(BASE_SHA, BASE_IMAGE)
TARGET = TargetReleaseReview(
    requester_subject="11111111-2222-4333-8444-555555555555",
    environment="hml", service_id="public-hub", target_commit_sha=TARGET_SHA,
    target_image_id=TARGET_IMAGE, manifest_digest=MANIFEST,
    statement_sha256=STATEMENT,
)


def runtime_doc():
    return {
        "version": 2,
        "repository": REPO,
        "host_id": HOST.host_id,
        "environment": HOST.environment,
        "service_id": HOST.service_id,
        "compose_project": HOST.compose_project,
        "container_name": HOST.container_name,
        "commit_sha": BASE_SHA,
        "release_image_id": BASE_IMAGE,
        "running_image_id": BASE_IMAGE,
        "container_id": "9"*64,
        "running": True, "healthy": True, "checkout_clean": False,
        "observed_at": NOW.isoformat().replace("+00:00", "Z"),
        "challenge": NONCE,
    }


def git_doc():
    return {
        "version": 1,
        "repository": REPO,
        "host_id": HOST.host_id,
        "environment": HOST.environment,
        "service_id": HOST.service_id,
        "compose_project": HOST.compose_project,
        "container_name": HOST.container_name,
        "branch": "main", "head_sha": BASE_SHA,
        "tracked_and_untracked_clean": True,
        "observation_scope": "tracked_and_untracked_nonignored",
        "observed_at": NOW.isoformat().replace("+00:00", "Z"),
        "challenge": NONCE,
    }


def seal(doc, key, domain):
    body = json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()
    return SignedReceiptWire(
        body=body,
        mac_hex=hmac.new(key, domain+body, hashlib.sha256).hexdigest(),
    )


def both(runtime=None, git=None):
    return (
        seal(runtime if runtime is not None else runtime_doc(), HOST_KEY, RUNTIME_DOMAIN),
        seal(git if git is not None else git_doc(), GIT_KEY, GIT_DOMAIN),
    )


def verify(*, runtime=None, git=None, host=HOST, base=BASE, nonce=NONCE,
           clock=NOW, runtime_key=HOST_KEY, git_key=GIT_KEY):
    rt, gi = both(runtime, git)
    return verify_host_receipt_pair(
        runtime_receipt=rt, git_receipt=gi,
        runtime_key=runtime_key, git_key=git_key,
        target=host, base=base, nonce=nonce, now=clock,
    )


def denied(code, **kwargs):
    with pytest.raises(HostReceiptBridgeError) as exc:
        verify(**kwargs)
    assert exc.value.code == code
    assert NONCE not in str(exc.value)
    assert HOST_KEY.decode() not in str(exc.value)


def test_signed_runtime_git_pair_is_verified_but_not_promoted_to_trust():
    pair = verify()
    assert pair.host_id == HOST.host_id
    assert pair.environment == "hml"
    assert pair.base_commit_sha == BASE_SHA
    assert pair.base_image_id == BASE_IMAGE
    assert pair.git_head_sha == BASE_SHA
    assert pair.branch == "main"
    assert pair.healthy and pair.running and pair.git_observed_clean
    assert pair.challenge_digest == NONCE_SHA
    assert pair.blocks == (
        "HOST_COLLECTOR_IDENTITY_NOT_ATTESTED",
        "GIT_IGNORED_FILES_NOT_ATTESTED",
        "GIT_FILESYSTEM_NOT_ATOMIC",
        "CHALLENGE_NOT_CONSUMED",
    )
    assert pair.signature_integrity_verified is True
    assert not pair.collector_identity_attested
    assert not pair.checkout_integrity_attested
    assert not pair.challenge_consumed
    assert not pair.prepare_eligible
    assert len(pair.runtime_receipt_sha256) == 64
    assert pair.git_receipt_sha256 != pair.runtime_receipt_sha256


@pytest.mark.parametrize("side,key,value,code", [
    ("runtime", "version", 1, "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("runtime", "repository", "evil/repo", "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("runtime", "host_id", "evil-host", "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("runtime", "environment", "prod", "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("runtime", "service_id", "wrong", "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("runtime", "compose_project", "other", "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("runtime", "container_name", "other", "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("runtime", "challenge", "f"*64, "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("git", "version", 2, "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("git", "host_id", "wrong", "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("git", "environment", "prod", "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("git", "compose_project", "prod", "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("git", "container_name", "bad", "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("git", "challenge", "0"*64, "ATLAS_HOST_TARGET_OR_NONCE_DRIFT"),
    ("runtime", "commit_sha", "0"*40, "ATLAS_HOST_BASE_DRIFT"),
    ("runtime", "running_image_id", "sha256:"+"f"*64, "ATLAS_HOST_RUNTIME_INVALID"),
    ("runtime", "container_id", "bad", "ATLAS_HOST_RUNTIME_INVALID"),
    ("runtime", "running", 1, "ATLAS_HOST_RUNTIME_INVALID"),
    ("runtime", "healthy", "yes", "ATLAS_HOST_RUNTIME_INVALID"),
    ("runtime", "checkout_clean", True, "ATLAS_HOST_RUNTIME_INVALID"),
    ("git", "head_sha", "BAD", "ATLAS_HOST_GIT_INVALID"),
    ("git", "branch", "", "ATLAS_HOST_GIT_INVALID"),
    ("git", "tracked_and_untracked_clean", 1, "ATLAS_HOST_GIT_INVALID"),
    ("git", "observation_scope", "tracked_only", "ATLAS_HOST_GIT_INVALID"),
])
def test_validly_signed_but_mismatched_or_invalid_claims_denied(side, key, value, code):
    rt, git = runtime_doc(), git_doc()
    if side == "runtime":
        rt[key] = value
    else:
        git[key] = value
    denied(code, runtime=rt, git=git)


def test_docker_base_image_mismatch_fails_closed_even_with_valid_mac():
    denied("ATLAS_HOST_BASE_DRIFT", base=ExpectedBaseRelease(BASE_SHA, "sha256:"+"1"*64))


def test_bad_keys_same_keys_or_wrong_scope_denied_before_verifying_receipts():
    denied("ATLAS_HOST_BRIDGE_UNCONFIGURED", runtime_key=b"x")
    denied("ATLAS_HOST_BRIDGE_UNCONFIGURED", git_key=HOST_KEY)
    denied("ATLAS_HOST_BRIDGE_UNCONFIGURED", nonce="bad")
    denied("ATLAS_HOST_BRIDGE_UNCONFIGURED", clock=NOW.replace(tzinfo=None))
    denied("ATLAS_HOST_BRIDGE_UNCONFIGURED", host=replace(HOST, container_name="another"))
    denied("ATLAS_HOST_BRIDGE_UNCONFIGURED", host=replace(HOST, environment="dev"))
    denied("ATLAS_HOST_BRIDGE_UNCONFIGURED", base=ExpectedBaseRelease("main", BASE_IMAGE))


def test_wrong_nonce_does_not_validate_mac_signed_to_prior_challenge():
    denied("ATLAS_HOST_TARGET_OR_NONCE_DRIFT", nonce="f"*64)


def test_tampered_bytes_or_cross_domain_are_rejected():
    rt, gi = both()
    altered = SignedReceiptWire(rt.body + b" ", rt.mac_hex)
    with pytest.raises(HostReceiptBridgeError, match="ATLAS_HOST_SIGNATURE_INVALID"):
        verify_host_receipt_pair(
            runtime_receipt=altered, git_receipt=gi,
            runtime_key=HOST_KEY, git_key=GIT_KEY,
            target=HOST, base=BASE, nonce=NONCE, now=NOW,
        )
    with pytest.raises(HostReceiptBridgeError, match="ATLAS_HOST_SIGNATURE_INVALID"):
        verify_host_receipt_pair(
            runtime_receipt=gi, git_receipt=rt,
            runtime_key=HOST_KEY, git_key=GIT_KEY,
            target=HOST, base=BASE, nonce=NONCE, now=NOW,
        )


def test_even_correctly_mac_signed_duplicate_json_and_extra_fields_are_rejected():
    rt, gi = both()
    duplicate = gi.body[:-1] + b',"host_id":"evil-host"}'
    bad_mac = hmac.new(GIT_KEY, GIT_DOMAIN+duplicate, hashlib.sha256).hexdigest()
    with pytest.raises(HostReceiptBridgeError, match="ATLAS_HOST_RECEIPT_INVALID"):
        verify_host_receipt_pair(
            runtime_receipt=rt,
            git_receipt=SignedReceiptWire(duplicate, bad_mac),
            runtime_key=HOST_KEY, git_key=GIT_KEY,
            target=HOST, base=BASE, nonce=NONCE, now=NOW,
        )
    denied("ATLAS_HOST_RECEIPT_INVALID", git={**git_doc(), "can_act": True})


@pytest.mark.parametrize("gap_seconds,reason", [
    (16, "HOST_GIT_OBSERVATION_GAP"),
    (10, None),
])
def test_host_git_observation_gap_is_reported_not_promoted(gap_seconds, reason):
    git = git_doc()
    git["observed_at"] = (
        NOW-timedelta(seconds=gap_seconds)
    ).isoformat().replace("+00:00", "Z")
    pair = verify(git=git)
    assert ("HOST_GIT_OBSERVATION_GAP" in pair.blocks) is bool(reason)


@pytest.mark.parametrize("age,code", [
    (-91, "ATLAS_HOST_RECEIPT_STALE"),
    (6, "ATLAS_HOST_RECEIPT_STALE"),
    (-90, None),
    (5, None),
])
def test_receipt_freshness_with_db_clock(age, code):
    rt = runtime_doc()
    rt["observed_at"] = (NOW+timedelta(seconds=age)).isoformat().replace("+00:00", "Z")
    if code:
        denied(code, runtime=rt)
    else:
        result = verify(runtime=rt)
        assert result.prepare_eligible is False


def test_unhealthy_dirty_or_wrong_git_commit_stay_blocked():
    rt=runtime_doc()
    rt["healthy"]=False
    git=git_doc()
    git["head_sha"]="0"*40
    git["branch"]="feature"
    git["tracked_and_untracked_clean"]=False
    pair=verify(runtime=rt, git=git)
    for expected in (
        "HOST_RUNTIME_UNHEALTHY",
        "GIT_RUNTIME_COMMIT_DRIFT",
        "GIT_CHECKOUT_NOT_MAIN",
        "GIT_CHECKOUT_DIRTY",
    ):
        assert expected in pair.blocks


class FakeRelease:
    def __init__(self, data=None, issue=None):
        self.data = data
        self.issue = issue
        self.calls = []
    async def read(self, **kwargs):
        self.calls.append(kwargs)
        if self.issue:
            raise self.issue
        return self.data if self.data is not None else release_result()


class FakeChallenge:
    def __init__(self, data=None, issue=None):
        self.data = data
        self.issue = issue
        self.calls = []
    def read(self, **kwargs):
        self.calls.append(kwargs)
        if self.issue:
            raise self.issue
        return self.data if self.data is not None else challenge_result()


def release_result(**changes):
    return replace(BlockedReadinessReport(
        status="blocked",
        blocks=("CHALLENGE_OBSERVED_NOT_CONSUMED","PREPARE_DISABLED","ACT_DISABLED"),
        environment="hml", service_id="public-hub",
        target_commit_sha=TARGET_SHA, target_image_id=TARGET_IMAGE,
        manifest_digest=MANIFEST, statement_sha256=STATEMENT,
        release_verified_at=NOW-timedelta(seconds=12),
        challenge_checked_at=NOW,
        challenge_expires_at=NOW+timedelta(seconds=25),
        challenge_issued_at=NOW-timedelta(seconds=30),
        ci_signature_verified=True,
    ), **changes)


def challenge_result(**changes):
    return replace(UnreservedChallengeSnapshot(
        environment="hml", service_id="public-hub",
        issued_at=NOW-timedelta(seconds=30),
        expires_at=NOW+timedelta(seconds=25),
        observed_at=NOW+timedelta(seconds=1),
    ), **changes)


def full(*, enabled=True, release=None, challenge=None, runtime=None,
         git=None, base=BASE, target=TARGET):
    release_f = release if release is not None else FakeRelease()
    challenge_f = challenge if challenge is not None else FakeChallenge()
    reviewer=FullReadOnlyReadinessReviewer(
        readiness=release_f,
        challenge_reader=challenge_f,
        runtime_key=HOST_KEY, checkout_key=GIT_KEY,
        diagnostics_enabled=enabled,
    )
    rt, gi=both(runtime, git)
    return reviewer, release_f, challenge_f, rt, gi, base, target


def run_full(**kwargs):
    reviewer, release, challenge, rt, gi, base, target=full(**kwargs)
    outcome=asyncio.run(reviewer.read(
        target=target, host=HOST, base=base,
        runtime_receipt=rt, checkout_receipt=gi, challenge=NONCE,
    ))
    return outcome, release, challenge


def fail_full(code, **kwargs):
    reviewer, release, challenge, rt, gi, base, target=full(**kwargs)
    with pytest.raises(FullReadinessError) as exc:
        asyncio.run(reviewer.read(
            target=target, host=HOST, base=base,
            runtime_receipt=rt, checkout_receipt=gi, challenge=NONCE,
        ))
    assert exc.value.code == code
    assert NONCE not in str(exc.value)
    return release,challenge


def test_full_review_requires_explicit_two_stage_enablement():
    r,c=fail_full("ATLAS_FULL_REVIEW_DISABLED", enabled=False)
    assert not r.calls and not c.calls


def test_combined_release_host_and_final_challenge_check_still_denies_prepare():
    outcome, rel, db = run_full()
    assert type(outcome) is FullReadinessBlocked
    assert outcome.status == "blocked"
    assert len(rel.calls)==1 and len(db.calls)==1
    assert db.calls[0]=={
        "requester_subject": TARGET.requester_subject,
        "environment":"hml","service_id":"public-hub","nonce":NONCE,
    }
    assert outcome.ci_signature_verified
    assert outcome.host_receipt_integrity_verified
    assert outcome.runtime_receipt_sha256 != outcome.git_receipt_sha256
    assert outcome.challenge_checked_at==NOW+timedelta(seconds=1)
    assert "HOST_COLLECTOR_IDENTITY_NOT_ATTESTED" in outcome.blocks
    assert "CORE_PREPARE_GRANT_NOT_CHECKED" in outcome.blocks
    assert "PREPARE_DISABLED" in outcome.blocks and "ACT_DISABLED" in outcome.blocks
    assert not outcome.host_collector_identity_attested
    assert not outcome.git_checkout_integrity_attested
    assert not outcome.one_shot_challenge_consumed
    assert not outcome.prepare_eligible
    assert not outcome.can_execute
    assert not hasattr(outcome,"proposal_id")


def test_full_report_rejects_replayed_or_invalid_ci_contract():
    for change in (
        {"status":"approved"},
        {"ci_signature_verified":False},
        {"blocks":("ACT_DISABLED",)},
        {"target_commit_sha":"0"*40},
        {"prepare_eligible":True},
    ):
        rel, ch = fail_full(
            "ATLAS_FULL_RELEASE_CONTRACT_INVALID",
            release=FakeRelease(data=release_result(**change)),
        )
        assert len(rel.calls)==1 and not ch.calls


def test_full_review_rejects_final_challenge_changed_or_consumed():
    rel,ch=fail_full(
        "ATLAS_FULL_CHALLENGE_FINAL_DRIFT",
        challenge=FakeChallenge(data=challenge_result(expires_at=NOW+timedelta(seconds=30))),
    )
    assert len(rel.calls)==1 and len(ch.calls)==1
    rel,ch=fail_full(
        "ATLAS_FULL_CHALLENGE_FINAL_DRIFT",
        challenge=FakeChallenge(data=challenge_result(one_shot_consumed=True)),
    )
    assert len(rel.calls)==1 and len(ch.calls)==1


def test_full_review_denies_challenge_reissued_with_same_expiry():
    rel,ch=fail_full(
        "ATLAS_FULL_CHALLENGE_FINAL_DRIFT",
        challenge=FakeChallenge(data=challenge_result(issued_at=NOW-timedelta(seconds=15))),
    )
    assert len(rel.calls)==1 and len(ch.calls)==1


def test_full_review_denies_expired_or_removed_challenge_after_host_verification():
    rel,ch=fail_full(
        "ATLAS_FULL_CHALLENGE_FINAL_UNAVAILABLE",
        challenge=FakeChallenge(issue=RuntimeError("invalid source token")),
    )
    assert rel.calls and ch.calls


def test_full_review_fails_closed_for_missing_or_forged_host_evidence():
    rel,ch=fail_full(
        "ATLAS_FULL_HOST_EVIDENCE_DENIED",
        runtime={**runtime_doc(),"commit_sha":"0"*40},
    )
    assert rel.calls and not ch.calls


def test_wrong_base_or_noncanon_target_rejected_before_ci():
    for kwargs in (
        {"base":ExpectedBaseRelease(TARGET_SHA,BASE_IMAGE)},
        {"base":ExpectedBaseRelease(BASE_SHA,TARGET_IMAGE)},
        {"target":replace(TARGET,environment="prod")},
    ):
        rel,ch=fail_full("ATLAS_FULL_TARGET_MISMATCH",**kwargs)
        assert not rel.calls and not ch.calls


def test_modules_cannot_be_exposed_as_fastapi_mcp_or_journal_writers():
    from pathlib import Path
    root=Path(__file__).resolve().parents[2] / "it_portal_app/infrastructure/persistence"
    for name in ("atlas_deploy_host_receipt_bridge.py","atlas_deploy_full_readiness.py"):
        source=(root/name).read_text()
        for forbidden in (
            "@router.", "subprocess.run", "docker compose",
            "psycopg.connect(", "INSERT INTO it_portal", "UPDATE it_portal",
            "os.system",
        ):
            assert forbidden not in source
