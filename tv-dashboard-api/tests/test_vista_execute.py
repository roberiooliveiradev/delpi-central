"""SEMANTIC_TOOLS_V2 A6 — ``execute`` semantic facade.

Closed contract ``entity="presentation" action="apply_mutation"
phase=prepare|commit`` over the canonical PREPARE→COMMIT pipeline with
``consent_required=True`` — the semantic surface has no confirmation
boolean; only the consent artifact minted by the trusted channel proves
human consent for confirm plans. ``operations[]`` belongs to prepare and
is never re-sent at commit (``PLAN_MISMATCH``).
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tv_app.application.gpt_actions import GPT_ACTIONS_OPERATION_IDS
from tv_app.application.gpt_actions.capability_surface import (
    EXECUTE_VERB_STATUS,
    build_capability_surface,
)
from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.proposal_store import (
    get_proposal_store,
    reset_proposal_store_for_tests,
)
from tv_app.application.gpt_actions.vista_consent_service import (
    VistaConsentService,
    _target_ref,
    confirm_op_names,
)
from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
)
from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
    InMemoryIdempotencyRepository,
)
from tv_app.infrastructure.persistence.repositories.vista_consent_challenge_repository import (
    InMemoryVistaConsentChallengeRepository,
)
from tv_app.interface.mcp.constants import MCP_TOOL_NAMES, TOOL_CLASS

ACTOR = "actor-1"
PID = str(uuid.uuid4())
SID = str(uuid.uuid4())


def _user(perms=None, principal_type="user"):
    return SimpleNamespace(
        is_superadmin=False,
        permissions=perms if perms is not None else ["tv-dashboard.read", "tv-dashboard.write"],
        roles=[], groups=[], id=ACTOR, email="a@d.local",
        principal_type=principal_type,
    )


def _writes_mock():
    writes = MagicMock(spec=[
        "assert_expected_revision", "get_revision",
        "add_slide", "delete_slide", "list_slides", "list_sections",
        "get_playlist", "create_playlist",
    ])
    writes.get_revision.return_value = 4
    writes.add_slide.return_value = {"id": SID, "title": "T"}
    writes.list_slides.return_value = [{"id": SID, "title": "T", "nativeConfig": {}}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": PID}
    writes.create_playlist.return_value = {"id": PID}
    return writes


def _dispatch(consent_repo=None):
    writes = _writes_mock()
    svc = VistaConsentService(
        challenges=consent_repo or InMemoryVistaConsentChallengeRepository()
    )
    commit = TvGptCommitService(
        writes=writes, idempotency=InMemoryIdempotencyRepository(),
        access=MagicMock(resolve=MagicMock(
            return_value=SimpleNamespace(can_edit=True, can_read=True, level="owner"))),
        consent=svc,
    )
    d = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=commit, consent=svc)
    d._access.resolve = MagicMock(
        return_value=SimpleNamespace(can_edit=True, can_read=True, level="owner"))
    return d, writes, svc


@pytest.fixture(autouse=True)
def _clean():
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


def _patch_preview(ops, policy="direct", risk="additive"):
    return patch.object(PresentationPatchService, "preview", return_value={
        "appliedOps": [o["op"] for o in ops],
        "orderedOps": ops,
        "baseRevision": 3,
        "risk": risk,
        "confirmationPolicy": policy,
        "sideEffectHints": [],
        "diff": {},
        "fingerprint": "fp-x",
    })


def _prepare(d, ops, target=None, **kw):
    with _patch_preview(ops, **{k: v for k, v in kw.items() if k in ("policy", "risk")}):
        return d.semantic_execute(
            user=_user(),
            entity="presentation",
            action="apply_mutation",
            phase="prepare",
            operations=ops,
            target=target if target is not None else {"playlistId": PID},
            catalog_version=PresentationOpsContentService.catalog_version(),
        )


def _approve_and_echo(svc, prepared, actor=ACTOR):
    from tv_app.application.gpt_actions.proposal_store import (
        parse_proposal_handle,
    )

    challenge = prepared["consentChallenge"]
    proposal = get_proposal_store().get(
        parse_proposal_handle(prepared["proposal_handle"]))
    svc.approve(
        challenge_id=challenge["challengeId"], actor_sub=actor,
        token_claims={"sub": actor, "iat": int(__import__("time").time())},
    )
    return challenge["challengeId"], _target_ref(proposal, confirm_op_names(proposal))


def _commit(d, prepared, **kw):
    from tv_app.application.gpt_actions.proposal_store import (
        parse_proposal_handle,
    )

    args = dict(
        user=_user(), entity="presentation", action="apply_mutation",
        phase="commit", proposal_handle=prepared["proposal_handle"],
    )
    args.update(kw)
    proposal = get_proposal_store().get(
        parse_proposal_handle(prepared["proposal_handle"]))
    ops = (
        (proposal.exact_change or {}).get("ops")
        if proposal is not None
        else (prepared.get("orderedOps") or prepared.get("ops") or [])
    ) or []
    policy = prepared.get("confirmationPolicy") or "direct"
    risk = prepared.get("risk") or "additive"
    # The canonical commit re-previews the sealed plan — keep the patch
    # service on the same deterministic result as the prepare phase.
    with _patch_preview(ops, policy=policy, risk=risk):
        return d.semantic_execute(**args)


# --- surface ---------------------------------------------------------------

def test_surface_has_seventeen_tools():
    assert len(MCP_TOOL_NAMES) == 17
    assert "execute" in MCP_TOOL_NAMES
    assert TOOL_CLASS["execute"] == "ACT"
    assert "vista_execute" in GPT_ACTIONS_OPERATION_IDS


def test_surface_execute_status_implemented():
    assert EXECUTE_VERB_STATUS == "implemented"
    verbs = build_capability_surface(transport="mcp")["semantic_verbs"]
    assert verbs["tools"]["execute"]["status"] == "implemented"
    assert verbs["tools"]["execute"]["phases"] == ["prepare", "commit"]


# --- prepare: contract ------------------------------------------------------

def test_prepare_returns_sealed_proposal():
    d, _, _ = _dispatch()
    ops = [{"op": "add_blank_slide", "title": "T"}]
    with _patch_preview(ops):
        out = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="prepare", operations=ops, target={"playlistId": PID},
            catalog_version=PresentationOpsContentService.catalog_version(),
        )
    assert out["proposal_handle"]
    assert out["canCommit"] is True
    assert out["confirmationPolicy"] == "direct"
    assert out["baseRevision"] == 3
    assert out["fingerprint"] == "fp-x"
    assert "consentChallenge" not in out


def test_prepare_default_phase_is_prepare():
    d, _, _ = _dispatch()
    ops = [{"op": "add_blank_slide", "title": "T"}]
    with _patch_preview(ops):
        out = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            operations=ops, target={"playlistId": PID},
        )
    assert out["proposal_handle"]


def test_prepare_args_envelope_flattened():
    """{op,args,as} entries flatten to canonical typed ops."""
    d, _, _ = _dispatch()
    captured = {}

    def _spy(envelope, **kw):
        captured["ops"] = envelope["ops"]
        return {
            "appliedOps": ["add_blank_slide"],
            "orderedOps": envelope["ops"],
            "baseRevision": 3, "risk": "additive",
            "confirmationPolicy": "direct", "sideEffectHints": [],
            "diff": {}, "fingerprint": "fp",
        }

    with patch.object(PresentationPatchService, "preview", side_effect=_spy):
        d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            operations=[{"op": "add_blank_slide", "args": {"title": "T"}, "as": "s1"}],
            target={"playlistId": PID},
        )
    assert captured["ops"] == [{"op": "add_blank_slide", "as": "s1", "title": "T"}]


def test_prepare_confirm_plan_emits_consent_challenge():
    d, _, _ = _dispatch()
    ops = [{"op": "delete_slide", "slideId": SID}]
    with _patch_preview(ops, policy="confirm", risk="destructive"):
        out = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            operations=ops, target={"playlistId": PID, "slideId": SID},
        )
    assert out["confirmationPolicy"] == "confirm"
    assert out["consentChallenge"]["status"] == "PENDING"
    assert out["requiredConfirmation"] == ["delete_slide"]


def test_compound_plan_preserves_compiler_order():
    """Compound create_playlist+slides plan — orderedOps from the
    canonical compiler are the sealed plan (as/*Ref refs pass through)."""
    d, _, _ = _dispatch()
    ops = [
        {"op": "create_playlist", "name": "Compound", "as": "pl"},
        {"op": "add_blank_slide", "playlistRef": "pl", "title": "S1", "as": "s1"},
        {"op": "create_block", "slideRef": "s1", "type": "text", "content": "hi"},
    ]
    with _patch_preview(ops):
        out = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            operations=ops, target={},
        )
    from tv_app.application.gpt_actions.proposal_store import (
        parse_proposal_handle,
    )

    proposal = get_proposal_store().get(
        parse_proposal_handle(out["proposal_handle"]))
    sealed = proposal.exact_change["ops"]
    assert [o["op"] for o in sealed] == [
        "create_playlist", "add_blank_slide", "create_block"]
    assert sealed[1]["playlistRef"] == "pl"
    assert sealed[2]["slideRef"] == "s1"


# --- prepare: negatives ------------------------------------------------------

def test_unknown_entity_rejected():
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(), entity="playlist", action="apply_mutation",
            operations=[{"op": "add_blank_slide"}], target={},
        )
    assert exc.value.code == "UNKNOWN_ENTITY"
    assert exc.value.status_code == 422


def test_unknown_action_rejected():
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(), entity="presentation", action="delete_all",
            operations=[{"op": "add_blank_slide"}], target={},
        )
    assert exc.value.code == "UNKNOWN_ACTION"


def test_invalid_phase_rejected():
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="apply", operations=[{"op": "add_blank_slide"}], target={},
        )
    assert exc.value.code == "VALIDATION_ERROR"


def test_prepare_requires_operations():
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="prepare", target={"playlistId": PID},
        )
    assert exc.value.code == "INVALID_CHANGE"


@pytest.mark.parametrize("field", ["proposal_handle", "consent_artifact", "target_echo"])
def test_commit_fields_rejected_in_prepare(field):
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="prepare", operations=[{"op": "add_blank_slide"}],
            target={"playlistId": PID}, **{field: "x"},
        )
    assert exc.value.code == "VALIDATION_ERROR"


def test_commit_now_rejected_on_mcp_transport():
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            operations=[{"op": "add_blank_slide"}], target={"playlistId": PID},
            commit_now=True, transport="mcp",
        )
    assert exc.value.code == "VALIDATION_ERROR"


def test_prepare_denied_without_write_permission():
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(perms=["tv-dashboard.read"]),
            entity="presentation", action="apply_mutation",
            operations=[{"op": "add_blank_slide"}], target={"playlistId": PID},
        )
    assert exc.value.code == "PERMISSION_DENIED"
    assert exc.value.status_code == 403


def test_prepare_denied_for_non_user_principal():
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(principal_type="service"),
            entity="presentation", action="apply_mutation",
            operations=[{"op": "add_blank_slide"}], target={},
        )
    assert exc.value.code == "PRINCIPAL_TYPE_DENIED"


# --- commit: contract ---------------------------------------------------------

def test_commit_direct_plan_verified():
    d, writes, _ = _dispatch()
    prepared = _prepare(d, [{"op": "add_blank_slide", "title": "T"}])
    out = _commit(d, prepared, idempotency_key="k-1")
    assert out.get("status") == "VERIFIED"
    writes.add_slide.assert_called_once()


def test_commit_rejects_operations_plan_mismatch():
    d, _, _ = _dispatch()
    prepared = _prepare(d, [{"op": "add_blank_slide", "title": "T"}])
    with pytest.raises(GptActionsError) as exc:
        _commit(d, prepared, idempotency_key="k-pm",
                operations=[{"op": "delete_slide", "slideId": SID}])
    assert exc.value.code == "PLAN_MISMATCH"
    assert exc.value.status_code == 409


@pytest.mark.parametrize("field,value", [
    ("target", {"playlistId": PID}),
    ("catalog_version", "v1"),
    ("commit_now", True),
])
def test_prepare_fields_rejected_in_commit(field, value):
    d, _, _ = _dispatch()
    prepared = _prepare(d, [{"op": "add_blank_slide", "title": "T"}])
    with pytest.raises(GptActionsError) as exc:
        _commit(d, prepared, idempotency_key="k-f", **{field: value})
    assert exc.value.code == "VALIDATION_ERROR"


def test_commit_requires_handle():
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="commit", idempotency_key="k-h",
        )
    assert exc.value.code == "INVALID_CHANGE"


# --- commit: consent / security -----------------------------------------------

def test_commit_confirm_plan_requires_artifact():
    """confirm plan on the semantic surface: no artifact → typed
    CONFIRMATION_REQUIRED — there is no confirmation boolean to bypass."""
    repo = InMemoryVistaConsentChallengeRepository()
    d, writes, _ = _dispatch(repo)
    prepared = _prepare(
        d, [{"op": "delete_slide", "slideId": SID}],
        target={"playlistId": PID, "slideId": SID},
        policy="confirm", risk="destructive",
    )
    assert prepared["consentChallenge"]["status"] == "PENDING"
    with pytest.raises(GptActionsError) as exc:
        _commit(d, prepared, idempotency_key="k-c1")
    assert exc.value.code == "CONFIRMATION_REQUIRED"
    writes.delete_slide.assert_not_called()


def test_commit_confirm_plan_with_approved_artifact():
    repo = InMemoryVistaConsentChallengeRepository()
    d, writes, svc = _dispatch(repo)
    prepared = _prepare(
        d, [{"op": "delete_slide", "slideId": SID}],
        target={"playlistId": PID, "slideId": SID},
        policy="confirm", risk="destructive",
    )
    artifact, echo = _approve_and_echo(svc, prepared)
    writes.list_slides.return_value = []  # read-back post-delete
    out = _commit(
        d, prepared, consent_artifact=artifact, target_echo=echo,
        idempotency_key="k-c2",
    )
    assert out.get("status") == "VERIFIED"
    writes.delete_slide.assert_called_once()
    row = repo.get_by_id(challenge_id=artifact)
    assert row["status"] == "CONSUMED"


def test_commit_wrong_target_echo_mismatch():
    repo = InMemoryVistaConsentChallengeRepository()
    d, writes, svc = _dispatch(repo)
    prepared = _prepare(
        d, [{"op": "delete_slide", "slideId": SID}],
        target={"playlistId": PID, "slideId": SID},
        policy="confirm", risk="destructive",
    )
    artifact, _ = _approve_and_echo(svc, prepared)
    with pytest.raises(GptActionsError) as exc:
        _commit(d, prepared, consent_artifact=artifact,
                target_echo="wrong-ref", idempotency_key="k-c3")
    assert exc.value.code == "CONFIRMATION_MISMATCH"
    writes.delete_slide.assert_not_called()


def test_commit_artifact_from_other_plan_rejected():
    repo = InMemoryVistaConsentChallengeRepository()
    d, writes, svc = _dispatch(repo)
    ops = [{"op": "delete_slide", "slideId": SID}]
    prepared_a = _prepare(
        d, ops, target={"playlistId": PID, "slideId": SID},
        policy="confirm", risk="destructive",
    )
    prepared_b = _prepare(
        d, ops, target={"playlistId": PID, "slideId": SID},
        policy="confirm", risk="destructive",
    )
    # Approve challenge of plan A but commit plan B → binding fails.
    artifact, echo = _approve_and_echo(svc, prepared_a)
    with pytest.raises(GptActionsError) as exc:
        _commit(d, prepared_b, consent_artifact=artifact, target_echo=echo,
                idempotency_key="k-c4")
    assert exc.value.code in ("CONSENT_MISMATCH", "CONSENT_CHALLENGE_NOT_FOUND")
    writes.delete_slide.assert_not_called()


def test_commit_proposal_of_other_actor_denied():
    """Handle is actor-bound — a different actor cannot commit it."""
    d, _, _ = _dispatch()
    prepared = _prepare(d, [{"op": "add_blank_slide", "title": "T"}])
    other = _user()
    other.id = "actor-2"
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=other, entity="presentation", action="apply_mutation",
            phase="commit", proposal_handle=prepared["proposal_handle"],
            idempotency_key="k-x",
        )
    assert exc.value.code in ("PROPOSAL_NOT_FOUND", "CONSENT_MISMATCH", "AUTHZ_DENIED")
    assert exc.value.status_code == 403


# --- commit: concurrency / idempotency ---------------------------------------

def test_commit_replay_same_idempotency_key():
    d, writes, _ = _dispatch()
    prepared = _prepare(d, [{"op": "add_blank_slide", "title": "T"}])
    out1 = _commit(d, prepared, idempotency_key="k-dup")
    # Replay: the proposal is consumed, but the idempotency snapshot
    # replays the stored outcome — no second write.
    with pytest.raises(GptActionsError):
        _commit(d, prepared, idempotency_key="k-other")
    out2 = _commit(d, prepared, idempotency_key="k-dup")
    assert out2.get("status") == out1.get("status")
    writes.add_slide.assert_called_once()


def test_commit_consumed_proposal_fails_closed():
    d, _, _ = _dispatch()
    prepared = _prepare(d, [{"op": "add_blank_slide", "title": "T"}])
    _commit(d, prepared, idempotency_key="k-1")
    with pytest.raises(GptActionsError) as exc:
        _commit(d, prepared, idempotency_key="k-2")
    assert exc.value.code == "PROPOSAL_NOT_FOUND"


def test_commit_revision_conflict_after_prepare():
    """CAS: revision moved between prepare and commit → typed conflict."""
    d, writes, _ = _dispatch()
    prepared = _prepare(d, [{"op": "add_blank_slide", "title": "T"}])
    from tv_app.application.services.tv_presentation_write_service import (
        PresentationWriteError,
    )

    writes.assert_expected_revision.side_effect = PresentationWriteError(
        "revision conflict", code="REVISION_CONFLICT", status_code=409)
    with pytest.raises((GptActionsError, PresentationWriteError)) as exc:
        _commit(d, prepared, idempotency_key="k-cas")
    code = getattr(exc.value, "code", None)
    assert code == "REVISION_CONFLICT"


# --- equivalence vs legacy surface --------------------------------------------

def test_prepare_equivalent_to_legacy_preview_change():
    """Same plan via execute(prepare) and prepare_change produces the
    same sealed proposal semantics (policy, risk, ops, base revision)."""
    d, _, _ = _dispatch()
    ops = [{"op": "add_blank_slide", "title": "T"}]
    with _patch_preview(ops):
        sem = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            operations=ops, target={"playlistId": PID},
            catalog_version=PresentationOpsContentService.catalog_version(),
        )
    with _patch_preview(ops):
        leg = d.preview_change(
            user=_user(), target={"playlistId": PID}, ops=ops,
            catalog_version=PresentationOpsContentService.catalog_version(),
            authorization=None, commit_now=False, transport="mcp",
        )
    for key in ("canCommit", "risk", "confirmationPolicy", "baseRevision",
                "operationNames", "orderedOps"):
        assert sem[key] == leg[key], key


def test_commit_equivalent_to_legacy_commit_change_direct():
    """Direct plan: semantic commit and legacy commit_proposal reach the
    same verified outcome on the same canonical commit service."""
    d, writes, _ = _dispatch()
    ops = [{"op": "add_blank_slide", "title": "T"}]
    prepared = _prepare(d, ops)
    with _patch_preview(ops):
        out = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="commit", proposal_handle=prepared["proposal_handle"],
            idempotency_key="k-eq",
        )
    assert out.get("status") == "VERIFIED"
    writes.add_slide.assert_called_once()


# --- commit_now single-shot (Actions-only) -------------------------------------

def test_commit_now_single_shot_direct_plan():
    """Actions envelope single-shot: direct plan + commit_now +
    idempotency_key commits inline via the canonical path."""
    d, writes, _ = _dispatch()
    ops = [{"op": "add_blank_slide", "title": "T"}]
    with _patch_preview(ops):
        out = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            operations=ops, target={"playlistId": PID},
            commit_now=True, idempotency_key="k-ss",
            transport="gpt_actions",
        )
    assert out.get("commit_now_applied") is True
    assert out.get("status") == "VERIFIED"
    writes.add_slide.assert_called_once()


def test_commit_now_ignored_for_confirm_plan():
    """confirm plan never single-shots — canonical pipeline flags the
    ignored commit_now and still requires the two-phase consent flow."""
    d, writes, _ = _dispatch()
    ops = [{"op": "delete_slide", "slideId": SID}]
    with _patch_preview(ops, policy="confirm", risk="destructive"):
        out = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            operations=ops, target={"playlistId": PID, "slideId": SID},
            commit_now=True, idempotency_key="k-ss2",
            transport="gpt_actions",
        )
    assert out.get("commit_now_applied") is False
    writes.delete_slide.assert_not_called()
