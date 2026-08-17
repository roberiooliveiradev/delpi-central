"""Planner: ops tipadas → comandos CRUD allowlisted (sem persistência)."""

from __future__ import annotations

import pytest

from tv_app.application.services.data.tv_copilot_http_command_planner_service import (
    TvCopilotHttpCommandPlannerService,
)

PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"
SLIDE_ID = "11111111-1111-1111-1111-111111111111"


def test_coalesces_native_config_ops_into_single_patch():
    cmds = TvCopilotHttpCommandPlannerService.build(
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
    cmds = TvCopilotHttpCommandPlannerService.build(
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
    cmds = TvCopilotHttpCommandPlannerService.build(
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
            tv_copilot_http_command_planner_service as mod,
        )

        mod._cmd(method="POST", path="/admin/secret", op="x")


def test_delete_slide_and_reorder():
    cmds = TvCopilotHttpCommandPlannerService.build(
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
