"""Testes TvCopilotPatchV1 — preview/apply sem M e sem resolved."""

from __future__ import annotations

from typing import Any

import pytest

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
    clear_tv_copilot_content_cache,
)
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
SECTION_ID = "22222222-2222-2222-2222-222222222222"


class _FakeRepo:
    def __init__(self) -> None:
        self.slides: dict[str, dict[str, Any]] = {
            SLIDE_ID: {
                "id": SLIDE_ID,
                "title": "Slide A",
                "durationSec": 30,
                "isActive": True,
                "sectionId": None,
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
                            "type": "kpi_view",
                            "dataSourceId": None,
                        },
                    ],
                },
            }
        }
        self.sections: dict[str, dict[str, Any]] = {
            SECTION_ID: {
                "id": SECTION_ID,
                "name": "Seção A",
                "isMain": False,
            }
        }
        self.updated: list[dict[str, Any]] = []
        self.created_playlists: list[dict[str, Any]] = []
        self.added_slides: list[dict[str, Any]] = []
        self.deleted_slides: list[str] = []
        self.reordered: list[list[dict[str, Any]]] = []
        self.section_ops: list[dict[str, Any]] = []

    def get_slide(self, slide_id, *, playlist_id=None):
        key = str(slide_id)
        if key not in self.slides:
            from tv_app.infrastructure.persistence.repositories.playlist_repository import (
                SlideNotFoundError,
            )

            raise SlideNotFoundError(key)
        return dict(self.slides[key])

    def get_by_id(self, playlist_id):
        return {
            "id": str(playlist_id),
            "dataDefaults": {"branch": "01"},
            "revision": 7,
        }

    def get_revision(self, playlist_id):
        return 7

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
        key = str(slide_id)
        slide = self.slides.setdefault(key, {"id": key})
        if "nativeConfig" in payload:
            slide["nativeConfig"] = payload["nativeConfig"]
        if "title" in payload and payload["title"] is not None:
            slide["title"] = payload["title"]
        if "durationSec" in payload:
            slide["durationSec"] = payload["durationSec"]
        if "isActive" in payload and payload["isActive"] is not None:
            slide["isActive"] = bool(payload["isActive"])
        if "sectionId" in payload:
            slide["sectionId"] = payload["sectionId"]
        return dict(slide)

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
        self.slides[str(slide["id"])] = slide
        return slide

    def delete_slide(self, playlist_id, slide_id, *, actor_user_id, reason):
        key = str(slide_id)
        if key not in self.slides:
            from tv_app.infrastructure.persistence.repositories.playlist_repository import (
                SlideNotFoundError,
            )

            raise SlideNotFoundError(key)
        del self.slides[key]
        self.deleted_slides.append(key)

    def reorder_slides(self, playlist_id, items, *, actor_user_id, reason):
        self.reordered.append(list(items))
        return [dict(self.slides[str(item["id"])]) for item in items if str(item["id"]) in self.slides]

    def add_section(self, playlist_id, payload, *, actor_user_id, reason):
        section = {
            "id": f"sec-{len(self.sections)+1}",
            "name": payload.get("name"),
            "isMain": False,
        }
        self.sections[section["id"]] = section
        self.section_ops.append({"op": "add", **section})
        return section

    def update_section(self, playlist_id, section_id, payload, *, actor_user_id, reason):
        key = str(section_id)
        if key not in self.sections:
            from tv_app.infrastructure.persistence.repositories.playlist_repository import (
                SectionNotFoundError,
            )

            raise SectionNotFoundError(key)
        section = self.sections[key]
        if "name" in payload and payload["name"] is not None:
            section["name"] = payload["name"]
        self.section_ops.append({"op": "update", **section})
        return dict(section)

    def delete_section(self, playlist_id, section_id, *, actor_user_id, reason, delete_slides=False):
        key = str(section_id)
        if key not in self.sections:
            from tv_app.infrastructure.persistence.repositories.playlist_repository import (
                SectionNotFoundError,
            )

            raise SectionNotFoundError(key)
        if self.sections[key].get("isMain"):
            from tv_app.infrastructure.persistence.repositories.playlist_repository import (
                MainSectionProtectedError,
            )

            raise MainSectionProtectedError()
        del self.sections[key]
        self.section_ops.append({"op": "delete", "id": key})


class _FakeResolution:
    def resolve_blocks(self, blocks, **kwargs):
        out = []
        for block in blocks:
            item = dict(block)
            item["resolved"] = {"idd": 6.57, "score": 6.57}
            out.append(item)
        return out


@pytest.fixture(autouse=True)
def _reset_telemetry_and_content_cache():
    reset_copilot_telemetry()
    clear_tv_copilot_content_cache()
    yield
    reset_copilot_telemetry()
    clear_tv_copilot_content_cache()


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


def test_capability_catalog_document_has_version_and_capabilities():
    doc = TvCopilotContentService.capability_catalog_document()
    assert doc["catalogVersion"]
    assert isinstance(doc["capabilities"], list) and len(doc["capabilities"]) >= 10
    assert "delete_block" in doc["allowedOps"]
    assert "add_blank_slide" in TvCopilotContentService.allowed_ops()


def test_patch_target_validation_uses_operation_contract(monkeypatch):
    svc = _service(monkeypatch=monkeypatch)

    with pytest.raises(TvCopilotPatchError, match="playlistId"):
        svc.preview(
            {
                "target": {},
                "ops": [{"op": "add_blank_slide", "title": "Novo"}],
            },
            user={},
        )

    with pytest.raises(TvCopilotPatchError, match="slideId"):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID},
                "ops": [
                    {
                        "op": "upsert_block",
                        "block": {"id": "txt-1", "type": "text", "content": "Olá"},
                    }
                ],
            },
            user={},
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
    assert isinstance(kpi.get("kpiProjection"), dict)
    assert all("resolved" not in b for b in blocks)
    assert result.get("fingerprint")
    assert "replaceNativeConfig" in result["sideEffectHints"]
    assert repo.updated == []


def test_apply_plans_crud_http_without_persisting(monkeypatch):
    """Apply do BFF só planeja — persistência = rotas /playlists/** na AI."""
    repo = _FakeRepo()
    svc = _service(repo, monkeypatch)
    notified: list[dict[str, Any]] = []

    monkeypatch.setattr(
        "tv_app.application.services.data.tv_copilot_patch_service.notify_presentation_changed",
        lambda **kwargs: notified.append(kwargs),
    )

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
    assert result["persisted"] is False
    assert result["executionMode"] == "crud_http"
    assert result["baseRevision"] == 7
    assert repo.updated == []
    assert notified == []
    cmds = result["httpCommands"]
    assert len(cmds) == 1
    assert cmds[0]["method"] == "PATCH"
    assert cmds[0]["path"] == f"/playlists/{PLAYLIST_ID}/slides/{SLIDE_ID}"
    assert "nativeConfig" in cmds[0]["body"]
    assert all("resolved" not in b for b in cmds[0]["body"]["nativeConfig"]["blocks"])
    assert cmds[0]["expectedRevision"] == 7


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
    assert "refreshFilmstrip" in preview["sideEffectHints"]

    with pytest.raises(TvCopilotPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [{"op": "upsert_block", "block": {"id": "x", "type": "text", "mScript": "x"}}],
            },
            user={},
        )


def test_delete_block_and_hints(monkeypatch):
    svc = _service(monkeypatch=monkeypatch)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [{"op": "delete_block", "blockId": "kpi-1"}],
        },
        user={},
    )
    assert "kpi-1" in result["diff"]["removedBlockIds"]
    assert result["sideEffects"]["removedBlockIds"] == ["kpi-1"]
    assert "removeBlockIds" in result["sideEffectHints"]
    assert "replaceNativeConfig" in result["sideEffectHints"]


def test_upsert_block_keeps_asset_id(monkeypatch):
    svc = _service(monkeypatch=monkeypatch)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_block",
                    "block": {
                        "id": "img-1",
                        "type": "image",
                        "assetId": "asset-abc",
                        "url": "https://evil.example/x.png",
                    },
                }
            ],
        },
        user={},
    )
    block = next(b for b in result["nativeConfig"]["blocks"] if b["id"] == "img-1")
    assert block["assetId"] == "asset-abc"
    assert "url" not in block


def test_patch_native_config_background(monkeypatch):
    svc = _service(monkeypatch=monkeypatch)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "patch_native_config",
                    "patch": {"background": {"type": "color", "value": "#112233"}},
                }
            ],
        },
        user={},
    )
    assert result["nativeConfig"]["background"] == {
        "type": "color",
        "value": "#112233",
    }
    assert "replaceNativeConfig" in result["sideEffectHints"]

    with pytest.raises(TvCopilotPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [{"op": "patch_native_config", "patch": {"blocks": []}}],
            },
            user={},
        )


def test_add_blank_slide_and_update_slide_emit_http_commands(monkeypatch):
    repo = _FakeRepo()
    svc = _service(repo, monkeypatch)

    blank_preview = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID},
            "ops": [{"op": "add_blank_slide", "title": "Em branco"}],
        },
        user={},
    )
    assert blank_preview["sideEffects"]["slides"][0]["preview"] is True
    assert blank_preview["sideEffects"]["slides"][0]["nativeScreenKey"] == "custom_message"
    assert repo.added_slides == []
    assert blank_preview["httpCommands"][0]["method"] == "POST"
    assert blank_preview["httpCommands"][0]["path"] == f"/playlists/{PLAYLIST_ID}/slides"

    blank_apply = svc.apply(
        {
            "target": {"playlistId": PLAYLIST_ID},
            "ops": [{"op": "add_blank_slide", "title": "Em branco"}],
        },
        user={},
        actor_user_id="u1",
    )
    assert blank_apply["persisted"] is False
    assert blank_apply["executionMode"] == "crud_http"
    assert repo.added_slides == []
    assert "refreshFilmstrip" in blank_apply["sideEffectHints"]
    assert blank_apply["httpCommands"][0]["body"]["title"] == "Em branco"

    updated = svc.apply(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [{"op": "update_slide", "title": "Novo título", "isActive": False}],
        },
        user={},
        actor_user_id="u1",
    )
    assert updated["persisted"] is False
    assert repo.updated == []
    # Estado do repo não muda — só o plano.
    assert repo.slides[SLIDE_ID]["title"] == "Slide A"
    cmd = updated["httpCommands"][0]
    assert cmd["method"] == "PATCH"
    assert cmd["body"]["title"] == "Novo título"
    assert cmd["body"]["isActive"] is False


def test_reorder_and_delete_slide_emit_http_commands(monkeypatch):
    repo = _FakeRepo()
    svc = _service(repo, monkeypatch)
    reorder = svc.apply(
        {
            "target": {"playlistId": PLAYLIST_ID},
            "ops": [
                {
                    "op": "reorder_slides",
                    "items": [{"id": SLIDE_ID, "sortOrder": 2}],
                }
            ],
        },
        user={},
        actor_user_id="u1",
    )
    assert repo.reordered == []
    assert reorder["sideEffects"]["reorder"]["items"][0]["sortOrder"] == 2
    assert reorder["httpCommands"][0]["path"] == f"/playlists/{PLAYLIST_ID}/slides/reorder"

    deleted = svc.apply(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [{"op": "delete_slide"}],
        },
        user={},
        actor_user_id="u1",
    )
    assert repo.deleted_slides == []
    assert deleted["sideEffects"]["deletedSlides"][0]["deleted"] is True
    assert deleted["httpCommands"][0]["method"] == "DELETE"
    assert deleted["httpCommands"][0]["path"] == (
        f"/playlists/{PLAYLIST_ID}/slides/{SLIDE_ID}"
    )


def test_fake_repo_mirrors_real_playlist_repository_api():
    """O fake não pode inventar método: era assim que `_repo.get` virou 500 em prod."""
    from tv_app.infrastructure.persistence.repositories.playlist_repository import (
        PlaylistRepository,
    )

    fake_methods = {
        name
        for name in dir(_FakeRepo)
        if not name.startswith("_") and callable(getattr(_FakeRepo, name))
    }
    missing = sorted(name for name in fake_methods if not hasattr(PlaylistRepository, name))
    assert missing == []


def test_apply_upsert_block_de_texto_planeja_patch_com_frame_padrao(monkeypatch):
    repo = _FakeRepo()
    svc = _service(repo, monkeypatch)

    result = svc.apply(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_block",
                    "block": {"id": "txt-1", "type": "text", "content": "Olá mundo!"},
                }
            ],
        },
        user={"sub": "u1"},
        actor_user_id="u1",
    )

    assert result["persisted"] is False
    assert repo.updated == []
    block = next(b for b in result["nativeConfig"]["blocks"] if b["id"] == "txt-1")
    assert block["content"] == "Olá mundo!"
    # Sem frame o bloco não aparece no editor nem no viewer.
    assert set(block["frame"]) == {"x", "y", "w", "h"}
    assert block["frame"]["w"] > 0 and block["frame"]["h"] > 0
    assert block["style"]["fontSize"]
    # Várias ops de canvas coalescem num único PATCH nativeConfig.
    assert len(result["httpCommands"]) == 1
    assert result["httpCommands"][0]["op"] == "native_config_batch"


def test_apply_upsert_block_existente_preserva_geometria_no_plano(monkeypatch):
    repo = _FakeRepo()
    repo.slides[SLIDE_ID]["nativeConfig"]["blocks"].append(
        {
            "id": "txt-1",
            "type": "text",
            "content": "Antes",
            "frame": {"x": 12, "y": 40, "w": 30, "h": 8},
            "style": {"fontSize": 44},
        }
    )
    svc = _service(repo, monkeypatch)

    result = svc.apply(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_block",
                    "block": {"id": "txt-1", "type": "text", "content": "Depois"},
                }
            ],
        },
        user={"sub": "u1"},
        actor_user_id="u1",
    )

    assert repo.updated == []
    block = next(b for b in result["nativeConfig"]["blocks"] if b["id"] == "txt-1")
    assert block["content"] == "Depois"
    assert block["frame"] == {"x": 12, "y": 40, "w": 30, "h": 8}
    assert block["style"]["fontSize"] == 44


def test_apply_traduz_erro_de_validacao_em_erro_de_patch(monkeypatch):
    repo = _FakeRepo()
    svc = _service(repo, monkeypatch)

    def _reject(cfg, user=None, catalog=None):
        raise ValueError("Rota de dados não permitida para o seu perfil.")

    monkeypatch.setattr(
        "tv_app.application.services.data.tv_copilot_patch_service.validate_comunicado_native_config",
        _reject,
    )

    with pytest.raises(TvCopilotPatchError, match="não permitida"):
        svc.apply(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [
                    {
                        "op": "upsert_block",
                        "block": {"id": "txt-1", "type": "text", "content": "Olá"},
                    }
                ],
            },
            user={"sub": "u1"},
            actor_user_id="u1",
        )
    assert repo.updated == []
