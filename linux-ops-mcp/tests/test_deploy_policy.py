"""Offline P2.1 preview policy tests: never touch runtime, auth or Docker."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from linux_ops_mcp.deploy_policy import (
    DeploymentPolicy, DeploymentTarget, TrustedDeployEvidence,
    evaluate_deployment_preview,
)

NOW = datetime(2026, 11, 15, 12, 0, tzinfo=timezone.utc)
OLD = "0" * 40
NEW = "a" * 40
REQUEST_ID = "01234567-89ab-4def-8abc-0123456789ab"


def inputs(**changes):
    policy = DeploymentPolicy(enabled=True, targets=(DeploymentTarget("it-portal-api", "hml", True),))
    evidence = TrustedDeployEvidence(
        approved_commit_sha=NEW, deployed_commit_sha=OLD, ci_passed=True,
        approved_ref_contains_commit=True, checkout_clean=True,
        health_passed=True, migrations_safe=True, rollback_ready=True,
        checked_at=NOW,
    )
    values = dict(
        policy=policy, environment="hml", service_id="it-portal-api",
        commit_sha=NEW, requester_subject="user-001",
        request_id=REQUEST_ID, evidence=evidence, now=NOW,
    )
    values.update(changes)
    return values


def block(**changes):
    result = evaluate_deployment_preview(**inputs(**changes))
    assert result.status == "blocked"
    assert result.proposal_hash is None
    assert result.expires_at is None
    return result.blocks


def test_deny_by_default():
    assert "POLICY_DISABLED" in block(policy=DeploymentPolicy())
    assert "TARGET_NOT_ALLOWLISTED" in block(policy=DeploymentPolicy(enabled=True))


def test_hml_eligible_preview_is_not_approval_or_execution():
    result = evaluate_deployment_preview(**inputs())
    assert result.status == "eligible_for_preparation"
    assert len(result.proposal_hash) == 64
    assert result.expires_at == (NOW + timedelta(minutes=10)).isoformat()
    assert not hasattr(result, "execute")
    assert not hasattr(result, "approved")


def test_hash_is_deterministic_and_request_scoped():
    a = evaluate_deployment_preview(**inputs())
    b = evaluate_deployment_preview(**inputs())
    c = evaluate_deployment_preview(**inputs(request_id=str(uuid4())))
    assert a.proposal_hash == b.proposal_hash
    assert a.proposal_hash != c.proposal_hash


@pytest.mark.parametrize("service", ["api;rm -rf /", "../it-portal-api", "", "it_portal_api", "It-portal-api"])
def test_reject_injected_or_invalid_service_id(service):
    assert "SERVICE_INVALID" in block(service_id=service)


@pytest.mark.parametrize("sha", ["main", "a" * 39, "A" * 40, "a" * 40 + "x", "a" * 39 + ";", None])
def test_require_exact_lowercase_40_hex_sha(sha):
    assert "COMMIT_SHA_INVALID" in block(commit_sha=sha)


def test_unknown_target_and_duplicate_target_fail_closed():
    assert "TARGET_NOT_ALLOWLISTED" in block(service_id="gateway")
    p = inputs()["policy"]
    p = replace(p, targets=p.targets + p.targets)
    assert "TARGET_NOT_ALLOWLISTED" in block(policy=p)


def test_production_is_locked_independently_of_allowlist():
    prod = DeploymentPolicy(enabled=True, targets=(DeploymentTarget("it-portal-api", "prod", True),))
    assert "PRODUCTION_LOCKED" in block(environment="prod", policy=prod)


def test_stale_or_future_evidence_rejected():
    ev = inputs()["evidence"]
    assert "ATTESTATION_STALE" in block(evidence=replace(ev, checked_at=NOW - timedelta(seconds=121)))
    assert "ATTESTATION_STALE" in block(evidence=replace(ev, checked_at=NOW + timedelta(seconds=6)))
    assert "ATTESTATION_STALE" in block(evidence=replace(ev, checked_at=NOW.replace(tzinfo=None)))


@pytest.mark.parametrize("changes,expected", [
    ({"ci_passed": False}, "CI_NOT_PASSED"),
    ({"ci_passed": 1}, "CI_NOT_PASSED"),
    ({"approved_ref_contains_commit": False}, "COMMIT_NOT_APPROVED"),
    ({"approved_commit_sha": OLD}, "COMMIT_NOT_APPROVED"),
    ({"checkout_clean": False}, "CHECKOUT_NOT_CLEAN"),
    ({"deployed_commit_sha": None}, "DEPLOYED_REVISION_UNVERIFIED"),
    ({"deployed_commit_sha": NEW}, "ALREADY_DEPLOYED"),
    ({"health_passed": False}, "HEALTH_NOT_PASSED"),
    ({"migrations_safe": False}, "MIGRATION_UNSAFE"),
    ({"rollback_ready": False}, "ROLLBACK_NOT_READY"),
])
def test_missing_or_invalid_proof_blocks(changes, expected):
    assert expected in block(evidence=replace(inputs()["evidence"], **changes))


def test_bad_evidence_object_and_requester_fail_closed():
    assert "ATTESTATION_MISSING" in block(evidence=None)
    assert "REQUESTER_INVALID" in block(requester_subject="sub;sudo")
    assert "REQUEST_ID_INVALID" in block(request_id="unknown")
    assert "CLOCK_INVALID" in block(now=NOW.replace(tzinfo=None))


def test_preview_result_and_policy_are_immutable():
    result = evaluate_deployment_preview(**inputs())
    with pytest.raises(FrozenInstanceError):
        result.status = "approved"
    with pytest.raises(FrozenInstanceError):
        inputs()["policy"].enabled = False


def test_false_positive_bool_flags_do_not_bypass_guards():
    ev = inputs()["evidence"]
    assert "MIGRATION_UNSAFE" in block(evidence=replace(ev, migrations_safe=1))
    assert "PRODUCTION_LOCKED" in block(
        environment="prod",
        policy=DeploymentPolicy(enabled=True, allow_prod=1,
                                targets=(DeploymentTarget("it-portal-api", "prod", True),)),
    )
