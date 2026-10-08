"""MCP2 — VISTA governed write envelope: prepare_change (PREPARE) + commit_proposal (ACT).

The MCP tools are pure adapters over ``GptActionsDispatchService.preview_change``
and ``commit_change`` — proposal handle, idempotency, confirmation policy,
actor binding, and postcondition verification are all canonical application
behavior. Tests exercise the real dispatch + real proposal store + real
commit service with in-memory idempotency and mocked persistence ports.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)

from tv_app.application.gpt_actions.commit_service import TvGptCommitService
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.proposal_store import reset_proposal_store_for_tests
from tv_app.application.services.data.presentation_mutation import PresentationPatchService
from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
)
from tv_app.infrastructure.persistence.repositories.idempotency_repository import (
    InMemoryIdempotencyRepository,
)
from tv_app.interface.mcp import tool_bridge
from tv_app.interface.mcp.constants import MCP_TOOL_NAMES, TOOL_CLASS


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _editor(user_id: str = "editor-1"):
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.read", "tv-dashboard.write"],
        roles=[],
        groups=[],
        id=user_id,
        email=f"{user_id}@delpi.local",
    )


def _viewer():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.read"],
        roles=[],
        groups=[],
        id="viewer-1",
        email="viewer@delpi.local",
    )


class _ctx:
    def __init__(self, user, authorization: str | None = "Bearer test"):
        self.user = user
        self.authorization = authorization
        self._u = None
        self._a = None

    def __enter__(self):
        self._u = set_current_user(self.user)
        self._a = set_request_authorization(self.authorization)
        return self

    def __exit__(self, *exc):
        reset_current_user(self._u)
        reset_request_authorization(self._a)


def _writes_mock():
    base = [
        "assert_expected_revision",
        "get_revision",
        "add_slide",
        "add_slide_from_preset",
        "update_slide",
        "delete_slide",
        "reorder_slides",
        "add_section",
        "update_section",
        "delete_section",
        "reorder_sections",
        "list_slides",
        "list_sections",
        "get_playlist",
        "create_playlist",
    ]
    return MagicMock(spec=base)


def _governed_dispatch():
    """Real dispatch + real commit service; in-memory idempotency; mocked writes."""
    writes = _writes_mock()
    idem = InMemoryIdempotencyRepository()
    access = MagicMock()
    access.resolve.return_value = SimpleNamespace(
        can_edit=True, can_read=True, level="owner"
    )
    commit = TvGptCommitService(writes=writes, idempotency=idem, access=access)
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=commit
    )
    return dispatch, writes, idem


def _access_patches(dispatch, *, can_edit=True, can_read=True):
    return (
        patch.object(
            dispatch._access,
            "resolve",
            return_value=SimpleNamespace(can_edit=can_edit, can_read=can_read, level="owner"),
        ),
    )


def _preview_result(**extra):
    return {
        "appliedOps": ["add_blank_slide"],
        "orderedOps": [{"op": "add_blank_slide", "title": "T"}],
        "baseRevision": 3,
        "risk": "additive",
        "confirmationPolicy": "direct",
        "sideEffectHints": [],
        "diff": {},
        "fingerprint": "fp",
        "nativeConfig": None,
        "message": "ok",
        **extra,
    }


@pytest.fixture(autouse=True)
def _clean_proposal_store():
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


# ---------------------------------------------------------------------------
# Surface exactness (11 tools: 6 READ + 1 DISCOVERY + 2 ANALYSIS + PREPARE + ACT)
# ---------------------------------------------------------------------------


def test_surface_has_exactly_eleven_tools():
    assert len(MCP_TOOL_NAMES) == 11
    assert TOOL_CLASS["prepare_change"] == "PREPARE"
    assert TOOL_CLASS["commit_proposal"] == "ACT"
    assert sum(1 for v in TOOL_CLASS.values() if v == "READ") == 6
    assert sum(1 for v in TOOL_CLASS.values() if v == "DISCOVERY") == 1
    assert TOOL_CLASS["get_catalog"] == "DISCOVERY"
    # Owner intelligence surface: ANALYSIS exposes the owner's semantic/
    # visual recommendation pipeline (preview_data_block) and the canonical
    # NL→typed-ops materializer (suggest_change) — both non-persisting.
    assert sum(1 for v in TOOL_CLASS.values() if v == "ANALYSIS") == 2
    assert TOOL_CLASS["preview_data_block"] == "ANALYSIS"


def test_mcp_catalog_exposes_field_vocabulary():
    """Orchestrator-facing catalog carries canonical enum vocabulary —
    a provider-neutral consumer can build create_block{type:'text'}
    without owner-specific knowledge."""
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_get_catalog()
    assert result.is_error is False
    ops = result.structured_content["data"]["operations"]
    create_block = ops["create_block"]
    assert "text" in create_block["fieldVocabulary"]["type"]
    assert "content" in create_block["fields"]
    # Destructive policy is owner-declared, not consumer-inferred.
    assert ops["delete_slide"]["confirmationPolicy"] == "confirm"
    assert create_block["confirmationPolicy"] == "direct"


# ---------------------------------------------------------------------------
# PREPARE — delegation, non-persistence, output passthrough
# ---------------------------------------------------------------------------


def test_prepare_change_delegates_with_commit_now_false():
    dispatch, writes, _ = _governed_dispatch()
    with _ctx(_editor()), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(
        PresentationPatchService, "preview", return_value=_preview_result()
    ) as prev:
        result = tool_bridge.tool_prepare_change(
            target={"playlistId": str(uuid4())},
            ops=[{"op": "add_blank_slide", "title": "T"}],
        )
    assert result.is_error is False
    prev.assert_called_once()
    data = result.structured_content["data"]
    assert data["proposal_handle"]
    assert data["canCommit"] is True
    assert data["persisted"] is False
    assert data["confirmationPolicy"] == "direct"
    # PREPARE must not touch the write port at all.
    assert writes.method_calls == []


def test_prepare_change_requires_write_permission():
    """READ-only identity cannot prepare — TV_WRITE gate is application-owned."""
    dispatch, writes, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_prepare_change(
            target={"playlistId": str(uuid4())},
            ops=[{"op": "add_blank_slide"}],
        )
    assert result.is_error is True
    assert result.structured_content["httpStatus"] == 403
    assert writes.method_calls == []


def test_prepare_change_requires_ops():
    with _ctx(_editor()):
        result = tool_bridge.tool_prepare_change(target={"playlistId": str(uuid4())}, ops=[])
    assert result.is_error is True
    assert result.structured_content["code"] == "INVALID_CHANGE"
    assert result.structured_content["httpStatus"] == 422


def test_prepare_unknown_op_fails_via_application():
    """Unknown op rejected by canonical preview pipeline — no MCP fallback."""
    dispatch, writes, _ = _governed_dispatch()
    from tv_app.application.services.data.presentation_mutation import (
        PresentationPatchError,
    )

    with _ctx(_editor()), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(
        PresentationPatchService,
        "preview",
        side_effect=PresentationPatchError(
            "Operação não suportada.", code="INVALID_CHANGE", details={"op": "bogus_op"}
        ),
    ):
        result = tool_bridge.tool_prepare_change(
            target={"playlistId": str(uuid4())},
            ops=[{"op": "bogus_op"}],
        )
    assert result.is_error is True
    assert result.structured_content["code"] == "INVALID_CHANGE"
    assert result.structured_content["httpStatus"] == 422
    assert writes.method_calls == []


def test_prepare_unauthorized_playlist_fails_closed():
    dispatch, writes, _ = _governed_dispatch()
    with _ctx(_editor()), patch.object(
        dispatch._access,
        "resolve",
        return_value=SimpleNamespace(can_edit=False, can_read=False, level=None),
    ), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_prepare_change(
            target={"playlistId": str(uuid4())},
            ops=[{"op": "add_blank_slide"}],
        )
    assert result.is_error is True
    assert result.structured_content["code"] == "RESOURCE_NOT_FOUND"
    assert result.structured_content["httpStatus"] == 404
    assert writes.method_calls == []


# ---------------------------------------------------------------------------
# ACT — idempotency, confirmation, proposal handle, postcondition
# ---------------------------------------------------------------------------


def _prepare_handle(dispatch, user, ops, playlist_id) -> str:
    with _ctx(user), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(PresentationPatchService, "preview", return_value=_preview_result()):
        result = tool_bridge.tool_prepare_change(
            target={"playlistId": playlist_id}, ops=ops
        )
    assert result.is_error is False
    return result.structured_content["data"]["proposal_handle"]


def test_commit_requires_idempotency_key():
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    user = _editor()
    handle = _prepare_handle(dispatch, user, [{"op": "add_blank_slide", "title": "T"}], playlist_id)
    with _ctx(user), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_commit_proposal(
            proposal_handle=handle, idempotency_key="", confirmation=True
        )
    assert result.is_error is True
    assert result.structured_content["code"] == "INVALID_CHANGE"
    assert result.structured_content["httpStatus"] == 422
    assert writes.method_calls == []


def test_commit_requires_explicit_confirmation():
    """confirmationPolicy=confirm ops (e.g. delete_slide) gate on explicit
    user confirmation; direct-policy ops never reach this gate."""
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    user = _editor()
    delete_ops = [{"op": "delete_slide", "slideId": str(uuid4())}]
    with _ctx(user), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(
        PresentationPatchService,
        "preview",
        return_value=_preview_result(
            appliedOps=["delete_slide"],
            orderedOps=delete_ops,
            risk="destructive",
            confirmationPolicy="confirm",
        ),
    ):
        prepared = tool_bridge.tool_prepare_change(
            target={"playlistId": playlist_id}, ops=delete_ops
        )
    assert prepared.is_error is False
    handle = prepared.structured_content["data"]["proposal_handle"]
    with _ctx(user), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_commit_proposal(
            proposal_handle=handle, idempotency_key="k-1", confirmation=False
        )
    assert result.is_error is True
    assert result.structured_content["code"] == "CONFIRMATION_REQUIRED"
    assert result.structured_content["httpStatus"] == 400
    assert writes.method_calls == []


def test_commit_direct_policy_needs_no_confirmation():
    """confirmationPolicy=direct proposal commits without explicit user
    confirmation — write port invoked via governed ACT path."""
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    slide_id = str(uuid4())
    writes.assert_expected_revision.return_value = 3
    writes.get_revision.return_value = 4
    writes.add_slide.return_value = {"id": slide_id, "title": "T"}
    writes.list_slides.return_value = [{"id": slide_id, "title": "T", "nativeConfig": {}}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": playlist_id}
    user = _editor()
    handle = _prepare_handle(dispatch, user, [{"op": "add_blank_slide", "title": "T"}], playlist_id)
    with _ctx(user), patch.object(tool_bridge, "_dispatch", dispatch), patch.object(
        PresentationPatchService, "preview", return_value={"confirmationPolicy": "direct"}
    ):
        result = tool_bridge.tool_commit_proposal(
            proposal_handle=handle, idempotency_key="k-direct-1", confirmation=None
        )
    assert result.is_error is False
    data = result.structured_content["data"]
    assert data["status"] == "VERIFIED"
    writes.add_slide.assert_called_once()


def test_commit_unknown_handle_fails_closed():
    dispatch, _, _ = _governed_dispatch()
    with _ctx(_editor()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_commit_proposal(
            proposal_handle="AAAA.BBBBCCCC", idempotency_key="k-2", confirmation=True
        )
    assert result.is_error is True
    assert result.structured_content["code"] == "PROPOSAL_NOT_FOUND"


def test_commit_tampered_handle_fails_closed():
    dispatch, _, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    user = _editor()
    handle = _prepare_handle(dispatch, user, [{"op": "add_blank_slide"}], playlist_id)
    tampered = handle[:-2] + ("AA" if not handle.endswith("AA") else "BB")
    with _ctx(user), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_commit_proposal(
            proposal_handle=tampered, idempotency_key="k-3", confirmation=True
        )
    assert result.is_error is True
    assert result.structured_content["code"] == "PROPOSAL_NOT_FOUND"


def test_commit_cross_user_fails_closed():
    """User A prepares → user B commits → AUTHZ_DENIED (proposal is actor-bound)."""
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    handle = _prepare_handle(dispatch, _editor("alice"), [{"op": "add_blank_slide"}], playlist_id)
    with _ctx(_editor("bob")), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_commit_proposal(
            proposal_handle=handle, idempotency_key="k-4", confirmation=True
        )
    assert result.is_error is True
    assert result.structured_content["code"] == "AUTHZ_DENIED"
    assert result.structured_content["httpStatus"] == 403
    assert writes.method_calls == []


def test_commit_verified_end_to_end():
    """PREPARE → ACT through MCP tools → canonical VERIFIED + write port hit once."""
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    slide_id = str(uuid4())
    writes.assert_expected_revision.return_value = 3
    writes.get_revision.return_value = 4
    writes.add_slide.return_value = {"id": slide_id, "title": "T"}
    writes.list_slides.return_value = [{"id": slide_id, "title": "T", "nativeConfig": {}}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": playlist_id}

    user = _editor()
    handle = _prepare_handle(dispatch, user, [{"op": "add_blank_slide", "title": "T"}], playlist_id)

    commit = dispatch._commit
    with _ctx(user), patch.object(tool_bridge, "_dispatch", dispatch), patch.object(
        commit, "_patch", MagicMock(preview=MagicMock(return_value={"confirmationPolicy": "direct"}))
    ) if hasattr(commit, "_patch") else patch.object(
        PresentationPatchService, "preview", return_value={"confirmationPolicy": "direct"}
    ):
        result = tool_bridge.tool_commit_proposal(
            proposal_handle=handle, idempotency_key="k-verified-1", confirmation=True
        )
    assert result.is_error is False
    data = result.structured_content["data"]
    assert data["status"] == "VERIFIED"
    writes.add_slide.assert_called_once()


def test_commit_idempotency_replay_same_key_same_handle():
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    slide_id = str(uuid4())
    writes.assert_expected_revision.return_value = 3
    writes.get_revision.return_value = 4
    writes.add_slide.return_value = {"id": slide_id, "title": "T"}
    writes.list_slides.return_value = [{"id": slide_id, "title": "T", "nativeConfig": {}}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": playlist_id}

    user = _editor()
    handle = _prepare_handle(dispatch, user, [{"op": "add_blank_slide", "title": "T"}], playlist_id)

    with _ctx(user), patch.object(tool_bridge, "_dispatch", dispatch), patch.object(
        PresentationPatchService, "preview", return_value={"confirmationPolicy": "direct"}
    ):
        first = tool_bridge.tool_commit_proposal(
            proposal_handle=handle, idempotency_key="k-replay", confirmation=True
        )
        second = tool_bridge.tool_commit_proposal(
            proposal_handle=handle, idempotency_key="k-replay", confirmation=True
        )
    assert first.is_error is False
    assert first.structured_content["data"]["status"] == "VERIFIED"
    # Replay: snapshot returned, no second execution.
    assert second.is_error is False
    assert second.structured_content["data"]["status"] == "VERIFIED"
    writes.add_slide.assert_called_once()


def test_commit_same_key_different_payload_conflicts():
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    slide_id = str(uuid4())
    writes.assert_expected_revision.return_value = 3
    writes.get_revision.return_value = 4
    writes.add_slide.return_value = {"id": slide_id, "title": "T"}
    writes.list_slides.return_value = [{"id": slide_id, "title": "T", "nativeConfig": {}}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": playlist_id}

    user = _editor()
    handle_a = _prepare_handle(dispatch, user, [{"op": "add_blank_slide", "title": "A"}], playlist_id)
    handle_b = _prepare_handle(dispatch, user, [{"op": "add_blank_slide", "title": "B"}], playlist_id)

    with _ctx(user), patch.object(tool_bridge, "_dispatch", dispatch), patch.object(
        PresentationPatchService, "preview", return_value={"confirmationPolicy": "direct"}
    ):
        first = tool_bridge.tool_commit_proposal(
            proposal_handle=handle_a, idempotency_key="k-shared", confirmation=True
        )
        conflict = tool_bridge.tool_commit_proposal(
            proposal_handle=handle_b, idempotency_key="k-shared", confirmation=True
        )
    assert first.is_error is False
    assert conflict.is_error is True
    assert conflict.structured_content["code"] == "IDEMPOTENCY_CONFLICT"
    assert conflict.structured_content["httpStatus"] == 409
    writes.add_slide.assert_called_once()


def test_commit_consumed_proposal_fails_closed():
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    slide_id = str(uuid4())
    writes.assert_expected_revision.return_value = 3
    writes.get_revision.return_value = 4
    writes.add_slide.return_value = {"id": slide_id, "title": "T"}
    writes.list_slides.return_value = [{"id": slide_id, "title": "T", "nativeConfig": {}}]
    writes.list_sections.return_value = []
    writes.get_playlist.return_value = {"id": playlist_id}

    user = _editor()
    handle = _prepare_handle(dispatch, user, [{"op": "add_blank_slide", "title": "T"}], playlist_id)

    with _ctx(user), patch.object(tool_bridge, "_dispatch", dispatch), patch.object(
        PresentationPatchService, "preview", return_value={"confirmationPolicy": "direct"}
    ):
        first = tool_bridge.tool_commit_proposal(
            proposal_handle=handle, idempotency_key="k-consume", confirmation=True
        )
        second = tool_bridge.tool_commit_proposal(
            proposal_handle=handle, idempotency_key="k-consume-2", confirmation=True
        )
    assert first.is_error is False
    assert second.is_error is True
    assert second.structured_content["code"] in {"PROPOSAL_NOT_FOUND", "PROPOSAL_CHANGED"}
    writes.add_slide.assert_called_once()


def test_commit_requires_write_permission():
    dispatch, writes, _ = _governed_dispatch()
    with _ctx(_viewer()), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_commit_proposal(
            proposal_handle="AAAA.BBBB", idempotency_key="k-9", confirmation=True
        )
    assert result.is_error is True
    assert result.structured_content["httpStatus"] == 403
    assert writes.method_calls == []


def test_commit_stale_revision_fails_typed():
    """Stale base revision → canonical write-path failure, never last-write-wins."""
    dispatch, writes, _ = _governed_dispatch()
    playlist_id = str(uuid4())
    from tv_app.application.services.tv_presentation_write_service import (
        PresentationWriteError,
    )

    writes.assert_expected_revision.side_effect = PresentationWriteError(
        "Revisão divergente.", status_code=409, code="REVISION_CONFLICT"
    )

    user = _editor()
    handle = _prepare_handle(dispatch, user, [{"op": "add_blank_slide", "title": "T"}], playlist_id)
    with _ctx(user), patch.object(tool_bridge, "_dispatch", dispatch), patch.object(
        PresentationPatchService, "preview", return_value={"confirmationPolicy": "direct"}
    ):
        result = tool_bridge.tool_commit_proposal(
            proposal_handle=handle, idempotency_key="k-stale", confirmation=True
        )
    assert result.is_error is True
    assert result.structured_content["code"] == "REVISION_CONFLICT"
    assert result.structured_content["httpStatus"] == 409
    writes.add_slide.assert_not_called()


def test_commit_proposal_cannot_override_target():
    """Caller supplies only proposal_handle + key + confirmation — there is no
    target parameter, so a proposal for playlist A cannot be steered to B."""
    import inspect

    sig = inspect.signature(tool_bridge.tool_commit_proposal)
    assert "target" not in sig.parameters
    assert "playlist_id" not in sig.parameters
    assert "ops" not in sig.parameters


# ---------------------------------------------------------------------------
# Error contract — domain codes survive the MCP envelope
# ---------------------------------------------------------------------------


def test_domain_codes_preserved_through_commit_path():
    dispatch, _, _ = _governed_dispatch()
    from tv_app.application.gpt_actions.errors import GptActionsError

    with _ctx(_editor()), patch.object(
        dispatch._commit,
        "commit",
        side_effect=GptActionsError(
            "Modelo em uso por consumidores.",
            code="data_model.in_use",
            status_code=409,
        ),
    ), patch.object(tool_bridge, "_dispatch", dispatch):
        result = tool_bridge.tool_commit_proposal(
            proposal_handle="AAAA.BBBBCCCC", idempotency_key="k-dom", confirmation=True
        )
    assert result.is_error is True
    body = result.structured_content
    assert body["code"] == "data_model.in_use"
    assert body["httpStatus"] == 409
    assert "Traceback" not in str(body)


def test_prepare_preserves_migration_conflict_code():
    dispatch, _, _ = _governed_dispatch()
    from tv_app.application.services.data.presentation_mutation import (
        PresentationPatchError,
    )

    with _ctx(_editor()), _access_patches(dispatch)[0], patch.object(
        tool_bridge, "_dispatch", dispatch
    ), patch.object(
        PresentationPatchService,
        "preview",
        side_effect=PresentationPatchError(
            "Fontes já migradas.", code="data_model.migration_conflict"
        ),
    ):
        result = tool_bridge.tool_prepare_change(
            target={"playlistId": str(uuid4())},
            ops=[{"op": "migrate_data_sources_to_model", "sourceIds": ["ds1"], "modelId": "m2"}],
        )
    assert result.is_error is True
    assert result.structured_content["code"] == "data_model.migration_conflict"
    assert result.structured_content["httpStatus"] == 422

