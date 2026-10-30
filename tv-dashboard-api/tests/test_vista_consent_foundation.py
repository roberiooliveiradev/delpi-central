"""VISTA consent foundation (SEMANTIC_TOOLS_V1, D-5).

Covers the challenge lifecycle (PENDING→APPROVED→CONSUMED), step-up
token freshness (``iat >= challenge.created_at``), actor/plan/target
binding, single-use consumption, target_echo anti-wrong-object checks,
and coexistence with the legacy ``confirmed=true`` gate (which is never
treated as human-consent proof on the semantic surface).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pytest

from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.proposal import create_proposal
from tv_app.application.gpt_actions.proposal_store import (
    get_proposal_store,
    reset_proposal_store_for_tests,
)
from tv_app.application.gpt_actions.vista_consent_service import (
    VistaConsentService,
    _target_ref,
    assert_step_up_token,
    confirm_op_names,
)
from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
    InMemoryIdempotencyRepository,
)
from tv_app.infrastructure.persistence.repositories.vista_consent_challenge_repository import (
    InMemoryVistaConsentChallengeRepository,
)

ACTOR = "actor-1"
OTHER = "actor-2"
PLAYLIST_ID = str(uuid.uuid4())
SLIDE_ID = str(uuid.uuid4())


def _ops():
    return [{"op": "delete_slide", "slideId": SLIDE_ID}]


def _catalog_version() -> str:
    from tv_app.application.services.data.presentation_ops_content_service import (
        PresentationOpsContentService,
    )

    return PresentationOpsContentService.catalog_version()


def _proposal(*, actor=ACTOR, policy="confirm", ops=None):
    proposal = create_proposal(
        actor_id=actor,
        target={"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
        ops=ops if ops is not None else _ops(),
        operation_names=["delete_slide"],
        catalog_version=_catalog_version(),
        base_revision=3,
        risk="destructive",
        confirmation_policy=policy,
    )
    return proposal


def _svc(repo=None):
    return VistaConsentService(
        challenges=repo or InMemoryVistaConsentChallengeRepository()
    )


def _fresh_claims(challenge, *, sub=ACTOR):
    iat = int(challenge["created_at"].timestamp()) + 5
    return {"sub": sub, "iat": iat, "jti": str(uuid.uuid4())}


@pytest.fixture(autouse=True)
def _clean_store():
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


@pytest.fixture
def stored():
    proposal = _proposal()
    handle = get_proposal_store().put(proposal)
    return proposal, handle


@pytest.fixture
def consent_repo():
    return InMemoryVistaConsentChallengeRepository()


@pytest.fixture
def svc(consent_repo):
    return _svc(consent_repo)


# ---------------------------------------------------------------------------
# Step-up token proof
# ---------------------------------------------------------------------------


def test_step_up_token_accepts_fresh_iat():
    challenge = {"created_at": datetime.now(timezone.utc)}
    proof = assert_step_up_token(
        {"sub": ACTOR, "iat": int(datetime.now(timezone.utc).timestamp()) + 2},
        prepared_at=challenge["created_at"],
    )
    assert proof["token_sub"] == ACTOR


def test_step_up_token_rejects_stale_iat():
    prepared = datetime.now(timezone.utc)
    stale = int((prepared - timedelta(minutes=5)).timestamp())
    with pytest.raises(GptActionsError) as exc:
        assert_step_up_token({"sub": ACTOR, "iat": stale}, prepared_at=prepared)
    assert exc.value.code == "STEP_UP_TOKEN_STALE"
    assert exc.value.status_code == 403


def test_step_up_token_rejects_missing_and_future_iat():
    prepared = datetime.now(timezone.utc)
    with pytest.raises(GptActionsError) as exc:
        assert_step_up_token({"sub": ACTOR}, prepared_at=prepared)
    assert exc.value.code == "STEP_UP_TOKEN_STALE"
    future = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    with pytest.raises(GptActionsError) as exc2:
        assert_step_up_token(
            {"sub": ACTOR, "iat": future}, prepared_at=prepared
        )
    assert exc2.value.code == "STEP_UP_TOKEN_STALE"


# ---------------------------------------------------------------------------
# Plan binding helpers
# ---------------------------------------------------------------------------


def test_confirm_op_names_and_target_ref():
    proposal = _proposal()
    names = confirm_op_names(proposal)
    assert names == ["delete_slide"]
    ref = _target_ref(proposal, names)
    assert ref == f"{PLAYLIST_ID}|delete_slide:{SLIDE_ID}"


def test_confirm_op_names_empty_for_direct_policy():
    proposal = _proposal(policy="direct", ops=[{"op": "add_blank_slide"}])
    assert confirm_op_names(proposal) == []


# ---------------------------------------------------------------------------
# Issue (PREPARE)
# ---------------------------------------------------------------------------


def test_issue_mints_pending_challenge_bound_to_plan(stored, svc):
    proposal, _ = stored
    challenge = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    assert challenge["status"] == "PENDING"
    assert challenge["actor_sub"] == ACTOR
    assert challenge["proposal_id"] == proposal.proposal_id
    assert challenge["plan_hash"] == proposal.content_hash
    assert challenge["origin"] == "gpt_actions"


def test_issue_is_idempotent_per_proposal(stored, svc):
    proposal, _ = stored
    first = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="mcp"
    )
    second = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="mcp"
    )
    assert first["challenge_id"] == second["challenge_id"]


# ---------------------------------------------------------------------------
# Consent view (human channel read)
# ---------------------------------------------------------------------------


def test_summary_returns_sealed_view(stored, svc):
    proposal, _ = stored
    svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    view = svc.summary_for_consent(
        proposal_id=proposal.proposal_id, actor_sub=ACTOR
    )
    assert view["consentable"] is True
    assert view["confirmOps"] == ["delete_slide"]
    assert view["challenge"]["status"] == "PENDING"


def test_summary_rejects_wrong_actor_and_unknown(stored, svc):
    proposal, _ = stored
    svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    with pytest.raises(GptActionsError) as exc:
        svc.summary_for_consent(
            proposal_id=proposal.proposal_id, actor_sub=OTHER
        )
    assert exc.value.code == "CONSENT_MISMATCH"
    with pytest.raises(GptActionsError) as exc2:
        svc.summary_for_consent(proposal_id="nope", actor_sub=ACTOR)
    assert exc2.value.code == "PROPOSAL_NOT_FOUND"


# ---------------------------------------------------------------------------
# Approve (human channel write)
# ---------------------------------------------------------------------------


def test_approve_happy_path_records_consent(stored, svc):
    proposal, _ = stored
    challenge = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    result = svc.approve(
        challenge_id=str(challenge["challenge_id"]),
        actor_sub=ACTOR,
        token_claims=_fresh_claims(challenge),
    )
    assert result["challenge"]["status"] == "APPROVED"
    assert result["consentArtifact"] == str(challenge["challenge_id"])
    record = result["consentRecord"]
    assert record["confirmed_by"] == ACTOR
    assert record["plan_hash"] == proposal.content_hash


def test_approve_rejects_wrong_actor(stored, svc):
    proposal, _ = stored
    challenge = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    with pytest.raises(GptActionsError) as exc:
        svc.approve(
            challenge_id=str(challenge["challenge_id"]),
            actor_sub=OTHER,
            token_claims=_fresh_claims(challenge, sub=OTHER),
        )
    assert exc.value.code == "CONSENT_MISMATCH"


def test_approve_rejects_token_sub_mismatch(stored, svc):
    proposal, _ = stored
    challenge = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    with pytest.raises(GptActionsError) as exc:
        svc.approve(
            challenge_id=str(challenge["challenge_id"]),
            actor_sub=ACTOR,
            token_claims=_fresh_claims(challenge, sub=OTHER),
        )
    assert exc.value.code == "CONSENT_MISMATCH"


def test_approve_rejects_stale_token(stored, svc):
    proposal, _ = stored
    challenge = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    stale = {
        "sub": ACTOR,
        "iat": int(challenge["created_at"].timestamp()) - 300,
    }
    with pytest.raises(GptActionsError) as exc:
        svc.approve(
            challenge_id=str(challenge["challenge_id"]),
            actor_sub=ACTOR,
            token_claims=stale,
        )
    assert exc.value.code == "STEP_UP_TOKEN_STALE"


def test_approve_rejects_reuse_and_unknown(stored, svc):
    proposal, _ = stored
    challenge = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    svc.approve(
        challenge_id=str(challenge["challenge_id"]),
        actor_sub=ACTOR,
        token_claims=_fresh_claims(challenge),
    )
    with pytest.raises(GptActionsError) as exc:
        svc.approve(
            challenge_id=str(challenge["challenge_id"]),
            actor_sub=ACTOR,
            token_claims=_fresh_claims(challenge),
        )
    assert exc.value.code == "CONSENT_CHALLENGE_CONSUMED"
    with pytest.raises(GptActionsError) as exc2:
        svc.approve(
            challenge_id=str(uuid.uuid4()),
            actor_sub=ACTOR,
            token_claims=_fresh_claims(challenge),
        )
    assert exc2.value.code == "CONSENT_CHALLENGE_NOT_FOUND"


def test_approve_rejects_expired(stored, svc, consent_repo):
    proposal, _ = stored
    challenge = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    row = consent_repo._rows[str(challenge["challenge_id"])]
    row["expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    with pytest.raises(GptActionsError) as exc:
        svc.approve(
            challenge_id=str(challenge["challenge_id"]),
            actor_sub=ACTOR,
            token_claims=_fresh_claims(challenge),
        )
    assert exc.value.code == "CONSENT_CHALLENGE_EXPIRED"


# ---------------------------------------------------------------------------
# Verify + consume (COMMIT binding)
# ---------------------------------------------------------------------------


def _approved(svc, proposal, actor=ACTOR):
    challenge = svc.issue_for_proposal(
        proposal=proposal, actor_sub=actor, origin="gpt_actions"
    )
    svc.approve(
        challenge_id=str(challenge["challenge_id"]),
        actor_sub=actor,
        token_claims=_fresh_claims(challenge, sub=actor),
    )
    return challenge


def test_verify_requires_artifact_on_semantic_surface(stored, svc):
    proposal, _ = stored
    with pytest.raises(GptActionsError) as exc:
        svc.verify_for_commit(
            proposal=proposal,
            actor_sub=ACTOR,
            consent_artifact=None,
            required=True,
        )
    assert exc.value.code == "CONFIRMATION_REQUIRED"
    # Legacy path without artifact stays out of the consent flow.
    assert (
        svc.verify_for_commit(
            proposal=proposal,
            actor_sub=ACTOR,
            consent_artifact=None,
            required=False,
        )
        is None
    )


def test_verify_rejects_pending_unknown_and_binding_mismatch(stored, svc):
    proposal, _ = stored
    pending = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    with pytest.raises(GptActionsError) as exc:
        svc.verify_for_commit(
            proposal=proposal,
            actor_sub=ACTOR,
            consent_artifact=str(pending["challenge_id"]),
            required=True,
        )
    assert exc.value.code == "CONFIRMATION_REQUIRED"
    with pytest.raises(GptActionsError) as exc2:
        svc.verify_for_commit(
            proposal=proposal,
            actor_sub=ACTOR,
            consent_artifact=str(uuid.uuid4()),
            required=True,
        )
    assert exc2.value.code == "CONSENT_CHALLENGE_NOT_FOUND"

    other_proposal = _proposal(actor=OTHER)
    get_proposal_store().put(other_proposal)
    foreign = _approved(svc, other_proposal, actor=OTHER)
    with pytest.raises(GptActionsError) as exc3:
        svc.verify_for_commit(
            proposal=proposal,
            actor_sub=ACTOR,
            consent_artifact=str(foreign["challenge_id"]),
            required=True,
        )
    assert exc3.value.code == "CONSENT_MISMATCH"


def test_verify_and_consume_single_use(stored, svc):
    proposal, _ = stored
    challenge = _approved(svc, proposal)
    verified = svc.verify_for_commit(
        proposal=proposal,
        actor_sub=ACTOR,
        consent_artifact=str(challenge["challenge_id"]),
        required=True,
    )
    assert verified["status"] == "APPROVED"
    svc.consume_for_commit(
        challenge=verified,
        proposal_id=proposal.proposal_id,
        actor_sub=ACTOR,
    )
    with pytest.raises(GptActionsError) as exc:
        svc.verify_for_commit(
            proposal=proposal,
            actor_sub=ACTOR,
            consent_artifact=str(challenge["challenge_id"]),
            required=True,
        )
    assert exc.value.code == "CONSENT_CHALLENGE_CONSUMED"


# ---------------------------------------------------------------------------
# Commit service integration (gate before execution)
# ---------------------------------------------------------------------------


def _commit_service(repo):
    writes = MagicMock(
        spec=[
            "assert_expected_revision",
            "get_revision",
            "delete_slide",
            "list_slides",
            "list_sections",
            "get_playlist",
        ]
    )
    writes.get_revision.return_value = 4
    writes.list_slides.return_value = []
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": PLAYLIST_ID}
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(
        can_edit=True, can_read=True, level="owner"
    )
    patch_svc = MagicMock()
    patch_svc.preview.return_value = {"confirmationPolicy": "confirm"}
    commit = TvGptCommitService(
        writes=writes,
        idempotency=InMemoryIdempotencyRepository(),
        access=access,
        consent=_svc(repo),
        patch=patch_svc,
    )
    return commit, writes


def _user():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.read", "tv-dashboard.write"],
        roles=[],
        groups=[],
        id=ACTOR,
        email=f"{ACTOR}@delpi.local",
    )


def test_commit_with_approved_artifact_executes_and_consumes(
    stored, consent_repo
):
    proposal, handle = stored
    svc = _svc(consent_repo)
    challenge = _approved(svc, proposal)
    echo = _target_ref(proposal, confirm_op_names(proposal))
    commit, writes = _commit_service(consent_repo)
    result = commit.commit(
        user=_user(),
        actor_id=ACTOR,
        proposal_handle=handle,
        confirmation={
            "consent_artifact": str(challenge["challenge_id"]),
            "target_echo": echo,
        },
        idempotency_key="consent-ok-1",
    )
    assert result.get("status") == "VERIFIED"
    writes.delete_slide.assert_called_once()
    row = consent_repo.get_by_id(challenge_id=str(challenge["challenge_id"]))
    assert row["status"] == "CONSUMED"


def test_commit_semantic_surface_rejects_confirmed_only(stored, consent_repo):
    _, handle = stored
    commit, writes = _commit_service(consent_repo)
    with pytest.raises(GptActionsError) as exc:
        commit.commit(
            user=_user(),
            actor_id=ACTOR,
            proposal_handle=handle,
            confirmation={"confirmed": True},
            idempotency_key="consent-missing-1",
            consent_required=True,
        )
    assert exc.value.code == "CONFIRMATION_REQUIRED"
    writes.delete_slide.assert_not_called()


def test_commit_rejects_mismatched_target_echo(stored, consent_repo):
    proposal, handle = stored
    svc = _svc(consent_repo)
    challenge = _approved(svc, proposal)
    commit, writes = _commit_service(consent_repo)
    with pytest.raises(GptActionsError) as exc:
        commit.commit(
            user=_user(),
            actor_id=ACTOR,
            proposal_handle=handle,
            confirmation={
                "consent_artifact": str(challenge["challenge_id"]),
                "target_echo": "wrong-target",
            },
            idempotency_key="consent-echo-1",
        )
    assert exc.value.code == "CONFIRMATION_MISMATCH"
    writes.delete_slide.assert_not_called()


def test_commit_rejects_pending_and_foreign_artifacts(stored, consent_repo):
    proposal, handle = stored
    svc = _svc(consent_repo)
    pending = svc.issue_for_proposal(
        proposal=proposal, actor_sub=ACTOR, origin="gpt_actions"
    )
    commit, writes = _commit_service(consent_repo)
    with pytest.raises(GptActionsError) as exc:
        commit.commit(
            user=_user(),
            actor_id=ACTOR,
            proposal_handle=handle,
            confirmation={"consent_artifact": str(pending["challenge_id"])},
            idempotency_key="consent-pending-1",
        )
    assert exc.value.code == "CONFIRMATION_REQUIRED"

    other_proposal = _proposal(actor=OTHER)
    get_proposal_store().put(other_proposal)
    foreign = _approved(svc, other_proposal, actor=OTHER)
    with pytest.raises(GptActionsError) as exc2:
        commit.commit(
            user=_user(),
            actor_id=ACTOR,
            proposal_handle=handle,
            confirmation={"consent_artifact": str(foreign["challenge_id"])},
            idempotency_key="consent-foreign-1",
        )
    assert exc2.value.code == "CONSENT_MISMATCH"
    writes.delete_slide.assert_not_called()


def test_commit_legacy_confirmed_still_works_without_artifact(
    stored, consent_repo
):
    """Coexistence: gpt_* callers keep the confirmed=true gate — the
    consent artifact is additive, not a breaking change."""
    _, handle = stored
    commit, writes = _commit_service(consent_repo)
    result = commit.commit(
        user=_user(),
        actor_id=ACTOR,
        proposal_handle=handle,
        confirmation=True,
        idempotency_key="legacy-ok-1",
    )
    assert result.get("status") == "VERIFIED"
    writes.delete_slide.assert_called_once()


# ---------------------------------------------------------------------------
# PREPARE issues the challenge (dispatch integration)
# ---------------------------------------------------------------------------


def test_preview_change_issues_consent_challenge_for_confirm_ops(
    consent_repo,
):
    from tv_app.application.gpt_actions.dispatch_service import (
        GptActionsDispatchService,
    )
    from tv_app.application.services.data.presentation_mutation import (
        PresentationPatchService,
    )

    svc = _svc(consent_repo)
    writes = MagicMock()
    commit = TvGptCommitService(
        writes=writes, idempotency=InMemoryIdempotencyRepository()
    )
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=commit, consent=svc
    )
    dispatch._access.resolve = MagicMock(
        return_value=SimpleNamespace(
            can_edit=True, can_read=True, level="owner"
        )
    )
    preview_result = {
        "appliedOps": ["delete_slide"],
        "orderedOps": _ops(),
        "baseRevision": 3,
        "risk": "destructive",
        "confirmationPolicy": "confirm",
        "sideEffectHints": [],
        "diff": {},
        "fingerprint": "fp-consent",
    }
    with patch.object(
        PresentationPatchService, "preview", return_value=preview_result
    ):
        payload = dispatch.preview_change(
            user=_user(),
            target={"playlistId": PLAYLIST_ID},
            ops=_ops(),
            catalog_version="v-test",
            authorization=None,
        )
    assert payload["confirmationPolicy"] == "confirm"
    assert payload["requiredConfirmation"] == ["delete_slide"]
    challenge = payload.get("consentChallenge")
    assert challenge is not None
    assert challenge["status"] == "PENDING"
    assert challenge["origin"] == "gpt_actions"
    assert "confirmationUnavailable" not in payload


# ---------------------------------------------------------------------------
# MCP commit envelope (consent fields reach commit_change)
# ---------------------------------------------------------------------------


def test_mcp_commit_proposal_forwards_consent_fields():
    from delpi_auth.request_context import (
        reset_current_user,
        reset_request_authorization,
        set_current_user,
        set_request_authorization,
    )
    from tv_app.interface.mcp import tool_bridge

    dispatch = MagicMock()
    dispatch.commit_change.return_value = {"status": "VERIFIED"}
    tok_u = set_current_user(_user())
    tok_a = set_request_authorization("Bearer test")
    try:
        with patch.object(tool_bridge, "_dispatch", dispatch):
            result = tool_bridge.tool_commit_proposal(
                proposal_handle="h",
                idempotency_key="k",
                confirmation=False,
                consent_artifact="challenge-uuid",
                target_echo="t-ref",
            )
    finally:
        reset_current_user(tok_u)
        reset_request_authorization(tok_a)
    assert result.is_error is False
    confirmation = dispatch.commit_change.call_args.kwargs["confirmation"]
    assert confirmation == {
        "confirmed": False,
        "consent_artifact": "challenge-uuid",
        "target_echo": "t-ref",
    }
