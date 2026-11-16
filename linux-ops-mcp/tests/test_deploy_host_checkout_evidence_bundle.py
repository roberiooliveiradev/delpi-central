"""P2.2h.2m: combined signer, verifier and fail-closed host evidence tests.

Use only ephemeral Git repositories and synthetic host/Docker snapshots.
Real HMAC/SHA256 is exercised, never production keys or external services.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import subprocess
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from linux_ops_mcp.deploy_git_checkout_readonly import GitCheckoutReadOnlyObserver
from linux_ops_mcp.deploy_git_checkout_witness import (
    GitCheckoutWitnessError, _DOMAIN as CHECKOUT_DOMAIN,
    issue_git_checkout_witness, verify_git_checkout_witness,
)
from linux_ops_mcp.deploy_host_checkout_evidence_bundle import (
    HostEvidenceBundleError, inspect_signed_host_checkout_bundle,
)
from linux_ops_mcp.deploy_host_oci_preflight import HostOCIIntentPreview
from linux_ops_mcp.deploy_host_receipt import SignedHostReceipt
from linux_ops_mcp.deploy_host_runtime_v2 import issue_host_runtime_receipt_v2
from linux_ops_mcp.deploy_host_signer import (
    SignedReleaseRecord, _DOMAIN as RELEASE_DOMAIN,
)
from linux_ops_mcp.deploy_host_source import RuntimeContainer, RuntimeTarget

NOW = datetime(2026, 11, 16, 23, 0, tzinfo=timezone.utc)
TARGET = RuntimeTarget(
    environment="hml", service_id="public-hub", host_id="srv-api-pilot",
    compose_project="delpi-hml", container_name="delpi-hml-public-hub",
)
CHALLENGE = "a" * 64
HASH = hashlib.sha256(bytes.fromhex(CHALLENGE)).hexdigest()
HOST_KEY = b"host-hmac-only-isolated-fixture-value-123456"
GIT_KEY = b"git-checkout-only-isolated-hmac-value-123456"
RELEASE_KEY = b"release-record-only-isolated-hmac-value-123456"
IMAGE = "sha256:" + "c" * 64
TARGET_IMAGE = "sha256:" + "d" * 64
TARGET_COMMIT = "f" * 40


def isolated_git(root: Path, *args: str) -> str:
    env = {
        "PATH": "/usr/bin:/bin", "HOME": "/nonexistent",
        "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
    }
    p = subprocess.run(
        ["git", "-C", str(root), *args], env=env,
        capture_output=True, text=True, check=True, timeout=10,
    )
    return p.stdout.strip()


@pytest.fixture
def checkout(tmp_path):
    root = tmp_path / "safe-test-checkout"
    root.mkdir()
    isolated_git(root, "init", "-q", "-b", "main")
    (root / "tracked.txt").write_text("verified isolated test\n", encoding="utf-8")
    isolated_git(root, "add", "tracked.txt")
    isolated_git(root, "-c", "user.name=CI Test",
                 "-c", "user.email=test@example.invalid",
                 "commit", "-q", "-m", "fixture initial commit")
    return root


class DockerFixture:
    def __init__(self, *, running=True, healthy=True):
        self.running = running
        self.healthy = healthy

    async def inspect(self, target):
        assert target == TARGET
        return RuntimeContainer(
            container_id="e" * 64, image_id=IMAGE,
            running=self.running, healthy=self.healthy,
        )


def release_record(sha: str) -> SignedReleaseRecord:
    payload = json.dumps({
        "version": 1, "repository": "roberiooliveiradev/delpi-central",
        "host_id": TARGET.host_id, "environment": TARGET.environment,
        "service_id": TARGET.service_id, "execution_id": str(uuid4()),
        "commit_sha": sha, "image_id": IMAGE,
    }, sort_keys=True, separators=(",", ":")).encode()
    return SignedReleaseRecord(
        payload, hmac.new(RELEASE_KEY, RELEASE_DOMAIN + payload, hashlib.sha256).hexdigest(),
    )


def intent(sha: str, **changes) -> HostOCIIntentPreview:
    original = HostOCIIntentPreview(
        environment=TARGET.environment, service_id=TARGET.service_id,
        base_commit_sha=sha, base_image_id=IMAGE,
        target_commit_sha=TARGET_COMMIT, target_image_id=TARGET_IMAGE,
        manifest_digest="sha256:" + "1" * 64,
        attestation_statement_sha256="2" * 64,
        host_challenge_sha256=HASH,
        rollback_image_id=IMAGE, rollback_ready=True,
    )
    return replace(original, **changes)


def host_receipt(sha: str, *, time=NOW, inspector=None, challenge=CHALLENGE):
    return asyncio.run(issue_host_runtime_receipt_v2(
        target=TARGET, release_record=release_record(sha),
        inspector=inspector or DockerFixture(),
        release_key=RELEASE_KEY, host_key=HOST_KEY,
        challenge=challenge, now=time,
    ))


def git_receipt(checkout: Path, *, now=NOW, observed=NOW,
                challenge=CHALLENGE, signing_key=GIT_KEY):
    observer = GitCheckoutReadOnlyObserver(
        checkout_root=checkout, clock=lambda: observed,
    )
    return issue_git_checkout_witness(
        observer=observer, target=TARGET, signing_key=signing_key,
        challenge=challenge, now=now,
    )


def verify(checkout_receipt, *, challenge=CHALLENGE, key=GIT_KEY,
           target=TARGET, now=NOW):
    return verify_git_checkout_witness(
        checkout_receipt, verification_key=key, target=target,
        expected_challenge=challenge, now=now,
    )


def bundle(checkout: Path, *, signed_git=None, signed_host=None,
           expected=None, now=NOW, host_key=HOST_KEY,
           git_key=GIT_KEY, challenge=CHALLENGE):
    commit = isolated_git(checkout, "rev-parse", "HEAD")
    git = signed_git if signed_git is not None else git_receipt(checkout)
    host = signed_host if signed_host is not None else host_receipt(commit)
    return inspect_signed_host_checkout_bundle(
        signed_host=host, signed_checkout=git,
        runtime_host_key=host_key, git_checkout_key=git_key,
        target=TARGET, intent=expected if expected is not None else intent(commit),
        expected_challenge=challenge, now=now,
    )


def deny_witness(code, action):
    with pytest.raises(GitCheckoutWitnessError) as issue:
        action()
    assert issue.value.code == code
    assert CHALLENGE not in str(issue.value)
    assert GIT_KEY.decode() not in str(issue.value)


def deny_bundle(code, action):
    with pytest.raises(HostEvidenceBundleError) as issue:
        action()
    assert issue.value.code == code
    assert CHALLENGE not in str(issue.value)
    assert GIT_KEY.decode() not in str(issue.value)


def resign_checkout(claims: dict) -> SignedHostReceipt:
    # TEST ONLY: deliberately compute MAC for a forged claim to assert that
    # signature alone cannot bypass schema/identity/nonce controls.
    raw = json.dumps(claims, sort_keys=True, separators=(",", ":")).encode()
    mac = hmac.new(GIT_KEY, CHECKOUT_DOMAIN + raw, hashlib.sha256).hexdigest()
    return SignedHostReceipt(raw, mac)


def test_real_git_observation_is_signed_and_bound_to_exact_nonce(checkout):
    receipt = git_receipt(checkout)
    expected_head = isolated_git(checkout, "rev-parse", "HEAD")
    actual = verify(receipt)
    claims = json.loads(receipt.body)
    assert claims["version"] == 1
    assert claims["repository"] == "roberiooliveiradev/delpi-central"
    assert claims["container_name"] == TARGET.container_name
    assert claims["compose_project"] == TARGET.compose_project
    assert claims["observation_scope"] == "tracked_and_untracked_nonignored"
    assert claims["challenge"] == CHALLENGE
    assert actual.head_sha == expected_head
    assert actual.branch == "main"
    assert actual.observed_clean is True
    assert actual.challenge_sha256 == HASH
    assert actual.receipt_sha256 == hashlib.sha256(receipt.body).hexdigest()
    assert actual.signature_verified and actual.challenge_bound
    assert not actual.checkout_trust_approved
    assert not actual.rollback_ready
    assert not actual.challenge_consumed
    assert not actual.prepare_eligible


def test_genuinely_signed_dirty_or_feature_branch_remains_an_observation(checkout):
    (checkout / "untracked.txt").write_text("test only", encoding="utf-8")
    observation = verify(git_receipt(checkout))
    assert not observation.observed_clean
    (checkout / "untracked.txt").unlink()
    isolated_git(checkout, "switch", "-q", "-c", "feat/test")
    observation = verify(git_receipt(checkout))
    assert observation.branch == "feat/test"
    assert observation.observed_clean
    assert not observation.prepare_eligible


def test_combined_runtime_and_checkout_receipts_are_always_blocked(checkout):
    report = bundle(checkout)
    assert report.status == "blocked"
    assert report.environment == TARGET.environment
    assert report.service_id == TARGET.service_id
    assert report.observed_base_commit_sha == isolated_git(checkout, "rev-parse", "HEAD")
    assert report.checkout_head_sha == report.observed_base_commit_sha
    assert report.observed_base_image_id == IMAGE
    assert report.checkout_observed_clean is True
    assert report.challenge_sha256 == HASH
    assert report.runtime_receipt_sha256 != report.checkout_receipt_sha256
    for required in (
        "OCI_CI_RELEASE_NOT_REVERIFIED",
        "OCI_CHECKOUT_NOT_ATTESTED",
        "OCI_MIGRATIONS_NOT_ATTESTED",
        "OCI_ROLLBACK_NOT_ATTESTED",
        "OCI_CHALLENGE_NOT_CONSUMED",
        "OCI_CORE_AUTHORIZATION_MISSING",
        "GIT_COLLECTOR_IDENTITY_NOT_ATTESTED",
        "GIT_IGNORED_FILES_NOT_MEASURED",
        "GIT_FILESYSTEM_SNAPSHOT_NOT_ATOMIC",
    ):
        assert required in report.blocks
    assert not report.checkout_trust_approved
    assert not report.challenge_consumed
    assert not report.prepare_eligible
    assert not report.migrations_safe
    assert not report.rollback_ready
    assert not hasattr(report, "approved")
    assert not hasattr(report, "candidate")


def test_dirty_and_other_branch_signatures_are_not_granted_prepare(checkout):
    (checkout / "tracked.txt").write_text("modified test\n", encoding="utf-8")
    dirty = bundle(checkout)
    assert "GIT_CHECKOUT_DIRTY" in dirty.blocks
    (checkout / "tracked.txt").write_text("verified isolated test\n", encoding="utf-8")
    isolated_git(checkout, "switch", "-q", "-c", "feat/test")
    branch = bundle(checkout)
    assert "GIT_CHECKOUT_BRANCH_NOT_MAIN" in branch.blocks
    assert branch.status == "blocked"


def test_runtime_checkout_commit_difference_is_detected_even_when_mac_valid(checkout):
    sha = isolated_git(checkout, "rev-parse", "HEAD")
    altered = "0" * 40 if sha != "0" * 40 else "1" * 40
    host = host_receipt(altered)
    report = bundle(checkout, signed_host=host, expected=intent(altered))
    assert "GIT_CHECKOUT_RUNTIME_COMMIT_DRIFT" in report.blocks
    assert "GIT_CHECKOUT_EXPECTED_BASE_COMMIT_DRIFT" in report.blocks
    assert report.status == "blocked"


def test_host_checkout_temporal_gap_is_reported_not_silently_accepted(checkout):
    git = git_receipt(checkout, observed=NOW - timedelta(seconds=45))
    report = bundle(checkout, signed_git=git)
    assert "GIT_RUNTIME_OBSERVATION_GAP" in report.blocks
    assert not report.prepare_eligible


def test_forged_or_wrong_host_mac_denies_complete_bundle(checkout):
    sha = isolated_git(checkout, "rev-parse", "HEAD")
    host = host_receipt(sha)
    corrupted = SignedHostReceipt(host.body + b" ", host.mac_hex)
    deny_bundle(
        "HOST_BUNDLE_RUNTIME_NOT_TRUSTED",
        lambda: bundle(checkout, signed_host=corrupted),
    )


def test_tampered_signed_git_receipt_denies_bundle(checkout):
    original = git_receipt(checkout)
    corrupted = SignedHostReceipt(original.body + b" ", original.mac_hex)
    deny_bundle(
        "HOST_BUNDLE_CHECKOUT_NOT_TRUSTED",
        lambda: bundle(checkout, signed_git=corrupted),
    )
    deny_witness(
        "GIT_WITNESS_SIGNATURE_INVALID",
        lambda: verify(original, key=b"wrong-unique-fixture-key-99999999999999"),
    )


def test_replay_with_different_nonce_is_rejected_by_both_signed_receipts(checkout):
    original = git_receipt(checkout)
    deny_witness(
        "GIT_WITNESS_TARGET_MISMATCH",
        lambda: verify(original, challenge="b" * 64),
    )
    deny_bundle(
        "HOST_BUNDLE_RUNTIME_NOT_TRUSTED",
        lambda: bundle(checkout, challenge="b" * 64),
    )


@pytest.mark.parametrize("field,value,code", [
    ("version", 2, "GIT_WITNESS_TARGET_MISMATCH"),
    ("version", True, "GIT_WITNESS_TARGET_MISMATCH"),
    ("repository", "attacker/other", "GIT_WITNESS_TARGET_MISMATCH"),
    ("host_id", "another-host", "GIT_WITNESS_TARGET_MISMATCH"),
    ("environment", "prod", "GIT_WITNESS_TARGET_MISMATCH"),
    ("service_id", "other", "GIT_WITNESS_TARGET_MISMATCH"),
    ("compose_project", "other", "GIT_WITNESS_TARGET_MISMATCH"),
    ("container_name", "other", "GIT_WITNESS_TARGET_MISMATCH"),
    ("challenge", "b" * 64, "GIT_WITNESS_TARGET_MISMATCH"),
    ("head_sha", "HEAD", "GIT_WITNESS_OBSERVATION_INVALID"),
    ("head_sha", "A" * 40, "GIT_WITNESS_OBSERVATION_INVALID"),
    ("branch", "", "GIT_WITNESS_OBSERVATION_INVALID"),
    ("tracked_and_untracked_clean", 1, "GIT_WITNESS_OBSERVATION_INVALID"),
    ("observation_scope", "tracked_only", "GIT_WITNESS_OBSERVATION_INVALID"),
    ("observed_at", "yesterday", "GIT_WITNESS_TIME_INVALID"),
])
def test_even_valid_mac_cannot_override_schema_or_trust_target(checkout, field, value, code):
    claims = json.loads(git_receipt(checkout).body)
    claims[field] = value
    deny_witness(code, lambda: verify(resign_checkout(claims)))


def test_added_or_missing_fields_and_duplicate_json_are_denied(checkout):
    claims = json.loads(git_receipt(checkout).body)
    deny_witness(
        "GIT_WITNESS_RECEIPT_INVALID",
        lambda: verify(resign_checkout({**claims, "can_act": True})),
    )
    missing = dict(claims)
    missing.pop("head_sha")
    deny_witness(
        "GIT_WITNESS_RECEIPT_INVALID",
        lambda: verify(resign_checkout(missing)),
    )
    text = git_receipt(checkout).body[:-1] + b',"host_id":"bad"}'
    mac = hmac.new(GIT_KEY, CHECKOUT_DOMAIN + text, hashlib.sha256).hexdigest()
    deny_witness(
        "GIT_WITNESS_RECEIPT_INVALID",
        lambda: verify(SignedHostReceipt(text, mac)),
    )


def test_same_key_cannot_sign_both_runtime_and_checkout(checkout):
    deny_bundle(
        "HOST_BUNDLE_SEPARATE_KEYS_REQUIRED",
        lambda: bundle(checkout, git_key=HOST_KEY),
    )
    deny_bundle(
        "HOST_BUNDLE_SEPARATE_KEYS_REQUIRED",
        lambda: bundle(checkout, host_key=b"short"),
    )


def test_expired_and_future_dated_signed_git_observations_are_denied(checkout):
    receipt = git_receipt(checkout)
    deny_witness(
        "GIT_WITNESS_OBSERVATION_STALE",
        lambda: verify(receipt, now=NOW + timedelta(seconds=91)),
    )
    deny_witness(
        "GIT_WITNESS_OBSERVATION_STALE",
        lambda: verify(receipt, now=NOW - timedelta(seconds=6)),
    )
    deny_witness(
        "GIT_WITNESS_OBSERVATION_STALE",
        lambda: git_receipt(checkout, observed=NOW - timedelta(seconds=91)),
    )


@pytest.mark.parametrize("challenge", ["bad", "A" * 64, None])
def test_signer_rejects_bad_nonce_without_running_git(checkout, challenge):
    deny_witness(
        "GIT_WITNESS_NOT_CONFIGURED",
        lambda: git_receipt(checkout, challenge=challenge),
    )


@pytest.mark.parametrize("key", [b"short", "a-text-secret", None])
def test_signer_rejects_invalid_secret_key(checkout, key):
    deny_witness(
        "GIT_WITNESS_NOT_CONFIGURED",
        lambda: git_receipt(checkout, signing_key=key),
    )


def test_signer_does_not_swallow_a_git_inspection_failure_as_clean(checkout):
    outside = checkout / "missing"
    fake = GitCheckoutReadOnlyObserver(checkout_root=outside, clock=lambda: NOW)
    deny_witness(
        "GIT_WITNESS_OBSERVATION_UNAVAILABLE",
        lambda: issue_git_checkout_witness(
            observer=fake, target=TARGET, signing_key=GIT_KEY,
            challenge=CHALLENGE, now=NOW,
        ),
    )


def test_unrelated_runtime_and_git_keys_cannot_cross_verify_receipts(checkout):
    sha = isolated_git(checkout, "rev-parse", "HEAD")
    host = host_receipt(sha)
    witness = git_receipt(checkout)
    deny_witness(
        "GIT_WITNESS_SIGNATURE_INVALID",
        lambda: verify(host),
    )
    deny_bundle(
        "HOST_BUNDLE_CHECKOUT_NOT_TRUSTED",
        lambda: bundle(checkout, signed_git=host, signed_host=host),
    )
    deny_bundle(
        "HOST_BUNDLE_RUNTIME_NOT_TRUSTED",
        lambda: bundle(checkout, signed_host=witness, signed_git=witness),
    )


def test_git_receipt_was_never_a_database_write_or_deployment_ticket(checkout):
    proof = verify(git_receipt(checkout))
    result = bundle(checkout)
    assert proof.checkout_trust_approved is False
    assert proof.challenge_consumed is False
    assert result.prepare_eligible is False
    for path in (
        Path(__file__).resolve().parents[1] / "linux_ops_mcp/deploy_git_checkout_witness.py",
        Path(__file__).resolve().parents[1] / "linux_ops_mcp/deploy_host_checkout_evidence_bundle.py",
    ):
        source = path.read_text()
        for forbidden in (
            "@router.", "@mcp.", "docker compose", "subprocess.run",
            "psycopg.connect(", "CREATE TABLE", "os.system",
        ):
            assert forbidden not in source
