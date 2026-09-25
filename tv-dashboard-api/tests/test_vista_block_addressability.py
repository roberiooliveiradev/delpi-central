"""VISTA-BLOCK-ADDRESSABILITY-001 — compact blockIndex for GPT Actions READ."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.response_compact import (
    GPT_ACTIONS_RESPONSE_MAX_BYTES,
    actions_response_sizes,
    content_preview_from_block,
    exceeds_actions_budget,
    iter_block_index_items,
    project_block_index,
    project_block_index_item,
    utf8_size,
)


def _four_card_labels_native() -> dict:
    """Structural fixture: 4 cards × 4 text labels + sources (no business hardcode in logic)."""
    cards = [
        ("grp-a", "Card A"),
        ("grp-b", "Card B"),
        ("grp-c", "Card C"),
        ("grp-d", "Card D"),
    ]
    label_suffixes = ["t1", "t2", "t3", "t4"]
    blocks: list[dict] = [
        {
            "id": "ds-main",
            "type": "data_source",
            "dataBinding": {
                "operationId": "op.demo",
                "params": {"branch": "01"},
                "label": "Fonte principal",
            },
        }
    ]
    for gi, (gid, gname) in enumerate(cards):
        for li, suffix in enumerate(label_suffixes):
            blocks.append(
                {
                    "id": f"lbl-{gid}-{suffix}",
                    "type": "text",
                    "groupId": gid,
                    "frame": {"x": gi * 40, "y": li * 12, "w": 36, "h": 10},
                    "content": f"{gname} · {suffix}",
                    "style": {"fontSize": 18, "zIndex": 10 + li},
                }
            )
        blocks.append(
            {
                "id": f"kpi-{gid}",
                "type": "kpi_view",
                "groupId": gid,
                "frame": {"x": gi * 40, "y": 60, "w": 36, "h": 28},
                "dataSourceId": "ds-main",
            }
        )
    # Pad to ~70 blocks for budget regression.
    while len(blocks) < 70:
        i = len(blocks)
        blocks.append(
            {
                "id": f"pad-{i}",
                "type": "shape",
                "frame": {"x": i % 10 * 8, "y": 100 + (i // 10), "w": 6, "h": 6},
                "content": f"shape-{i}",
            }
        )
    return {"version": 5, "blocks": blocks}


def test_project_block_index_ids_subset_of_persisted():
    native = _four_card_labels_native()
    index = project_block_index(native, slide_id="s1", revision=7)
    source_ids = {
        str(b.get("id"))
        for b in native["blocks"]
        if isinstance(b, dict) and str(b.get("id") or "").strip()
    }
    index_ids = {str(item["id"]) for item in index["items"]}
    assert index_ids <= source_ids
    assert index["total"] == len(source_ids)
    assert index["revision"] == 7
    assert index["slideId"] == "s1"
    assert index["truncated"] is False


def test_content_preview_truncates_and_skips_resolved():
    long_text = "alpha " * 40
    preview = content_preview_from_block({"type": "text", "id": "t1", "content": long_text})
    assert preview is not None
    assert len(preview) <= 81
    assert "…" in preview
    # resolved must never be used
    assert (
        content_preview_from_block(
            {
                "id": "t2",
                "type": "text",
                "content": "",
                "resolved": {"displayText": "SECRET_ROW_DATA"},
            }
        )
        is None
    )


def test_label_addressability_without_selected_ids():
    native = _four_card_labels_native()
    index = project_block_index(native, slide_id="s1", revision=1)
    labels = [i for i in index["items"] if i["type"] == "text" and str(i["id"]).startswith("lbl-")]
    assert len(labels) == 16
    groups = {i.get("groupId") for i in labels}
    assert groups == {"grp-a", "grp-b", "grp-c", "grp-d"}
    previews = {i.get("contentPreview") for i in labels}
    assert len(previews) == 16


def test_editor_focus_includes_block_index_without_selection():
    writes = MagicMock()
    playlist_id = str(uuid4())
    sid = str(uuid4())
    native = _four_card_labels_native()
    writes.get_playlist.return_value = {
        "id": playlist_id,
        "name": "Painel",
        "dataDefaults": {},
    }
    writes.list_slides.return_value = [
        {"id": sid, "title": "Slide", "sortOrder": 0, "nativeConfig": native},
    ]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 42
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")

    with (
        patch.object(
            dispatch._access,
            "resolve",
            return_value=SimpleNamespace(
                can_read=True,
                can_edit=True,
                level="owner",
                playlist={"id": playlist_id, "name": "Painel", "dataDefaults": {}},
            ),
        ),
        patch.object(dispatch, "_actor", return_value="u1"),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.assert_permission",
            return_value=None,
        ),
    ):
        out = dispatch.get_playlist_context(
            user=user,
            playlist_id=playlist_id,
            scope="editorFocus",
            preview_slide_id=sid,
        )

    assert out["scope"] == "editorFocus"
    assert "nativeConfig" not in (out.get("focusedSlide") or {})
    assert "blockIndex" in out
    assert out["blockIndex"]["revision"] == 42
    assert out["blockIndex"]["total"] == 70
    assert out["blockIndex"]["returned"] == 70
    assert out["currentRevision"] == 42
    assert "blockIndex" in out["note"]
    sizes = actions_response_sizes(out)
    assert all(v <= GPT_ACTIONS_RESPONSE_MAX_BYTES for v in sizes.values())


def test_auto_downgrade_retains_block_index_for_70_blocks():
    writes = MagicMock()
    playlist_id = str(uuid4())
    sid = str(uuid4())
    native = _four_card_labels_native()
    # Inflate authored fields so full scope exceeds Actions budget.
    pad = "P" * 3000
    for block in native["blocks"]:
        if block.get("type") == "text":
            block["style"] = {**(block.get("style") or {}), "notes": pad}
    native["speakerNotes"] = pad * 30
    writes.get_playlist.return_value = {
        "id": playlist_id,
        "name": "Painel grande",
        "dataDefaults": {},
    }
    writes.list_slides.return_value = [
        {"id": sid, "title": "Dense", "sortOrder": 0, "nativeConfig": native},
    ]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 1150
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")

    with (
        patch.object(
            dispatch._access,
            "resolve",
            return_value=SimpleNamespace(
                can_read=True,
                can_edit=True,
                level="owner",
                playlist={"id": playlist_id, "name": "Painel grande", "dataDefaults": {}},
            ),
        ),
        patch.object(dispatch, "_actor", return_value="u1"),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.assert_permission",
            return_value=None,
        ),
        patch(
            "tv_app.application.services.data.brand_logo_media_service.BrandLogoMediaService.list_brand_assets",
            return_value={},
        ),
        patch(
            "tv_app.application.services.data.brand_logo_media_service.BrandLogoMediaService.list_playlist_assets",
            return_value=[],
        ),
    ):
        out = dispatch.get_playlist_context(
            user=user,
            playlist_id=playlist_id,
            preview_slide_id=sid,
            scope="full",
        )

    assert out["scope"] == "editorFocus"
    assert out.get("scopeDowngraded") is True
    assert out.get("scopeDowngradeReason") == "response_budget"
    assert "nativeConfig" not in (out.get("focusedSlide") or {})
    assert out["blockIndex"]["total"] == 70
    source_ids = {str(b["id"]) for b in native["blocks"]}
    assert {i["id"] for i in out["blockIndex"]["items"]} <= source_ids
    assert utf8_size(out) < GPT_ACTIONS_RESPONSE_MAX_BYTES
    assert not exceeds_actions_budget(out)


def test_object_query_returns_object_matches():
    writes = MagicMock()
    playlist_id = str(uuid4())
    sid = str(uuid4())
    native = _four_card_labels_native()
    writes.get_playlist.return_value = {"id": playlist_id, "name": "P", "dataDefaults": {}}
    writes.list_slides.return_value = [
        {"id": sid, "title": "S", "sortOrder": 0, "nativeConfig": native},
    ]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 3
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")

    with (
        patch.object(
            dispatch._access,
            "resolve",
            return_value=SimpleNamespace(
                can_read=True,
                can_edit=True,
                level="owner",
                playlist={"id": playlist_id, "name": "P", "dataDefaults": {}},
            ),
        ),
        patch.object(dispatch, "_actor", return_value="u1"),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.assert_permission",
            return_value=None,
        ),
    ):
        out = dispatch.get_playlist_context(
            user=user,
            playlist_id=playlist_id,
            scope="editorFocus",
            preview_slide_id=sid,
            object_query="Card B",
            object_types="text",
        )

    matches = out.get("objectMatches") or []
    assert matches
    assert all(m["type"] == "text" for m in matches)
    assert all("Card B" in (m.get("contentPreview") or "") for m in matches)
    assert {m["id"] for m in matches} <= {b["id"] for b in native["blocks"]}


def test_block_index_pagination_is_explicit():
    native = {"blocks": [{"id": f"b{i}", "type": "text", "content": f"c{i}"} for i in range(12)]}
    page1 = project_block_index(native, slide_id="s", revision=1, cursor=0, limit=5)
    assert page1["returned"] == 5
    assert page1["truncated"] is True
    assert page1["nextCursor"] == "5"
    page2 = project_block_index(
        native, slide_id="s", revision=1, cursor=page1["nextCursor"], limit=5
    )
    assert page2["returned"] == 5
    ids = [i["id"] for i in page1["items"]] + [i["id"] for i in page2["items"]]
    page3 = project_block_index(native, slide_id="s", revision=1, cursor=page2["nextCursor"], limit=5)
    ids += [i["id"] for i in page3["items"]]
    assert len(ids) == 12
    assert len(set(ids)) == 12


def test_invented_block_id_still_fail_closed():
    from tv_app.application.services.data.presentation_mutation import (
        PresentationPatchError,
        PresentationPatchService,
    )

    svc = PresentationPatchService()
    cfg = {"version": 1, "blocks": [{"id": "real-1", "type": "text", "content": "ok"}]}
    with pytest.raises(PresentationPatchError) as caught:
        svc._op_upsert_block(
            cfg,
            {
                "op": "upsert_block",
                "blockId": "invented",
                "block": {"type": "text", "content": "x"},
            },
        )
    assert "invented" in str(caught.value)
    assert caught.value.details.get("reason") == "TARGET_BLOCK_NOT_FOUND"
    assert caught.value.details.get("requestedBlockId") == "invented"
    assert len(cfg["blocks"]) == 1


def test_e2e_resolve_and_update_existing_labels_without_create():
    """READ blockIndex → PREPARE upserts on INFORMED ids → block count unchanged."""
    from tv_app.application.services.data.presentation_mutation import PresentationPatchService

    writes = MagicMock()
    playlist_id = str(uuid4())
    sid = str(uuid4())
    native = _four_card_labels_native()
    pad = "Z" * 2800
    native["speakerNotes"] = pad * 25
    for block in native["blocks"]:
        if block.get("type") in {"text", "shape"}:
            block["style"] = {**(block.get("style") or {}), "pad": pad}
    writes.get_playlist.return_value = {"id": playlist_id, "name": "E2E", "dataDefaults": {}}
    writes.list_slides.return_value = [
        {"id": sid, "title": "Labels", "sortOrder": 0, "nativeConfig": native},
    ]
    writes.list_sections.return_value = []
    writes.get_revision.return_value = 100
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    user = SimpleNamespace(is_superadmin=True, permissions=[], id="u1")

    with (
        patch.object(
            dispatch._access,
            "resolve",
            return_value=SimpleNamespace(
                can_read=True,
                can_edit=True,
                level="owner",
                playlist={"id": playlist_id, "name": "E2E", "dataDefaults": {}},
            ),
        ),
        patch.object(dispatch, "_actor", return_value="u1"),
        patch(
            "tv_app.application.gpt_actions.dispatch_service.assert_permission",
            return_value=None,
        ),
        patch(
            "tv_app.application.services.data.brand_logo_media_service.BrandLogoMediaService.list_brand_assets",
            return_value={},
        ),
        patch(
            "tv_app.application.services.data.brand_logo_media_service.BrandLogoMediaService.list_playlist_assets",
            return_value=[],
        ),
    ):
        ctx = dispatch.get_playlist_context(
            user=user,
            playlist_id=playlist_id,
            preview_slide_id=sid,
            scope="full",
        )

    assert ctx.get("scopeDowngraded") is True
    label_ids = sorted(
        item["id"]
        for item in ctx["blockIndex"]["items"]
        if item["type"] == "text" and str(item["id"]).startswith("lbl-")
    )
    assert len(label_ids) == 16

    before_count = len(native["blocks"])
    before_by_id = {str(b["id"]): dict(b) for b in native["blocks"]}
    ops = [
        {
            "op": "upsert_block",
            "blockId": bid,
            "block": {"content": f"UPDATED::{bid}"},
        }
        for bid in label_ids
    ]
    patch_svc = PresentationPatchService()
    # Seed slide native into preview path via writes mock used by patch — call op directly
    # on a cloned config to prove fail-closed identity + count stability.
    working = {"version": 5, "blocks": [dict(b) for b in native["blocks"]]}
    for op in ops:
        patch_svc._op_upsert_block(working, op)

    after_ids = [str(b.get("id")) for b in working["blocks"] if isinstance(b, dict)]
    assert len(after_ids) == before_count
    assert set(after_ids) == set(before_by_id)
    for bid in label_ids:
        updated = next(b for b in working["blocks"] if b.get("id") == bid)
        assert updated.get("content") == f"UPDATED::{bid}"
    untouched = [
        b
        for b in working["blocks"]
        if str(b.get("id")) not in set(label_ids)
    ]
    for block in untouched:
        assert block.get("content") == before_by_id[str(block["id"])].get("content")
    native = {
        "blocks": [
            {"id": "keep-me", "type": "heading", "content": "Title"},
            {"type": "text", "content": "missing id skipped"},
        ]
    }
    items = iter_block_index_items(native)
    assert [i["id"] for i in items] == ["keep-me"]
    assert project_block_index_item({"type": "text", "content": "no-id"}) is None
