"""P2.2h.2c offline approval-review contract; no DB, Core calls or deploy."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from it_portal_app.domain.atlas_deploy_approval_review import (
    ACCESS, REVIEW_VIEW, REVIEW_APPROVE,
    ApprovalReviewRejected, CoreReviewerSnapshot, PendingDeployReview,
    prepare_readonly_review,
)

NOW = datetime(2026, 11, 16, 16, 0, tzinfo=timezone.utc)
REQUESTER = "11111111-2222-4333-8444-555555555555"
REVIEWER = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"


def snapshot():
    return CoreReviewerSnapshot(
        subject=REVIEWER, principal_type="user",
        permissions=(ACCESS, REVIEW_VIEW, REVIEW_APPROVE),
        fetched_at=NOW-timedelta(seconds=3), core_available=True, active=True,
    )


def proposal():
    return PendingDeployReview(
        proposal_id="01234567-89ab-4def-8abc-0123456789ab",
        requester_subject=REQUESTER, service_id="public-hub", environment="prod",
        status="pending_approval",
        target_commit_sha="f81ddd0075de1e4ef8bb68ca58791e9c43e70759",
        signed_manifest_digest="sha256:" + "a"*64,
        base_image_id="sha256:" + "b"*64, target_image_id="sha256:" + "c"*64,
        binding_sha256="d"*64,
        created_at=NOW-timedelta(minutes=1),
        expires_at=NOW+timedelta(minutes=9), revoked=False, approved_by=None,
    )


def check(actor=None, target=None, enabled=True, at=NOW):
    return prepare_readonly_review(
        actor=actor if actor is not None else snapshot(),
        proposal=target if target is not None else proposal(),
        now=at, backend_policy_enabled=enabled,
    )


def denied(code, *, actor=None, target=None, enabled=True, at=NOW):
    with pytest.raises(ApprovalReviewRejected) as exc:
        check(actor=actor, target=target, enabled=enabled, at=at)
    assert exc.value.code == code


def test_default_denies_even_if_caller_constructs_valid_objects():
    denied("ATLAS_APPROVAL_DISABLED", enabled=False)
    denied("ATLAS_APPROVAL_DISABLED", enabled="true")


def test_review_passes_only_as_non_authorizing_candidate():
    outcome = check()
    assert outcome.state == "review_candidate_only"
    assert outcome.binding_sha256 == proposal().binding_sha256
    assert outcome.approval_enabled is False
    assert outcome.execution_enabled is False
    assert outcome.manual_deploy_blocked is False


@pytest.mark.parametrize("changes,reason", [
    ({"principal_type": "service"}, "ATLAS_CORE_IDENTITY_DENIED"),
    ({"principal_type": "bot"}, "ATLAS_CORE_IDENTITY_DENIED"),
    ({"subject": "nobody"}, "ATLAS_CORE_IDENTITY_DENIED"),
    ({"subject": REQUESTER}, "ATLAS_SELF_APPROVAL_DENIED"),
    ({"active": False}, "ATLAS_CORE_IDENTITY_DENIED"),
    ({"core_available": False}, "ATLAS_CORE_IDENTITY_DENIED"),
    ({"core_available": "yes"}, "ATLAS_CORE_IDENTITY_DENIED"),
    ({"permissions": (ACCESS, REVIEW_VIEW)}, "ATLAS_CORE_PERMISSION_DENIED"),
    ({"permissions": (ACCESS, REVIEW_APPROVE)}, "ATLAS_CORE_PERMISSION_DENIED"),
    ({"permissions": (REVIEW_VIEW, REVIEW_APPROVE)}, "ATLAS_CORE_PERMISSION_DENIED"),
    ({"permissions": (ACCESS, REVIEW_VIEW, "it-portal.servers.manage")}, "ATLAS_CORE_PERMISSION_DENIED"),
    ({"permissions": "it-portal.access it-portal.deploy.view it-portal.deploy.approve"}, "ATLAS_CORE_PERMISSION_DENIED"),
    ({"fetched_at": NOW-timedelta(seconds=61)}, "ATLAS_CORE_STALE"),
    ({"fetched_at": NOW+timedelta(seconds=6)}, "ATLAS_CORE_STALE"),
    ({"fetched_at": NOW.replace(tzinfo=None)}, "ATLAS_CORE_STALE"),
])
def test_core_identity_or_permission_denials(changes, reason):
    denied(reason, actor=replace(snapshot(), **changes))


@pytest.mark.parametrize("changes,reason", [
    ({"proposal_id": "not-a-uuid"}, "ATLAS_PROPOSAL_ID_INVALID"),
    ({"requester_subject": "service-account"}, "ATLAS_PROPOSAL_ID_INVALID"),
    ({"service_id": "gateway"}, "ATLAS_REVIEW_TARGET_DENIED"),
    ({"environment": "../prod"}, "ATLAS_REVIEW_TARGET_DENIED"),
    ({"target_commit_sha": "short"}, "ATLAS_REVIEW_BINDING_INVALID"),
    ({"signed_manifest_digest": "sha256:short"}, "ATLAS_REVIEW_BINDING_INVALID"),
    ({"target_image_id": "sha256:" + "b"*64}, "ATLAS_REVIEW_BINDING_INVALID"),
    ({"base_image_id": "sha256:" + "z"*64}, "ATLAS_REVIEW_BINDING_INVALID"),
    ({"binding_sha256": "x"*64}, "ATLAS_REVIEW_BINDING_INVALID"),
    ({"status": "approved"}, "ATLAS_REVIEW_NOT_PENDING"),
    ({"status": "executing"}, "ATLAS_REVIEW_NOT_PENDING"),
    ({"revoked": True}, "ATLAS_REVIEW_NOT_PENDING"),
    ({"approved_by": REVIEWER}, "ATLAS_REVIEW_NOT_PENDING"),
    ({"created_at": NOW.replace(tzinfo=None)}, "ATLAS_REVIEW_TIME_INVALID"),
    ({"created_at": NOW+timedelta(seconds=6)}, "ATLAS_REVIEW_EXPIRED"),
    ({"expires_at": NOW}, "ATLAS_REVIEW_EXPIRED"),
    ({"expires_at": NOW+timedelta(minutes=20)}, "ATLAS_REVIEW_EXPIRED"),
])
def test_proposal_invariants_fail_closed(changes, reason):
    denied(reason, target=replace(proposal(), **changes))


def test_cross_environment_remains_preview_only():
    outcome = check(target=replace(proposal(), environment="hml"))
    assert outcome.state == "review_candidate_only"
    assert outcome.execution_enabled is False


def test_policy_does_not_expose_mutating_apis():
    from pathlib import Path
    source = (Path(__file__).resolve().parents[2]
              / "it_portal_app/domain/atlas_deploy_approval_review.py").read_text()
    for forbidden in ("docker compose", "docker pull", "subprocess", "requests.post",
                      "httpx.post", "psycopg", "asyncpg", "os.system", "ssh "):
        assert forbidden not in source
