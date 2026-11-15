"""P2.2a: no external calls, purely synthetic trusted-provider evidence."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp.deploy_attestation import (
    AttestationResult, CoreProof, GithubProof, HostProof,
    WorkflowRunProof, attest_preview_evidence,
)
from linux_ops_mcp.deploy_policy import DeploymentPolicy, DeploymentTarget, evaluate_deployment_preview

NOW = datetime(2026, 11, 15, 14, tzinfo=timezone.utc)
SHA = "a" * 40
OLD = "b" * 40


def valid(**changes):
    run = WorkflowRunProof(101, 999, 1, SHA, "main", "push", "completed", "success")
    values = dict(
        environment="hml", service_id="it-portal-api", commit_sha=SHA,
        requester_subject="subject-123", required_workflow_ids=(101,),
        github=GithubProof("roberiooliveiradev/delpi-central", SHA, "main", True, (run,), NOW),
        host=HostProof("hml", "it-portal-api", "roberiooliveiradev/delpi-central",
                       OLD, True, True, True, True, NOW),
        core=CoreProof("subject-123", "user", frozenset((
            "linux_ops.deploy.view", "linux_ops.deploy.prepare",
        )), NOW), now=NOW,
    )
    values.update(changes)
    return values


def blocks(**changes):
    output = attest_preview_evidence(**valid(**changes))
    assert output.status == "blocked"
    assert output.evidence is None
    return output.blocks


def test_valid_preview_attestation_can_be_consumed_by_p21():
    a = attest_preview_evidence(**valid())
    assert a.status == "verified_for_preview_only" and a.blocks == ()
    result = evaluate_deployment_preview(
        policy=DeploymentPolicy(enabled=True, targets=(DeploymentTarget("it-portal-api", "hml", True),)),
        environment="hml", service_id="it-portal-api", commit_sha=SHA,
        requester_subject="subject-123", request_id="01234567-89ab-4def-8abc-0123456789ab",
        evidence=a.evidence, now=NOW,
    )
    assert result.status == "eligible_for_preparation"
    assert result.proposal_hash and not hasattr(a, "approve")


def test_none_everywhere_and_missing_workflows_fail_closed():
    denied = blocks(github=None, host=None, core=None, required_workflow_ids=())
    assert {"GITHUB_PROOF_MISSING", "HOST_PROOF_MISSING", "CORE_PROOF_MISSING", "CI_POLICY_MISSING"}.issubset(denied)


@pytest.mark.parametrize("kw,code", [
    (dict(environment="dev"), "ENVIRONMENT_INVALID"),
    (dict(service_id="../../db"), "SERVICE_INVALID"),
    (dict(commit_sha="main"), "COMMIT_SHA_INVALID"),
    (dict(requester_subject=""), "REQUESTER_INVALID"),
    (dict(requester_subject="bad\nuser"), "REQUESTER_INVALID"),
    (dict(now=NOW.replace(tzinfo=None)), "CLOCK_INVALID"),
    (dict(required_workflow_ids=()), "CI_POLICY_MISSING"),
    (dict(required_workflow_ids=(101, 101)), "CI_POLICY_MISSING"),
    (dict(required_workflow_ids=(True,)), "CI_POLICY_MISSING"),
    (dict(required_workflow_ids=(102,)), "CI_REQUIRED_CHECK_MISSING_OR_AMBIGUOUS"),
])
def test_input_and_ci_policy_rejections(kw, code):
    assert code in blocks(**kw)


@pytest.mark.parametrize("changes,expected", [
    ({"repository": "attacker/repo"}, "GITHUB_SOURCE_MISMATCH"),
    ({"branch": "feature"}, "GITHUB_SOURCE_MISMATCH"),
    ({"commit_sha": OLD}, "GITHUB_COMMIT_NOT_APPROVED"),
    ({"branch_contains_commit": False}, "GITHUB_COMMIT_NOT_APPROVED"),
    ({"checked_at": NOW - timedelta(seconds=121)}, "GITHUB_PROOF_STALE"),
    ({"checked_at": NOW + timedelta(seconds=6)}, "GITHUB_PROOF_STALE"),
    ({"runs": ()}, "CI_REQUIRED_CHECK_MISSING_OR_AMBIGUOUS"),
    ({"runs": None}, "CI_RUNS_MALFORMED"),
])
def test_github_proof_failures(changes, expected):
    assert expected in blocks(github=replace(valid()["github"], **changes))


@pytest.mark.parametrize("field,value", [
    ("run_id", 0), ("attempt", 0), ("head_sha", OLD), ("head_branch", "hml"),
    ("event", "pull_request"), ("status", "in_progress"), ("conclusion", "failure"),
])
def test_ci_must_be_successful_for_exact_main_sha(field, value):
    g = valid()["github"]
    assert "CI_CHECK_NOT_VERIFIED" in blocks(github=replace(g, runs=(replace(g.runs[0], **{field: value}),)))


def test_ci_duplicate_run_is_ambiguous_and_fails_closed():
    g = valid()["github"]
    assert "CI_REQUIRED_CHECK_MISSING_OR_AMBIGUOUS" in blocks(github=replace(g, runs=g.runs + g.runs))


@pytest.mark.parametrize("changes,expected", [
    ({"repository": "attacker/repo"}, "HOST_TARGET_MISMATCH"),
    ({"environment": "prod"}, "HOST_TARGET_MISMATCH"),
    ({"service_id": "gateway"}, "HOST_TARGET_MISMATCH"),
    ({"deployed_commit_sha": None}, "DEPLOYED_REVISION_UNVERIFIED"),
    ({"deployed_commit_sha": SHA}, "ALREADY_DEPLOYED"),
    ({"checkout_clean": False}, "CHECKOUT_NOT_CLEAN"),
    ({"service_healthy": False}, "HEALTH_NOT_PASSED"),
    ({"migrations_safe": False}, "MIGRATION_UNSAFE"),
    ({"rollback_ready": False}, "ROLLBACK_NOT_READY"),
    ({"checked_at": NOW - timedelta(seconds=121)}, "HOST_PROOF_STALE"),
])
def test_host_proof_must_match_reality(changes, expected):
    assert expected in blocks(host=replace(valid()["host"], **changes))


@pytest.mark.parametrize("changes,expected", [
    ({"subject": "another-user"}, "CORE_SUBJECT_MISMATCH"),
    ({"principal_type": "service"}, "CORE_SUBJECT_MISMATCH"),
    ({"permissions": frozenset()}, "CORE_PREPARE_PERMISSION_MISSING"),
    ({"permissions": frozenset({"linux_ops.deploy.prepare"})}, "CORE_PREPARE_PERMISSION_MISSING"),
    ({"permissions": None}, "CORE_PERMISSIONS_INVALID"),
    ({"checked_at": NOW - timedelta(seconds=121)}, "CORE_PROOF_STALE"),
])
def test_core_authz_needs_fresh_explicit_grants(changes, expected):
    assert expected in blocks(core=replace(valid()["core"], **changes))


def test_prod_gate_not_unlockable_from_attestation():
    a = attest_preview_evidence(**valid(environment="prod", host=replace(valid()["host"], environment="prod")))
    assert a.status == "verified_for_preview_only"
    result = evaluate_deployment_preview(
        policy=DeploymentPolicy(), environment="prod", service_id="it-portal-api", commit_sha=SHA,
        requester_subject="subject-123", request_id="01234567-89ab-4def-8abc-0123456789ab",
        evidence=a.evidence, now=NOW,
    )
    assert "PRODUCTION_LOCKED" in result.blocks
