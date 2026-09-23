"""Planner: ops tipadas → comandos CRUD allowlisted (sem persistência)."""

from __future__ import annotations

import pytest

from tv_app.application.services.data.presentation_http_command_planner_service import (
    PresentationHttpCommandPlannerService,
)

PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"
SLIDE_ID = "11111111-1111-1111-1111-111111111111"


def test_coalesces_native_config_ops_into_single_patch():
    cmds = PresentationHttpCommandPlannerService.build(
        ops=[
            {
                "op": "upsert_block",
                "block": {"id": "t1", "type": "text", "content": "Hi"},
            },
            {"op": "delete_block", "blockId": "old"},
            {
                "op": "bind_visual",
                "visualId": "kpi-1",
                "dataSourceId": "src-a",
            },
        ],
        target={"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
        native_config={"version": 5, "blocks": [{"id": "t1", "type": "text"}]},
        base_revision=3,
    )
    assert len(cmds) == 1
    assert cmds[0]["method"] == "PATCH"
    assert cmds[0]["path"] == f"/playlists/{PLAYLIST_ID}/slides/{SLIDE_ID}"
    assert cmds[0]["op"] == "native_config_batch"
    assert cmds[0]["body"]["nativeConfig"]["blocks"][0]["id"] == "t1"
    assert cmds[0]["expectedRevision"] == 3
    assert cmds[0]["requiresIfMatch"] is True


def test_blank_slide_then_native_config_uses_slide_placeholder():
    cmds = PresentationHttpCommandPlannerService.build(
        ops=[
            {"op": "add_blank_slide", "title": "Novo"},
            {
                "op": "upsert_block",
                "block": {"id": "t1", "type": "text", "content": "Hi"},
            },
        ],
        target={"playlistId": PLAYLIST_ID},
        native_config={"version": 5, "blocks": []},
        base_revision=1,
    )
    assert cmds[0]["method"] == "POST"
    assert cmds[0]["path"] == f"/playlists/{PLAYLIST_ID}/slides"
    assert cmds[1]["path"] == f"/playlists/{PLAYLIST_ID}/slides/{{slideId}}"
    assert cmds[1]["op"] == "native_config_batch"


def test_create_playlist_skips_if_match():
    cmds = PresentationHttpCommandPlannerService.build(
        ops=[{"op": "create_playlist", "name": "Turno"}],
        target={},
        native_config=None,
        base_revision=None,
    )
    assert len(cmds) == 1
    assert cmds[0]["method"] == "POST"
    assert cmds[0]["path"] == "/playlists"
    assert cmds[0]["requiresIfMatch"] is False
    assert "expectedRevision" not in cmds[0]


def test_rejects_path_outside_playlists():
    with pytest.raises(ValueError, match="fora do CRUD"):
        # Força via build interno: path é validado em _cmd.
        from tv_app.application.services.data import (
            presentation_http_command_planner_service as mod,
        )

        mod._cmd(method="POST", path="/admin/secret", op="x")


def test_delete_slide_and_reorder():
    cmds = PresentationHttpCommandPlannerService.build(
        ops=[
            {
                "op": "reorder_slides",
                "items": [{"id": SLIDE_ID, "sortOrder": 0}],
            },
            {"op": "delete_slide"},
        ],
        target={"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
        native_config=None,
        base_revision=9,
    )
    assert cmds[0]["method"] == "POST"
    assert cmds[0]["path"].endswith("/slides/reorder")
    assert cmds[1]["method"] == "DELETE"
    assert cmds[1]["expectedRevision"] == 9


def test_patch_playlist_data_defaults_maps_to_playlist_patch():
    cmds = PresentationHttpCommandPlannerService.build(
        ops=[
            {
                "op": "patch_playlist_data_defaults",
                "dataDefaults": {"branch": "02", "periodDays": 7},
            }
        ],
        target={"playlistId": PLAYLIST_ID},
        native_config=None,
        base_revision=2,
    )
    assert len(cmds) == 1
    assert cmds[0]["method"] == "PATCH"
    assert cmds[0]["path"] == f"/playlists/{PLAYLIST_ID}"
    assert cmds[0]["op"] == "patch_playlist_data_defaults"
    assert cmds[0]["body"] == {"dataDefaults": {"branch": "02", "periodDays": 7}}
    assert cmds[0]["expectedRevision"] == 2


def test_patch_playlist_data_defaults_requires_playlist():
    with pytest.raises(ValueError, match="playlistId"):
        PresentationHttpCommandPlannerService.build(
            ops=[
                {
                    "op": "patch_playlist_data_defaults",
                    "dataDefaults": {"branch": "01"},
                }
            ],
            target={},
            native_config=None,
            base_revision=None,
        )


def test_patch_playlist_data_defaults_requires_object():
    with pytest.raises(ValueError):
        PresentationHttpCommandPlannerService.build(
            ops=[{"op": "patch_playlist_data_defaults", "dataDefaults": "bad"}],
            target={"playlistId": PLAYLIST_ID},
            native_config=None,
            base_revision=None,
        )


SLIDE_B = "33333333-3333-3333-3333-333333333333"


def test_multi_slide_native_configs_emit_one_patch_each():
    cmds = PresentationHttpCommandPlannerService.build(
        ops=[
            {
                "op": "patch_native_config",
                "slideRef": SLIDE_ID,
                "patch": {"background": {"type": "color", "value": "#111111"}},
            },
            {
                "op": "upsert_block",
                "slideRef": SLIDE_B,
                "block": {"id": "t1", "type": "text", "content": "Hi"},
            },
        ],
        target={"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
        native_config={"version": 5, "blocks": []},
        native_configs_by_slide={
            SLIDE_ID: {
                "version": 5,
                "background": {"type": "color", "value": "#111111"},
                "blocks": [],
            },
            SLIDE_B: {
                "version": 5,
                "blocks": [{"id": "t1", "type": "text", "content": "Hi"}],
            },
        },
        base_revision=4,
    )
    native = [c for c in cmds if c["op"] == "native_config_batch"]
    assert len(native) == 2
    assert {c["path"] for c in native} == {
        f"/playlists/{PLAYLIST_ID}/slides/{SLIDE_ID}",
        f"/playlists/{PLAYLIST_ID}/slides/{SLIDE_B}",
    }
    assert all(c.get("expectedRevision") == 4 for c in native)


def test_single_slide_without_by_slide_keeps_legacy_coalesce():
    """Negative sibling: no nativeConfigsBySlide → one PATCH to target slide."""
    cmds = PresentationHttpCommandPlannerService.build(
        ops=[{"op": "upsert_block", "block": {"id": "t1", "type": "text"}}],
        target={"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
        native_config={"version": 5, "blocks": [{"id": "t1", "type": "text"}]},
        native_configs_by_slide=None,
        base_revision=1,
    )
    assert len(cmds) == 1
    assert cmds[0]["path"] == f"/playlists/{PLAYLIST_ID}/slides/{SLIDE_ID}"
