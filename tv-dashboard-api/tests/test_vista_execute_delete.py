"""SEMANTIC_TOOLS_V1 A6/A7 — execute + delete facades.

Both verbs are thin facades over the canonical PREPARE→COMMIT pipeline
with ``consent_required=True`` — confirmation=true never proves human
consent on the semantic surface.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.proposal_store import (
    get_proposal_store,
    reset_proposal_store_for_tests,
)
from tv_app.application.gpt_actions.vista_consent_service import (
    VistaConsentService,
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
from tv_app.interface.mcp.constants import MCP_FORBIDDEN_TOOLS, MCP_TOOL_NAMES

ACTOR = "actor-1"
PID = str(uuid.uuid4())
SID = str(uuid.uuid4())


def _user():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.read", "tv-dashboard.write"],
        roles=[], groups=[], id=ACTOR, email="a@d.local",
    )


def _dispatch(consent_repo=None):
    writes = MagicMock(spec=["assert_expected_revision", "get_revision",
        "add_slide", "delete_slide", "list_slides", "list_sections", "get_playlist"])
    writes.get_revision.return_value = 4
    writes.add_slide.return_value = {"id": SID, "title": "T"}
    writes.list_slides.return_value = [{"id": SID, "title": "T", "nativeConfig": {}}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": PID}
    svc = VistaConsentService(challenges=consent_repo or InMemoryVistaConsentChallengeRepository())
    commit = TvGptCommitService(
        writes=writes, idempotency=InMemoryIdempotencyRepository(),
        access=MagicMock(resolve=MagicMock(
            return_value=SimpleNamespace(can_edit=True, can_read=True, level="owner"))),
        consent=svc,
    )
    d = GptActionsDispatchService(repo=MagicMock(), writes=writes, commit=commit, consent=svc)
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


# --- surface ---------------------------------------------------------------

def test_surface_has_six_tools():
    # SEMANTIC_TOOLS_V1 consolidation (six-tools surface): execute and
    # delete are facades over PREPARE→COMMIT; the 12 legacy per-op tools
    # were removed and remain forbidden on the wire.
    assert len(MCP_TOOL_NAMES) == 6
    assert {"execute", "delete"} <= set(MCP_TOOL_NAMES)
    assert "execute" not in MCP_FORBIDDEN_TOOLS
    assert "delete_data_model" in MCP_FORBIDDEN_TOOLS
    assert "delete_data_source" in MCP_FORBIDDEN_TOOLS


# --- execute ---------------------------------------------------------------

def test_execute_prepare_returns_sealed_proposal():
    d, _, _ = _dispatch()
    with _patch_preview([{"op": "add_blank_slide", "title": "T"}]):
        out = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="prepare", operations=[{"op": "add_blank_slide", "title": "T"}],
            target={"playlistId": PID},
            catalog_version=PresentationOpsContentService.catalog_version(),
        )
    assert out["proposal_handle"]
    assert out["confirmationPolicy"] == "direct"
    assert "consentChallenge" not in out


def test_execute_requires_ops_or_handle():
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation")
    assert exc.value.code == "INVALID_CHANGE"


def test_execute_commit_requires_artifact_for_confirm_plan():
    """confirm plan + consent_required → CONFIRMATION_REQUIRED without
    artifact even with confirmation=true."""
    repo = InMemoryVistaConsentChallengeRepository()
    d, writes, svc = _dispatch(repo)
    ops = [{"op": "delete_slide", "slideId": SID}]
    with _patch_preview(ops, policy="confirm", risk="destructive"):
        prepared = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="prepare", operations=ops,
            target={"playlistId": PID, "slideId": SID},
            catalog_version=PresentationOpsContentService.catalog_version(),
        )
    assert prepared["consentChallenge"]["status"] == "PENDING"
    with pytest.raises(GptActionsError) as exc:
        d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="commit", proposal_handle=prepared["proposal_handle"],
            idempotency_key="k-ex-1",
        )
    assert exc.value.code == "CONFIRMATION_REQUIRED"
    writes.delete_slide.assert_not_called()


def test_execute_commit_with_approved_artifact_verified():
    repo = InMemoryVistaConsentChallengeRepository()
    d, writes, svc = _dispatch(repo)
    ops = [{"op": "delete_slide", "slideId": SID}]
    with _patch_preview(ops, policy="confirm", risk="destructive"):
        prepared = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="prepare", operations=ops,
            target={"playlistId": PID, "slideId": SID},
            catalog_version=PresentationOpsContentService.catalog_version(),
        )
    challenge = prepared["consentChallenge"]
    from tv_app.application.gpt_actions.proposal_store import (
        parse_proposal_handle,
    )
    proposal = get_proposal_store().get(
        parse_proposal_handle(prepared["proposal_handle"]))
    svc.approve(
        challenge_id=challenge["challengeId"], actor_sub=ACTOR,
        token_claims={"sub": ACTOR, "iat": int(__import__("time").time())},
    )
    from tv_app.application.gpt_actions.vista_consent_service import (
        _target_ref, confirm_op_names)
    echo = _target_ref(proposal, confirm_op_names(proposal))
    writes.list_slides.return_value = []  # read-back post-delete
    with _patch_preview(ops, policy="confirm", risk="destructive"):
        out = d.semantic_execute(
            user=_user(), entity="presentation", action="apply_mutation",
            phase="commit", proposal_handle=prepared["proposal_handle"],
            consent_artifact=challenge["challengeId"], target_echo=echo,
            idempotency_key="k-ex-2",
        )
    assert out.get("status") == "VERIFIED"
    writes.delete_slide.assert_called_once()


# --- delete ----------------------------------------------------------------

def test_delete_rejects_unapproved_entity():
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_delete(user=_user(), entity="process",
                          target={"playlistId": PID})
    assert exc.value.code == "CAPABILITY_NOT_APPROVED"
    assert exc.value.status_code == 403


def test_delete_data_model_without_model_id_fails_dependency_gate():
    """data_model is mapped in DELETE_ENTITIES, but without ``modelId``
    in target the canonical plan-dependency gate rejects the plan
    (DEPENDENCY_UNSATISFIABLE) — the op name stays forbidden on the
    wire via MCP_FORBIDDEN_TOOLS either way."""
    d, _, _ = _dispatch()
    with pytest.raises(GptActionsError) as exc:
        d.semantic_delete(user=_user(), entity="data_model",
                          target={"playlistId": PID})
    assert exc.value.code == "DEPENDENCY_UNSATISFIABLE"


def test_delete_slide_prepare_emits_challenge():
    d, _, _ = _dispatch()
    with _patch_preview([{"op": "delete_slide", "slideId": SID}],
                        policy="confirm", risk="destructive"):
        out = d.semantic_delete(
            user=_user(), entity="slide",
            target={"playlistId": PID, "slideId": SID},
            catalog_version=PresentationOpsContentService.catalog_version(),
        )
    assert out["confirmationPolicy"] == "confirm"
    assert out["consentChallenge"]["status"] == "PENDING"
    assert out["requiredConfirmation"] == ["delete_slide"]


def test_delete_commit_without_artifact_fails_closed():
    d, writes, _ = _dispatch(InMemoryVistaConsentChallengeRepository())
    with _patch_preview([{"op": "delete_slide", "slideId": SID}],
                        policy="confirm", risk="destructive"):
        prepared = d.semantic_delete(
            user=_user(), entity="slide",
            target={"playlistId": PID, "slideId": SID},
            catalog_version=PresentationOpsContentService.catalog_version(),
        )
    with pytest.raises(GptActionsError) as exc:
        d.semantic_delete(
            user=_user(), entity="slide", phase="commit",
            proposal_handle=prepared["proposal_handle"],
            idempotency_key="k-del-1",
        )
    assert exc.value.code == "CONFIRMATION_REQUIRED"
    writes.delete_slide.assert_not_called()


def test_delete_commit_consumes_artifact_single_use():
    repo = InMemoryVistaConsentChallengeRepository()
    d, writes, svc = _dispatch(repo)
    ops = [{"op": "delete_slide", "slideId": SID}]
    with _patch_preview(ops, policy="confirm", risk="destructive"):
        prepared = d.semantic_delete(
            user=_user(), entity="slide",
            target={"playlistId": PID, "slideId": SID},
            catalog_version=PresentationOpsContentService.catalog_version(),
        )
    challenge = prepared["consentChallenge"]
    from tv_app.application.gpt_actions.proposal_store import (
        parse_proposal_handle,
    )
    proposal = get_proposal_store().get(
        parse_proposal_handle(prepared["proposal_handle"]))
    svc.approve(
        challenge_id=challenge["challengeId"], actor_sub=ACTOR,
        token_claims={"sub": ACTOR, "iat": int(__import__("time").time())},
    )
    from tv_app.application.gpt_actions.vista_consent_service import (
        _target_ref, confirm_op_names)
    echo = _target_ref(proposal, confirm_op_names(proposal))
    writes.list_slides.return_value = []  # read-back post-delete
    with _patch_preview(ops, policy="confirm", risk="destructive"):
        out = d.semantic_delete(
            user=_user(), entity="slide", phase="commit",
            proposal_handle=prepared["proposal_handle"],
            consent_artifact=challenge["challengeId"], target_echo=echo,
            idempotency_key="k-del-2",
        )
    assert out.get("status") == "VERIFIED"
    row = repo.get_by_id(challenge_id=challenge["challengeId"])
    assert row["status"] == "CONSUMED"
