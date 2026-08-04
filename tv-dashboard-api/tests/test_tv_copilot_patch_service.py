"""Testes TvCopilotPatchV1 — preview/apply sem M e sem resolved."""

from __future__ import annotations

from typing import Any

import pytest

from tv_app.application.services.data.tv_copilot_patch_service import (
    TvCopilotPatchError,
    TvCopilotPatchService,
)
from tv_app.application.services.data.tv_copilot_telemetry import (
    reset_copilot_telemetry,
)


class _FakeCatalog:
    def __init__(self, routes: dict[str, dict]) -> None:
        self._routes = routes

    def get_route(self, operation_id: str):
        return self._routes.get(operation_id)


SLIDE_ID = "11111111-1111-1111-1111-111111111111"
PLAYLIST_ID = "00000000-0000-0000-0000-000000000001"


class _FakeRepo:
    def __init__(self) -> None:
        self.slides: dict[str, dict[str, Any]] = {
            SLIDE_ID: {
                "id": SLIDE_ID,
                "nativeConfig": {
                    "version": 5,
                    "blocks": [
                        {
                            "id": "src-a",
                            "type": "data_source",
                            "dataBinding": {
                                "operationId": "op.demo",
                                "params": {"branch": "01"},
                                "displayMode": "auto",
                                "label": "Demo",
                            },
                        },
                        {
                            "id": "kpi-1",
                            "type": "kpi",
                            "dataSourceId": None,
                        },
                    ],
                },
            }
        }
        self.updated: list[dict[str, Any]] = []
        self.created_playlists: list[dict[str, Any]] = []
        self.added_slides: list[dict[str, Any]] = []

    def get_slide(self, slide_id, *, playlist_id=None):
        key = str(slide_id)
        if key not in self.slides:
            from tv_app.infrastructure.persistence.repositories.playlist_repository import (
                SlideNotFoundError,
            )

            raise SlideNotFoundError(key)
        return dict(self.slides[key])

    def get(self, playlist_id):
        return {"id": str(playlist_id), "dataDefaults": {"branch": "01"}}

    def update_slide(self, playlist_id, slide_id, payload, *, actor_user_id, reason):
        self.updated.append(
            {
                "playlist_id": str(playlist_id),
                "slide_id": str(slide_id),
                "payload": payload,
                "actor": actor_user_id,
                "reason": reason,
            }
        )
        cfg = payload.get("nativeConfig")
        if cfg:
            self.slides[SLIDE_ID]["nativeConfig"] = cfg
        return self.slides[SLIDE_ID]

    def create(self, *, name, description, created_by):
        item = {"id": "pl-new", "name": name, "description": description, "createdBy": created_by}
        self.created_playlists.append(item)
        return item

    def add_slide(self, playlist_id, payload, *, actor_user_id, reason):
        slide = {
            "id": f"slide-{len(self.added_slides)+2}",
            **payload,
        }
        self.added_slides.append(slide)
        return slide


class _FakeResolution:
    def resolve_blocks(self, blocks, **kwargs):
        out = []
        for block in blocks:
            item = dict(block)
            item["resolved"] = {"idd": 6.57, "score": 6.57}
            out.append(item)
        return out


@pytest.fixture(autouse=True)
def _reset_telemetry():
    reset_copilot_telemetry()
    yield
    reset_copilot_telemetry()


def _service(repo=None, monkeypatch=None):
    if monkeypatch is not None:

        def _sanitize(cfg, catalog=None):
            cleaned = dict(cfg or {})
            blocks = cleaned.get("blocks")
            if isinstance(blocks, list):
                next_blocks = []
                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    item = dict(block)
                    item.pop("resolved", None)
                    next_blocks.append(item)
                cleaned["blocks"] = next_blocks
            return cleaned

        monkeypatch.setattr(
            "tv_app.application.services.data.tv_copilot_patch_service.sanitize_and_hydrate_comunicado_config",
            _sanitize,
        )
        monkeypatch.setattr(
            "tv_app.application.services.data.tv_copilot_patch_service.validate_comunicado_native_config",
            lambda cfg, user=None, catalog=None: None,
        )
    return TvCopilotPatchService(
        catalog=_FakeCatalog({"op.demo": {"label": "Demo", "operationId": "op.demo"}}),
        repo=repo or _FakeRepo(),
        resolution=_FakeResolution(),
    )


def test_preview_upsert_data_source_and_bind_without_persist(monkeypatch):
    repo = _FakeRepo()
    svc = _service(repo, monkeypatch)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_data_source",
                    "blockId": "src-b",
                    "operationId": "op.demo",
                    "params": {"branch": "02"},
                    "label": "Nova",
                },
                {"op": "bind_visual", "visualId": "kpi-1", "dataSourceId": "src-a"},
            ],
        },
        user={"sub": "u1"},
        authorization="Bearer x",
    )
    assert result["ok"] is True
    assert result["persisted"] is False
    assert "src-b" in result["diff"]["addedBlockIds"]
    blocks = result["nativeConfig"]["blocks"]
    kpi = next(b for b in blocks if b["id"] == "kpi-1")
    assert kpi["dataSourceId"] == "src-a"
    assert all("resolved" not in b for b in blocks)
    assert result.get("fingerprint")
    assert repo.updated == []


def test_apply_persists_and_strips_resolved(monkeypatch):
    repo = _FakeRepo()
    svc = _service(repo, monkeypatch)
    notified: list[dict[str, Any]] = []

    def _notify(**kwargs):
        notified.append(kwargs)

    monkeypatch.setattr(
        "tv_app.application.services.data.tv_copilot_patch_service.notify_presentation_changed",
        _notify,
    )

    # Inject resolved into source to ensure sanitize strips it on apply path
    repo.slides[SLIDE_ID]["nativeConfig"]["blocks"][0]["resolved"] = {"idd": 1}

    result = svc.apply(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "set_data_transform",
                    "blockId": "src-a",
                    "steps": [{"op": "select", "columns": ["idd"]}],
                }
            ],
        },
        user={"sub": "u1"},
        actor_user_id="u1",
    )
    assert result["persisted"] is True
    assert repo.updated
    saved = repo.updated[0]["payload"]["nativeConfig"]
    assert all("resolved" not in b for b in saved["blocks"])
    assert notified and notified[0]["reason"] == "copilot_patch_applied"


def test_rejects_unknown_op_and_unknown_operation_id(monkeypatch):
    svc = _service(monkeypatch=monkeypatch)
    with pytest.raises(TvCopilotPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [{"op": "run_m_script", "script": "let x = 1"}],
            },
            user={},
        )
    with pytest.raises(TvCopilotPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [{"op": "upsert_data_source", "operationId": "missing.op"}],
            },
            user={},
        )


def test_create_playlist_preview_and_m_forbidden_on_upsert_block(monkeypatch):
    svc = _service(monkeypatch=monkeypatch)
    preview = svc.preview(
        {"target": {}, "ops": [{"op": "create_playlist", "name": "Turno A"}]},
        user={},
    )
    assert preview["sideEffects"]["playlist"]["preview"] is True
    assert preview["sideEffects"]["playlist"]["name"] == "Turno A"

    with pytest.raises(TvCopilotPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [{"op": "upsert_block", "block": {"id": "x", "type": "text", "mScript": "x"}}],
            },
            user={},
        )
