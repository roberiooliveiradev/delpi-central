"""Testes PresentationMutation — preview/apply sem M e sem resolved."""

from __future__ import annotations

from typing import Any

import pytest

from tv_app.application.services.data.presentation_ops_content_service import (
    PresentationOpsContentService,
    clear_presentation_ops_content_cache,
)
from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.data.presentation_mutation_telemetry import (
    reset_presentation_mutation_telemetry,
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
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()
    yield
    reset_presentation_mutation_telemetry()
    clear_presentation_ops_content_cache()


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
            "tv_app.application.services.data.presentation_mutation.patch_service.sanitize_and_hydrate_comunicado_config",
            _sanitize,
        )
        monkeypatch.setattr(
            "tv_app.application.services.data.presentation_mutation.patch_service.validate_comunicado_native_config",
            lambda cfg, user=None, catalog=None: None,
        )
    return PresentationPatchService(
        catalog=_FakeCatalog({"op.demo": {"label": "Demo", "operationId": "op.demo"}}),
        repo=repo or _FakeRepo(),
        resolution=_FakeResolution(),
    )


def test_capability_catalog_document_has_version_and_capabilities():
    doc = PresentationOpsContentService.capability_catalog_document()
    assert doc["catalogVersion"]
    assert isinstance(doc["capabilities"], list) and len(doc["capabilities"]) >= 10
    assert "delete_block" in doc["allowedOps"]
    assert "add_blank_slide" in PresentationOpsContentService.allowed_ops()


def test_patch_target_validation_uses_operation_contract(monkeypatch):
    svc = _service(monkeypatch=monkeypatch)

    with pytest.raises(PresentationPatchError, match="playlistId"):
        svc.preview(
            {
                "target": {},
                "ops": [{"op": "add_blank_slide", "title": "Novo"}],
            },
            user={},
        )

    with pytest.raises(PresentationPatchError, match="slideId"):
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


def test_preview_upsert_date_range_inherits_playlist_period(monkeypatch):
    """Regression: playlist dateRangePreset + params {} must not INVALID_CHANGE."""
    repo = _FakeRepo()
    base = repo.get_by_id

    def _playlist(playlist_id):
        row = base(playlist_id)
        row["dataDefaults"] = {"branch": "01", "dateRangePreset": "this_month"}
        return row

    repo.get_by_id = _playlist  # type: ignore[method-assign]
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
            "tv_app.application.services.data.presentation_mutation.patch_service.sanitize_and_hydrate_comunicado_config",
            _sanitize,
        )
        monkeypatch.setattr(
            "tv_app.application.services.data.presentation_mutation.patch_service.validate_comunicado_native_config",
            lambda cfg, user=None, catalog=None: None,
        )
    svc = PresentationPatchService(
        catalog=_FakeCatalog(
            {
                "op.billing": {
                    "label": "Billing",
                    "operationId": "op.billing",
                    "paramStrategy": "date_range",
                    "openEndedDateRange": False,
                    "paramSchema": {
                        "start_date": {"optional": True, "label": "Data início"},
                        "end_date": {"optional": True, "label": "Data fim"},
                        "dateRangePreset": {"optional": True, "label": "Período"},
                    },
                }
            }
        ),
        repo=repo,
        resolution=_FakeResolution(),
    )
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_data_source",
                    "blockId": "src-billing",
                    "operationId": "op.billing",
                    "params": {},
                    "label": "Carteira",
                }
            ],
        },
        user={"sub": "u1"},
        authorization="Bearer x",
    )
    assert result["ok"] is True
    src = next(b for b in result["nativeConfig"]["blocks"] if b["id"] == "src-billing")
    # Period stays on playlist layer — not duplicated onto the source.
    binding_params = (src.get("dataBinding") or {}).get("params") or {}
    assert "dateRangePreset" not in binding_params


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


def test_preview_re_layer_with_valid_target_does_not_raise_missing_target(monkeypatch):
    """Regression: re_layer must preload nativeConfig; else INVALID_CHANGE/missingTarget
    even when playlistId+slideId are present (GR Comercial continuous review)."""
    repo = _FakeRepo()
    repo.slides[SLIDE_ID]["nativeConfig"] = {
        "version": 5,
        "blocks": [
            {
                "id": "src-a",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "op.demo",
                    "params": {"periodDays": 7, "branch": "01"},
                },
            },
            {
                "id": "src-b",
                "type": "data_source",
                "dataBinding": {
                    "operationId": "op.demo",
                    "params": {"periodDays": 7, "branch": "01"},
                },
            },
        ],
    }
    svc = _service(repo, monkeypatch)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {"op": "re_layer_playlist_filters", "scope": "playlist", "keys": ["periodDays"]},
            ],
        },
        user={"sub": "u1"},
        authorization="Bearer x",
    )
    assert result["ok"] is True
    assert "re_layer_playlist_filters" in result["appliedOps"]
    assert result["persisted"] is False

    with pytest.raises(PresentationPatchError, match="playlistId"):
        svc.preview(
            {
                "target": {},
                "ops": [{"op": "re_layer_playlist_filters", "scope": "playlist"}],
            },
            user={"sub": "u1"},
        )


def test_preview_compound_relayer_defaults_and_pause(monkeypatch):
    repo = _FakeRepo()
    svc = _service(repo, monkeypatch)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "patch_playlist_data_defaults",
                    "dataDefaults": {"periodDays": 7},
                    "replace": False,
                },
                {"op": "re_layer_playlist_filters", "scope": "playlist", "keys": ["periodDays"]},
                {"op": "update_slide", "isActive": False},
            ],
        },
        user={"sub": "u1"},
        authorization="Bearer x",
    )
    assert result["ok"] is True
    assert "re_layer_playlist_filters" in result["appliedOps"]
    assert "update_slide" in result["appliedOps"]


def test_apply_plans_crud_http_without_persisting(monkeypatch):
    """Apply do BFF só planeja — persistência = rotas /playlists/** na AI."""
    repo = _FakeRepo()
    svc = _service(repo, monkeypatch)
    notified: list[dict[str, Any]] = []

    monkeypatch.setattr(
        "tv_app.application.services.data.presentation_mutation.patch_service.notify_presentation_changed",
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
    with pytest.raises(PresentationPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [{"op": "run_m_script", "script": "let x = 1"}],
            },
            user={},
        )
    with pytest.raises(PresentationPatchError):
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

    with pytest.raises(PresentationPatchError):
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


def test_upsert_block_rejects_invalid_projection_field(monkeypatch):
    svc = PresentationPatchService(
        catalog=_FakeCatalog(
            {
                "op.demo": {
                    "label": "Demo",
                    "operationId": "op.demo",
                    "valueFields": ["forecast_value", "value"],
                }
            }
        ),
        repo=_FakeRepo(),
        resolution=_FakeResolution(),
    )
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
            "tv_app.application.services.data.presentation_mutation.patch_service.sanitize_and_hydrate_comunicado_config",
            _sanitize,
        )
        monkeypatch.setattr(
            "tv_app.application.services.data.presentation_mutation.patch_service.validate_comunicado_native_config",
            lambda cfg, user=None, catalog=None: None,
        )

    with pytest.raises(PresentationPatchError) as exc_info:
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [
                    {
                        "op": "upsert_block",
                        "block": {
                            "id": "txt-1",
                            "type": "text",
                            "dataSourceId": "src-a",
                            "textProjection": {"field": "nao_existe", "format": "raw"},
                        },
                    }
                ],
            },
            user={},
        )
    assert exc_info.value.code == "INVALID_PROJECTION_FIELD"
    assert "nao_existe" in (exc_info.value.details or {}).get("invalidFields", [])


def test_upsert_block_keeps_filter_context_projection_field(monkeypatch):
    svc = _service(monkeypatch=monkeypatch)
    # Amplia catálogo da fonte com valueFields para exercitar allowlist + context.
    svc._catalog = _FakeCatalog(
        {
            "op.demo": {
                "label": "Demo",
                "operationId": "op.demo",
                "valueFields": ["value"],
            }
        }
    )
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_block",
                    "block": {
                        "id": "txt-week",
                        "type": "text",
                        "dataSourceId": "src-a",
                        "contentRuns": [
                            {"text": "semana "},
                            {"dataRef": {"field": "filter.start_date", "format": "date"}},
                        ],
                    },
                }
            ],
        },
        user={},
    )
    block = next(b for b in result["nativeConfig"]["blocks"] if b["id"] == "txt-week")
    assert block["contentRuns"][1]["dataRef"]["field"] == "filter.start_date"


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

    with pytest.raises(PresentationPatchError):
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
        "tv_app.application.services.data.presentation_mutation.patch_service.validate_comunicado_native_config",
        _reject,
    )

    with pytest.raises(PresentationPatchError, match="não permitida"):
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


def test_nested_contract_positive_sibling_negative(monkeypatch):
    svc = _service(monkeypatch=monkeypatch)

    ok_patch = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "patch_native_config",
                    "patch": {"speakerNotes": "Nota de teste"},
                }
            ],
        },
        user={},
    )
    assert ok_patch["nativeConfig"]["speakerNotes"] == "Nota de teste"

    ok_transform = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "set_data_transform",
                    "blockId": "src-a",
                    "steps": [{"op": "keepRows", "count": 5, "from": "top"}],
                }
            ],
        },
        user={},
    )
    source = next(b for b in ok_transform["nativeConfig"]["blocks"] if b["id"] == "src-a")
    assert source["dataTransform"]["steps"][0]["op"] == "keepRows"
    assert "script" not in source["dataTransform"]
    assert source["dataTransform"].get("version") != 2

    with pytest.raises(PresentationPatchError, match="etapas tipadas|Script M|não é aceito"):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [
                    {
                        "op": "set_data_transform",
                        "blockId": "src-a",
                        "steps": [{"op": "keepRows", "count": 1, "from": "top"}],
                        "script": "let X = Fonte in X",
                    }
                ],
            },
            user={},
        )

    ok_labels = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_data_source",
                    "operationId": "op.demo",
                    "blockId": "src-a",
                    "fieldLabels": {"idd": "IDD"},
                }
            ],
        },
        user={},
    )
    updated = next(b for b in ok_labels["nativeConfig"]["blocks"] if b["id"] == "src-a")
    assert updated["fieldLabels"]["idd"] == "IDD"

    with pytest.raises(PresentationPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [{"op": "patch_native_config", "patch": {"blocks": []}}],
            },
            user={},
        )
    with pytest.raises(PresentationPatchError, match="step"):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [
                    {
                        "op": "set_data_transform",
                        "blockId": "src-a",
                        "steps": [{"op": "runSql"}],
                    }
                ],
            },
            user={},
        )
    with pytest.raises(PresentationPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID},
                "ops": [{"op": "reorder_slides", "items": [{"sortOrder": 1}]}],
            },
            user={},
        )
    with pytest.raises(PresentationPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [
                    {
                        "op": "upsert_data_source",
                        "operationId": "op.demo",
                        "fieldLabels": {"value": 9},
                    }
                ],
            },
            user={},
        )
    with pytest.raises(PresentationPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [
                    {
                        "op": "upsert_data_source",
                        "operationId": "op.demo",
                        "params": {"branch": {"nested": True}},
                    }
                ],
            },
            user={},
        )
    with pytest.raises(PresentationPatchError):
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [{"op": "upsert_block", "block": {"content": "sem tipo"}}],
            },
            user={},
        )


def test_patch_error_reports_op_index(monkeypatch):
    svc = _service(_FakeRepo(), monkeypatch)
    with pytest.raises(PresentationPatchError) as first:
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [{"op": "not_a_real_op"}],
            },
            user={"sub": "u1"},
            authorization="Bearer x",
        )
    assert first.value.details["opIndex"] == 0
    assert first.value.details["operation"] == "not_a_real_op"
    with pytest.raises(PresentationPatchError) as second:
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": [
                    {"op": "update_slide", "isActive": False},
                    {"op": "not_a_real_op"},
                ],
            },
            user={"sub": "u1"},
            authorization="Bearer x",
        )
    assert second.value.details["opIndex"] == 1


SLIDE_B_ID = "33333333-3333-3333-3333-333333333333"


def test_multi_existing_slide_native_ops_emit_per_slide_patch(monkeypatch):
    """Positive: slideRef UUID switches nativeConfig; httpCommands = 1 PATCH per slide."""
    repo = _FakeRepo()
    repo.slides[SLIDE_B_ID] = {
        "id": SLIDE_B_ID,
        "title": "Slide B",
        "durationSec": 30,
        "isActive": True,
        "sectionId": None,
        "nativeConfig": {
            "version": 5,
            "blocks": [
                {"id": "kpi-b", "type": "kpi_view", "dataSourceId": None},
            ],
        },
    }
    svc = _service(repo, monkeypatch)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "patch_native_config",
                    "slideRef": SLIDE_ID,
                    "patch": {"background": {"type": "color", "value": "#111111"}},
                },
                {
                    "op": "patch_native_config",
                    "slideRef": SLIDE_B_ID,
                    "patch": {"background": {"type": "color", "value": "#222222"}},
                },
            ],
        },
        user={},
    )
    by_slide = result.get("nativeConfigsBySlide") or {}
    assert set(by_slide.keys()) == {SLIDE_ID, SLIDE_B_ID}
    assert by_slide[SLIDE_ID]["background"]["value"] == "#111111"
    assert by_slide[SLIDE_B_ID]["background"]["value"] == "#222222"
    cmds = result["httpCommands"]
    native_cmds = [c for c in cmds if c.get("op") == "native_config_batch"]
    assert len(native_cmds) == 2
    paths = {c["path"] for c in native_cmds}
    assert paths == {
        f"/playlists/{PLAYLIST_ID}/slides/{SLIDE_ID}",
        f"/playlists/{PLAYLIST_ID}/slides/{SLIDE_B_ID}",
    }
    bodies = {c["path"]: c["body"]["nativeConfig"]["background"]["value"] for c in native_cmds}
    assert bodies[f"/playlists/{PLAYLIST_ID}/slides/{SLIDE_ID}"] == "#111111"
    assert bodies[f"/playlists/{PLAYLIST_ID}/slides/{SLIDE_B_ID}"] == "#222222"


def test_multi_slide_sibling_only_second_slide_touched(monkeypatch):
    """Sibling: ops only on slide B via slideRef — A not in nativeConfigsBySlide."""
    repo = _FakeRepo()
    repo.slides[SLIDE_B_ID] = {
        "id": SLIDE_B_ID,
        "title": "Slide B",
        "durationSec": 30,
        "isActive": True,
        "sectionId": None,
        "nativeConfig": {"version": 5, "blocks": []},
    }
    svc = _service(repo, monkeypatch)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_block",
                    "slideRef": SLIDE_B_ID,
                    "block": {"id": "txt-b", "type": "text", "content": "B only"},
                }
            ],
        },
        user={},
    )
    by_slide = result.get("nativeConfigsBySlide") or {}
    assert set(by_slide.keys()) == {SLIDE_B_ID}
    assert any(b.get("id") == "txt-b" for b in by_slide[SLIDE_B_ID].get("blocks") or [])
    native_cmds = [c for c in result["httpCommands"] if c.get("op") == "native_config_batch"]
    assert len(native_cmds) == 1
    assert native_cmds[0]["path"].endswith(f"/slides/{SLIDE_B_ID}")


def test_batch_too_large_is_honest_error(monkeypatch):
    """Negative: exceeding maxOpsPerPatch raises BATCH_TOO_LARGE — not silent noOps."""
    svc = _service(monkeypatch=monkeypatch)
    max_ops = PresentationOpsContentService.setting_int("maxOpsPerPatch", 80)
    ops = [
        {
            "op": "upsert_block",
            "block": {"id": f"t{i}", "type": "text", "content": str(i)},
        }
        for i in range(max_ops + 1)
    ]
    with pytest.raises(PresentationPatchError) as excinfo:
        svc.preview(
            {
                "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
                "ops": ops,
            },
            user={},
        )
    assert excinfo.value.code == "BATCH_TOO_LARGE"


def test_preview_label_only_preserves_source_identity(monkeypatch):
    """Rename data_source label must keep operationId/params/transform/bindings."""
    clear_presentation_ops_content_cache()
    repo = _FakeRepo()
    # Attach transform + bind so we can assert identity.
    blocks = repo.slides[SLIDE_ID]["nativeConfig"]["blocks"]
    src = next(b for b in blocks if b["id"] == "src-a")
    src["dataTransform"] = {"steps": [{"op": "keepRows", "count": 5, "from": "top"}]}
    src["resolved"] = {"rows": [{"v": 1}]}
    kpi = next(b for b in blocks if b["id"] == "kpi-1")
    kpi["dataSourceId"] = "src-a"

    svc = _service(repo, monkeypatch)
    result = svc.preview(
        {
            "target": {"playlistId": PLAYLIST_ID, "slideId": SLIDE_ID},
            "ops": [
                {
                    "op": "upsert_data_source",
                    "blockId": "src-a",
                    "label": "WEG SC · setembro ano passado",
                }
            ],
        },
        user={"sub": "u1"},
        authorization="Bearer x",
    )
    assert result["ok"] is True
    updated = next(b for b in result["nativeConfig"]["blocks"] if b["id"] == "src-a")
    binding = updated["dataBinding"]
    assert binding["label"] == "WEG SC · setembro ano passado"
    assert binding["operationId"] == "op.demo"
    assert binding["params"] == {"branch": "01"}
    assert updated["dataTransform"]["steps"][0]["count"] == 5
    # Persistence sanitize strips resolved; identity of the source must remain.
    bound = next(b for b in result["nativeConfig"]["blocks"] if b["id"] == "kpi-1")
    assert bound["dataSourceId"] == "src-a"
    # Same id — no recreate.
    assert [b["id"] for b in result["nativeConfig"]["blocks"] if b["type"] == "data_source"] == [
        "src-a"
    ]
