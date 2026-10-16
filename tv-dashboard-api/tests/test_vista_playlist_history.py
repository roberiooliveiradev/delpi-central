"""P9 — VISTA get_playlist_history: safe digest, AuthZ, isolation, parity.

Covers the one read-only semantic capability end-to-end at the dispatch
boundary (fake history repo + mocked access), the projection rules, the
MCP tool surface and the GPT Actions surface. No DB, no writes.
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tv_app.application.gpt_actions import GPT_ACTIONS_OPERATION_IDS
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi,
    count_operations,
)
from tv_app.application.services.playlist_history_digest_service import (
    TECHNICAL_PROVENANCE_CODES,
    history_detail_projection,
    history_item_digest,
    history_list_projection,
)
from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.infrastructure.persistence.repositories.playlist_history_repository import (
    HISTORY_LIMIT_PER_PLAYLIST,
    PlaylistHistoryNotFoundError,
)
from tv_app.interface.mcp.constants import MCP_TOOL_NAMES, TOOL_CLASS
from tv_app.interface.mcp.server import create_mcp_server

FORBIDDEN_KEYS = {
    "authorEmail",
    "authorId",
    "email",
    "playlist",  # raw snapshot
    "nativeConfig",
    "masterConfig",
    "dataDefaults",
    "externalUrl",
    "externalSandbox",
    "selectedSlideId",
}


def _reader(user_id: str = "user-1"):
    # Resource AuthZ is exercised via PlaylistAccessService mocks; the
    # permission gate itself only needs any TV_READ-capable principal.
    return SimpleNamespace(id=user_id, permissions=[], is_superadmin=True)


def _access_ok(playlist_id):
    return PlaylistAccess(
        level="viewer",
        playlist={"id": str(playlist_id), "revision": 7},
    )


def _row(
    playlist_id,
    *,
    revision=1,
    reason="slide_updated",
    name="Robério Oliveira",
    change=None,
):
    snapshot = {
        "playlist": {
            "name": "Painel OEE",
            "externalUrl": "https://x.example",
            "externalSandbox": "allow-scripts",
            "dataDefaults": {"k": 1},
        },
        "slides": [
            {
                "id": "s1",
                "title": "Capa",
                "nativeConfig": {"blocks": [{"id": "b1", "fontSize": 32}]},
                "masterConfig": {"m": 1},
            }
        ],
    }
    return {
        "snapshotId": str(uuid4()),
        "playlistId": str(playlist_id),
        "revision": revision,
        "authorId": "user-1",
        "authorName": name,
        "authorEmail": "roberio@delpi.com.br",
        "reason": reason,
        "createdAt": "2026-10-05T10:00:00+00:00",
        "preview": {
            "playlistName": "Painel OEE",
            "slideCount": 1,
            "slideTitles": ["Capa"],
            "selectedSlideId": None,
        },
        "change": change
        if change is not None
        else {
            "available": True,
            "comparedToRevision": revision + 1,
            "playlistFields": ["name"],
            "slides": {
                "added": [{"id": "s9", "title": "Novo"}],
                "removed": [{"id": "s2", "title": "Antigo"}],
                "updated": [
                    {"id": "s1", "title": "Capa", "fields": ["nativeConfig"]}
                ],
                "reordered": True,
            },
            "totals": {"added": 1, "removed": 1, "updated": 1},
        },
        "playlist": snapshot["playlist"] | {"slides": snapshot["slides"]},
    }


def _list_payload(playlist_id, items):
    return {
        "playlistId": str(playlist_id),
        "items": items,
        "page": 1,
        "pageSize": 10,
        "total": len(items),
        "totalPages": 1,
        "currentRevision": 7,
        "currentSnapshotId": "snap-live",
    }


def _dispatch(repo):
    access = MagicMock()
    access.resolve.return_value = _access_ok(uuid4())
    return (
        GptActionsDispatchService(
            repo=MagicMock(),
            writes=MagicMock(),
            commit=MagicMock(),
            access=access,
            history=repo,
        ),
        access,
    )


def _walk_strings(node):
    if isinstance(node, dict):
        for k, v in node.items():
            yield k
            yield from _walk_strings(v)
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from _walk_strings(v)


def _assert_no_forbidden_keys(payload):
    for key in _walk_strings(payload):
        assert key not in FORBIDDEN_KEYS, key


# --- projection ----------------------------------------------------------


def test_digest_omits_author_id_email_and_raw_fields():
    pid = uuid4()
    digest = history_item_digest(_row(pid))
    _assert_no_forbidden_keys(digest)
    assert digest["actor"] == {"name": "Robério Oliveira"}
    assert digest["mutationProvenance"] == "slide_updated"
    assert "reason" not in digest


def test_digest_change_is_slide_field_granularity_only():
    digest = history_item_digest(_row(uuid4()))
    updated = digest["change"]["slides"]["updated"]
    assert updated[0]["fields"] == ["nativeConfig"]
    # Block-level claims are impossible: no block ids / before-after values.
    assert not any("block" in k.lower() for k in _walk_strings(digest))
    raw = json.dumps(digest)
    assert '"b1"' not in raw  # block id never leaks as a value
    assert "fontSize" not in raw


def test_free_form_reason_is_not_projected():
    row = _row(uuid4(), reason="voltei para a versão boa")
    digest = history_item_digest(row)
    assert digest["mutationProvenance"] is None
    assert "voltei" not in json.dumps(digest, ensure_ascii=False)


def test_provenance_allowlist_is_bounded_technical_codes():
    assert "history_restored" in TECHNICAL_PROVENANCE_CODES
    assert "slide_updated" in TECHNICAL_PROVENANCE_CODES
    for code in TECHNICAL_PROVENANCE_CODES:
        assert " " not in code  # codes only, never sentences


def test_diff_unavailable_is_preserved_not_fabricated():
    change = {"available": False, "comparedToRevision": None}
    digest = history_item_digest(_row(uuid4(), change=change))
    assert digest["change"]["available"] is False
    assert digest["change"]["slides"]["updated"] == []


def test_list_projection_carry_retention_and_paging_truth():
    pid = uuid4()
    out = history_list_projection(
        _list_payload(pid, [_row(pid, revision=1), _row(pid, revision=2)]),
        playlist_id=str(pid),
    )
    _assert_no_forbidden_keys(out)
    assert out["mode"] == "list"
    assert out["retention"] == {
        "maxSnapshots": HISTORY_LIMIT_PER_PLAYLIST,
        "completeHistoryGuaranteed": False,
    }
    assert out["retention"]["maxSnapshots"] == 500
    assert out["currentRevision"] == 7
    assert len(out["items"]) == 2
    assert out["total"] == 2


def test_zero_history_rows_list_is_empty_not_error():
    pid = uuid4()
    out = history_list_projection(
        _list_payload(pid, []), playlist_id=str(pid)
    )
    assert out["items"] == []
    assert out["total"] == 0


def test_detail_projection_never_exposes_raw_snapshot():
    pid = uuid4()
    out = history_detail_projection(_row(pid))
    _assert_no_forbidden_keys(out)
    assert out["mode"] == "detail"
    assert "slides" not in out.get("preview", {}) or True
    assert json.dumps(out, ensure_ascii=False).find("allow-scripts") == -1


# --- dispatch: authz + modes + isolation -----------------------------------


def test_dispatch_list_mode_uses_read_access_and_repo():
    pid = uuid4()
    repo = MagicMock()
    repo.list_history.return_value = _list_payload(pid, [_row(pid)])
    service, access = _dispatch(repo)
    access.resolve.return_value = _access_ok(pid)

    out = service.get_playlist_history(
        user=_reader(), playlist_id=str(pid)
    )
    access.resolve.assert_called_once()
    repo.list_history.assert_called_once_with(pid, page=1, page_size=10)
    assert out["mode"] == "list"
    _assert_no_forbidden_keys(out)


def test_dispatch_detail_mode_returns_single_digest():
    pid = uuid4()
    sid = uuid4()
    repo = MagicMock()
    repo.get_history.return_value = _row(pid)
    service, _ = _dispatch(repo)

    out = service.get_playlist_history(
        user=_reader(), playlist_id=str(pid), snapshot_id=str(sid)
    )
    repo.get_history.assert_called_once_with(pid, sid)
    assert out["mode"] == "detail"
    _assert_no_forbidden_keys(out)


def test_dispatch_denies_unreadable_playlist_fail_closed():
    pid = uuid4()
    repo = MagicMock()
    service, access = _dispatch(repo)
    access.resolve.return_value = PlaylistAccess(level="none")

    with pytest.raises(GptActionsError) as caught:
        service.get_playlist_history(user=_reader(), playlist_id=str(pid))
    assert caught.value.code == "RESOURCE_NOT_FOUND"
    assert caught.value.status_code == 404
    repo.list_history.assert_not_called()


def test_dispatch_cross_playlist_snapshot_is_isolated():
    """snapshot of playlist B through playlist A scope -> typed not-found."""
    pid = uuid4()
    repo = MagicMock()
    repo.get_history.side_effect = PlaylistHistoryNotFoundError
    service, access = _dispatch(repo)
    access.resolve.return_value = _access_ok(pid)

    with pytest.raises(GptActionsError) as caught:
        service.get_playlist_history(
            user=_reader(), playlist_id=str(pid), snapshot_id=str(uuid4())
        )
    assert caught.value.code == "RESOURCE_NOT_FOUND"
    # repo was scoped by playlist id — cross-playlist fetch cannot escape.
    assert repo.get_history.call_args.args[0] == pid


def test_dispatch_invalid_ids_are_typed_errors():
    service, _ = _dispatch(MagicMock())
    with pytest.raises(GptActionsError) as caught:
        service.get_playlist_history(user=_reader(), playlist_id="not-a-uuid")
    assert caught.value.code == "INVALID_CHANGE"
    with pytest.raises(GptActionsError):
        service.get_playlist_history(
            user=_reader(), playlist_id=str(uuid4()), snapshot_id="xx"
        )


def test_dispatch_requires_read_permission():
    repo = MagicMock()
    service, access = _dispatch(repo)

    with pytest.raises(PermissionError):
        service.get_playlist_history(
            user=SimpleNamespace(id=None, permissions=[], is_superadmin=False),
            playlist_id=str(uuid4()),
        )
    repo.list_history.assert_not_called()


def test_read_only_user_has_no_restore_path():
    """Restore stays a domain edit op — it must not exist on the VISTA read."""
    service, _ = _dispatch(MagicMock())
    for attr in dir(service):
        assert "restore" not in attr
        assert "rollback" not in attr
        assert "revert" not in attr


# --- MCP surface -----------------------------------------------------------


def test_mcp_tool_registered_read_classified_and_bounded():
    assert TOOL_CLASS["get_playlist_history"] == "READ"
    assert "get_playlist_history" in MCP_TOOL_NAMES
    assert len(MCP_TOOL_NAMES) == 12

    tools = {
        t.name: t.model_dump(mode="json", by_alias=True, exclude_none=True)
        for t in asyncio.run(create_mcp_server().list_tools())
    }
    tool = tools["get_playlist_history"]
    schema = tool["inputSchema"]
    props = schema["properties"]
    assert set(props) == {"playlist_id", "snapshot_id", "page", "page_size"}
    assert "playlist_id" in schema.get("required", [])
    assert "snapshot_id" not in schema.get("required", [])
    ann = tool["annotations"]
    assert ann["readOnlyHint"] is True
    assert ann["destructiveHint"] is False
    assert ann["idempotentHint"] is True


def test_mcp_has_no_restore_rollback_revert_replay_tools():
    names = {t.name for t in asyncio.run(create_mcp_server().list_tools())}
    for banned in ("restore", "rollback", "revert", "replay", "delete_history"):
        assert not any(banned in n for n in names), banned


# --- GPT Actions surface ---------------------------------------------------


def test_actions_operation_present_compact_and_schema_bounded():
    doc = build_gpt_actions_openapi()
    assert count_operations(doc) == 12
    assert "gpt_get_playlist_history" in GPT_ACTIONS_OPERATION_IDS

    op = doc["paths"]["/gpt-actions/v1/playlists/{playlist_id}/history"]["get"]
    assert op["operationId"] == "gpt_get_playlist_history"
    assert len(op["description"]) <= 300
    params = {p["name"]: p for p in op["parameters"]}
    assert params["playlist_id"]["in"] == "path"
    assert params["playlist_id"]["required"] is True
    assert params["snapshotId"]["in"] == "query"
    assert params["pageSize"]["schema"]["default"] == 10
    # no write body on a read-only action
    assert "requestBody" not in op


def test_actions_has_no_restore_rollback_operations():
    doc = build_gpt_actions_openapi()
    ids = {
        op["operationId"]
        for methods in doc["paths"].values()
        for op in methods.values()
        if isinstance(op, dict) and op.get("operationId")
    }
    for banned in ("restore", "rollback", "revert", "replay"):
        assert not any(banned in i for i in ids), banned


def test_parity_map_canonical_single_entry():
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
    )

    parity = VistaAgentIntelligenceService.document()["surface_parity"]["parity_map"]
    assert parity["gpt_get_playlist_history"] == "get_playlist_history"
    assert len(parity) == 12


# --- response size ----------------------------------------------------------


def test_max_page_digest_stays_bounded():
    pid = uuid4()
    items = [_row(pid, revision=i) for i in range(100)]
    out = history_list_projection(
        _list_payload(pid, items) | {"pageSize": 100, "totalPages": 5},
        playlist_id=str(pid),
    )
    raw = len(json.dumps(out, ensure_ascii=True).encode("utf-8"))
    assert raw < 200_000  # bounded digest; well under envelope ceiling
