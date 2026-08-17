"""Testes do apply via CRUD HTTP no tool tv_dashboard_copilot."""

from __future__ import annotations

from app.infrastructure.tools.tv_dashboard_copilot_tool import TvDashboardCopilotTool


class _FakeCrudGateway:
    def __init__(self, *, commands=None, fail_at_index: int | None = None):
        self.preview_calls = []
        self.crud_calls = []
        self._commands = commands or []
        self._fail_at_index = fail_at_index
        self._created_playlist = "pl-created"
        self._created_slide = "sl-created"

    def preview_patch(self, envelope, *, access_token, include_fingerprint=True):
        self.preview_calls.append((envelope, access_token, include_fingerprint))
        return {
            "_ok": True,
            "_httpStatus": 200,
            "ok": True,
            "data": {
                "ok": True,
                "persisted": False,
                "executionMode": "crud_http",
                "baseRevision": 10,
                "target": envelope.get("target") or {},
                "appliedOps": [c.get("op") for c in self._commands],
                "sideEffectHints": ["reload_playlist"],
                "nativeConfig": {"version": 5, "blocks": []},
                "httpCommands": list(self._commands),
            },
        }

    def apply_patch(self, envelope, *, access_token):
        raise AssertionError("apply_patch must not be used for persistence")

    def execute_crud_command(self, command, *, access_token, expected_revision=None):
        idx = len(self.crud_calls)
        self.crud_calls.append(
            {
                "command": dict(command),
                "access_token": access_token,
                "expected_revision": expected_revision,
            }
        )
        if self._fail_at_index is not None and idx == self._fail_at_index:
            return {
                "_ok": False,
                "_httpStatus": 409,
                "ok": False,
                "message": "revision conflict",
            }

        op = str(command.get("op") or "")
        data: dict = {"ok": True}
        if op == "create_playlist":
            data = {"id": self._created_playlist, "name": "Nova"}
        elif op in {"add_blank_slide", "add_slide_from_preset"}:
            data = {"id": self._created_slide, "title": "Slide"}

        next_rev = (expected_revision or 10) + 1
        return {
            "_ok": True,
            "_httpStatus": 200 if command.get("method") != "POST" else 201,
            "ok": True,
            "data": data,
            "playlistRevision": next_rev,
        }


def test_preview_includes_http_commands():
    gateway = _FakeCrudGateway(
        commands=[
            {
                "method": "PATCH",
                "path": "/playlists/p1/slides/s1",
                "body": {"nativeConfig": {}},
                "op": "native_config_batch",
                "requiresIfMatch": True,
                "expectedRevision": 10,
            }
        ]
    )
    tool = TvDashboardCopilotTool(gateway=gateway)
    result = tool.execute(
        {
            "mode": "preview",
            "target": {"playlistId": "p1", "slideId": "s1"},
            "ops": [{"op": "upsert_block", "block": {"id": "b1"}}],
        },
        access_token="tok",
    )
    assert result.metadata["mode"] == "preview"
    assert result.metadata["sensitivity"] == "read"
    assert isinstance(result.data.get("httpCommands"), list)
    assert len(result.data["httpCommands"]) == 1
    assert gateway.crud_calls == []


def test_apply_plans_then_executes_crud_sequentially():
    commands = [
        {
            "method": "PATCH",
            "path": "/playlists/p1/slides/s1",
            "body": {"title": "A"},
            "op": "update_slide",
            "requiresIfMatch": True,
            "expectedRevision": 10,
        },
        {
            "method": "PATCH",
            "path": "/playlists/p1/slides/s1",
            "body": {"nativeConfig": {"version": 5}},
            "op": "native_config_batch",
            "requiresIfMatch": True,
            "expectedRevision": 10,
        },
    ]
    gateway = _FakeCrudGateway(commands=commands)
    tool = TvDashboardCopilotTool(gateway=gateway)
    result = tool.execute(
        {
            "mode": "apply",
            "target": {"playlistId": "p1", "slideId": "s1"},
            "ops": [
                {"op": "update_slide", "title": "A"},
                {"op": "upsert_block", "block": {"id": "b1"}},
            ],
        },
        access_token="tok",
    )

    assert len(gateway.preview_calls) == 1
    assert len(gateway.crud_calls) == 2
    assert gateway.crud_calls[0]["expected_revision"] == 10
    assert gateway.crud_calls[1]["expected_revision"] == 11
    assert result.data["ok"] is True
    assert result.data["persisted"] is True
    assert result.data["revision"] == 12
    assert result.metadata["path"] == "/playlists (crud)"
    assert result.metadata["persisted"] is True
    assert len(result.data["executedRequests"]) == 2
    assert result.data.get("nativeConfig") == {"version": 5, "blocks": []}
    assert result.data.get("sideEffectHints") == ["reload_playlist"]


def test_apply_stops_on_409_without_further_calls():
    commands = [
        {
            "method": "PATCH",
            "path": "/playlists/p1/slides/s1",
            "body": {"title": "A"},
            "op": "update_slide",
            "requiresIfMatch": True,
        },
        {
            "method": "DELETE",
            "path": "/playlists/p1/slides/s1",
            "op": "delete_slide",
            "requiresIfMatch": True,
        },
    ]
    gateway = _FakeCrudGateway(commands=commands, fail_at_index=0)
    tool = TvDashboardCopilotTool(gateway=gateway)
    result = tool.execute(
        {
            "mode": "apply",
            "target": {"playlistId": "p1", "slideId": "s1"},
            "ops": [{"op": "update_slide", "title": "A"}, {"op": "delete_slide"}],
        },
        access_token="tok",
    )

    assert len(gateway.crud_calls) == 1
    assert result.data["ok"] is False
    assert result.data["persisted"] is False
    assert result.metadata["httpStatus"] == 409
    assert result.data["executedRequests"][0]["status"] == 409


def test_apply_substitutes_playlist_id_after_create():
    commands = [
        {
            "method": "POST",
            "path": "/playlists",
            "body": {"name": "Nova"},
            "op": "create_playlist",
            "requiresIfMatch": False,
        },
        {
            "method": "POST",
            "path": "/playlists/{playlistId}/slides/from-preset",
            "body": {"presetKey": "kpi"},
            "op": "add_slide_from_preset",
            "requiresIfMatch": False,
        },
        {
            "method": "PATCH",
            "path": "/playlists/{playlistId}/slides/{slideId}",
            "body": {"nativeConfig": {"version": 5}},
            "op": "native_config_batch",
            "requiresIfMatch": True,
            "expectedRevision": 10,
        },
    ]
    gateway = _FakeCrudGateway(commands=commands)
    tool = TvDashboardCopilotTool(gateway=gateway)
    result = tool.execute(
        {
            "mode": "apply",
            "target": {},
            "ops": [
                {"op": "create_playlist", "name": "Nova", "seedPresetKeys": ["kpi"]},
                {"op": "upsert_block", "block": {"id": "b1"}},
            ],
        },
        access_token="tok",
    )

    assert result.data["ok"] is True
    assert len(gateway.crud_calls) == 3
    assert gateway.crud_calls[1]["command"]["path"] == (
        "/playlists/pl-created/slides/from-preset"
    )
    assert gateway.crud_calls[2]["command"]["path"] == (
        "/playlists/pl-created/slides/sl-created"
    )
    assert "{playlistId}" not in gateway.crud_calls[1]["command"]["path"]
    assert "{slideId}" not in gateway.crud_calls[2]["command"]["path"]


def test_apply_fails_when_http_commands_missing():
    gateway = _FakeCrudGateway(commands=[])
    tool = TvDashboardCopilotTool(gateway=gateway)
    result = tool.execute(
        {
            "mode": "apply",
            "target": {"playlistId": "p1", "slideId": "s1"},
            "ops": [{"op": "update_slide", "title": "X"}],
        },
        access_token="tok",
    )
    assert result.data["ok"] is False
    assert result.data["persisted"] is False
    assert "httpCommands" in result.data["message"]
    assert gateway.crud_calls == []
