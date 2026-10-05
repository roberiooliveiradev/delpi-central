"""Boundary gate: todo write humano de ``playlist.dataDefaults`` passa pelo
mesmo pipeline canônico do PresentationMutation
(``TvPresentationWriteService.prepare_playlist_data_defaults_write``).

Cobre:
- PATCH /playlists/{id} (route): scalar PASS, ExpressionSpec válida PASS,
  AST inválida/param não declarado/objeto arbitrário → 422 sem persistir;
- PresentationMutation PREPARE (preview, persist=False): mesmo gate
  fail-closed para ``patch_playlist_data_defaults``;
- MDD ``apply_import``: ExpressionSpec em dataDefaults do pacote faz
  roundtrip verbatim; spec inválida falha o apply.
"""

from __future__ import annotations

import io
import json
import zipfile
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tv_app.application.services.playlist_access_service import PlaylistAccess
from tv_app.application.services.data.presentation_mutation import (
    PresentationPatchError,
    PresentationPatchService,
)
from tv_app.application.services.tv_deck_package_service import (
    MANIFEST_FILENAME,
    PLAYLIST_PATH,
    SLIDES_PATH,
    TvDeckPackageError,
    TvDeckPackageService,
    _PreviewStore,
)
from tv_app.application.services.tv_presentation_write_service import (
    TvPresentationWriteService,
)
from tv_app.interface.http.routes import playlist_routes


def _spec(ast=None, *, version=1):
    return {
        "expression": {
            "version": version,
            "expression": ast if ast is not None else {"kind": "literal", "value": "weg"},
        }
    }


# Rota real do catálogo bundled — params declarados no paramSchema.
ROUTE_OP = "get_commercial_rol_summary"
ROUTE_PARAM = "customer_segment"


def _slide_with_route(operation_id: str = ROUTE_OP) -> dict:
    return {
        "id": str(uuid4()),
        "nativeConfig": {
            "version": 5,
            "blocks": [
                {
                    "id": "kpi1",
                    "type": "data_kpi",
                    "dataBinding": {"operationId": operation_id, "params": {}},
                }
            ],
        },
    }


class _FakePlaylistRepo:
    """Repositório mínimo para o boundary de playlist (route + writes)."""

    def __init__(self, slides: list[dict] | None = None, defaults: dict | None = None):
        self._slides = list(slides or [])
        self._playlist = {
            "id": str(uuid4()),
            "name": "Programação",
            "revision": 7,
            "publicToken": "tok",
            "dataDefaults": dict(defaults or {}),
        }
        self.update_calls: list[dict] = []

    def list_slides(self, playlist_id):
        return [dict(s) for s in self._slides]

    def get_by_id(self, playlist_id):
        return dict(self._playlist)

    def get_revision(self, playlist_id):
        return self._playlist["revision"]

    def update(self, playlist_id, *, actor_user_id, reason, **kwargs):
        self.update_calls.append(dict(kwargs))
        if "data_defaults" in kwargs and kwargs["data_defaults"] is not None:
            self._playlist["dataDefaults"] = kwargs["data_defaults"]
        return dict(self._playlist)

    def update_data_defaults(self, playlist_id, data_defaults, *, actor_user_id, reason):
        self._playlist["dataDefaults"] = data_defaults
        return dict(self._playlist)

    def list_shares(self, playlist_id):
        return []


def _request(user_id: str = "user-1"):
    request = MagicMock()
    request.state.user = SimpleNamespace(id=user_id)
    return request


def _access(playlist_id, *, level="editor"):
    return (
        SimpleNamespace(id="user-1"),
        PlaylistAccess(
            level=level,
            playlist={"id": str(playlist_id), "revision": 7},
        ),
    )


def _response_body(response):
    return json.loads(response.body.decode("utf-8"))


def _call_update(repo, playlist_id, body_kwargs):
    with (
        patch.object(playlist_routes, "_repo", repo),
        patch.object(
            playlist_routes, "_writes", TvPresentationWriteService(repo=repo)
        ),
        patch(
            "tv_app.interface.http.routes.playlist_routes.require_playlist_access",
            return_value=_access(playlist_id),
        ),
        patch.object(playlist_routes, "notify_presentation_changed"),
        patch.object(playlist_routes, "_notify_library"),
    ):
        return playlist_routes.update_playlist(
            _request(),
            playlist_id,
            playlist_routes.UpdatePlaylistBody(**body_kwargs),
        )


# --------------------------------------------------------------- PATCH route


def test_patch_playlist_accepts_scalar_literal():
    repo = _FakePlaylistRepo(slides=[_slide_with_route()])
    playlist_id = uuid4()

    response = _call_update(
        repo, playlist_id, {"dataDefaults": {"branch": "01", "customer_segment": "weg"}}
    )

    assert response.status_code == 200
    defaults = repo.update_calls[-1]["data_defaults"]
    assert defaults["branch"] == "01"
    assert defaults["customer_segment"] == "weg"


def test_patch_playlist_accepts_valid_expression_spec():
    repo = _FakePlaylistRepo(slides=[_slide_with_route()])
    playlist_id = uuid4()

    response = _call_update(
        repo,
        playlist_id,
        {"dataDefaults": {ROUTE_PARAM: _spec(), "branch": "01"}},
    )

    assert response.status_code == 200
    persisted = repo.update_calls[-1]["data_defaults"]
    assert persisted[ROUTE_PARAM]["expression"]["version"] == 1
    assert persisted["branch"] == "01"


def test_patch_playlist_rejects_invalid_ast():
    repo = _FakePlaylistRepo(slides=[_slide_with_route()])
    playlist_id = uuid4()

    bad_spec = _spec({"kind": "definitivamente_invalido"})
    response = _call_update(
        repo, playlist_id, {"dataDefaults": {ROUTE_PARAM: bad_spec}}
    )

    assert response.status_code == 422
    assert repo.update_calls == []


def test_patch_playlist_rejects_expression_for_undeclared_param():
    repo = _FakePlaylistRepo(slides=[_slide_with_route()])
    playlist_id = uuid4()

    response = _call_update(
        repo,
        playlist_id,
        {"dataDefaults": {"param_inexistente_xyz": _spec()}},
    )

    assert response.status_code == 422
    assert repo.update_calls == []


def test_patch_playlist_rejects_arbitrary_object():
    repo = _FakePlaylistRepo(slides=[_slide_with_route()])
    playlist_id = uuid4()

    response = _call_update(
        repo,
        playlist_id,
        {"dataDefaults": {"branch": {"arbitrary": "object"}}},
    )

    assert response.status_code == 422
    assert repo.update_calls == []


def test_patch_playlist_normalizes_period_on_replace():
    """dataDefaults é replace full-map: preset remove datas literais stale."""
    repo = _FakePlaylistRepo(slides=[_slide_with_route()])
    playlist_id = uuid4()

    response = _call_update(
        repo,
        playlist_id,
        {
            "dataDefaults": {
                "dateRangePreset": "this_month",
                "start_date": "2020-01-01",
                "end_date": "2020-01-31",
            }
        },
    )

    assert response.status_code == 200
    persisted = repo.update_calls[-1]["data_defaults"]
    assert persisted["dateRangePreset"] == "this_month"
    assert "start_date" not in persisted
    assert "end_date" not in persisted


# ----------------------------------------------------- PresentationMutation PREPARE


class _FakeCatalog:
    def __init__(self, routes: dict[str, dict]) -> None:
        self._routes = routes

    def get_route(self, operation_id: str):
        return self._routes.get(operation_id)


class _FakeResolution:
    def resolve_blocks(self, blocks, **kwargs):
        return [dict(block) for block in blocks]


def _patch_service(repo):
    return PresentationPatchService(
        catalog=_FakeCatalog({}),
        repo=repo,
        resolution=_FakeResolution(),
    )


def _preview_playlist_defaults(repo, playlist_id: str, data_defaults: dict, **op_extra):
    return _patch_service(repo).preview(
        {
            "target": {"playlistId": playlist_id},
            "ops": [
                {
                    "op": "patch_playlist_data_defaults",
                    "dataDefaults": data_defaults,
                    **op_extra,
                }
            ],
        },
        user={},
    )


def test_prepare_patch_playlist_defaults_accepts_expression_spec():
    repo = _FakePlaylistRepo(slides=[_slide_with_route()])

    out = _preview_playlist_defaults(
        repo, str(uuid4()), {ROUTE_PARAM: _spec()}
    )

    preview_playlist = out["sideEffects"]["playlist"]
    assert (
        preview_playlist["dataDefaults"][ROUTE_PARAM]["expression"]["version"] == 1
    )


def test_prepare_patch_playlist_defaults_fails_closed_on_invalid_expression():
    repo = _FakePlaylistRepo(slides=[_slide_with_route()])

    with pytest.raises(PresentationPatchError):
        _preview_playlist_defaults(
            repo, str(uuid4()), {"param_inexistente_xyz": _spec()}
        )


def test_prepare_patch_playlist_defaults_fails_closed_on_arbitrary_object():
    repo = _FakePlaylistRepo(slides=[_slide_with_route()])

    with pytest.raises(PresentationPatchError):
        _preview_playlist_defaults(
            repo, str(uuid4()), {"branch": {"nested": "no"}}
        )


# ----------------------------------------------------- patch_native_config PREPARE


def _real_route(operation_id: str = ROUTE_OP) -> dict:
    from tv_app.application.services.tv_data_route_catalog_service import (
        TvDataRouteCatalogService,
    )

    return TvDataRouteCatalogService().get_route(operation_id)


def _repo_with_slide(slide: dict):
    repo = _FakePlaylistRepo(slides=[slide])

    def _get_slide(slide_id, *, playlist_id=None):
        return dict(slide)

    repo.get_slide = _get_slide  # type: ignore[attr-defined]
    return repo


def test_prepare_patch_native_config_data_filters_accepts_expression_spec():
    from tv_app.application.services.tv_data_route_catalog_service import (
        TvDataRouteCatalogService,
    )

    slide = _slide_with_route()
    repo = _repo_with_slide(slide)
    catalog = _FakeCatalog({ROUTE_OP: _real_route()})
    svc = PresentationPatchService(
        catalog=catalog,
        repo=repo,
        resolution=_FakeResolution(),
    )

    out = svc.preview(
        {
            "target": {"playlistId": str(uuid4()), "slideId": slide["id"]},
            "ops": [
                {
                    "op": "patch_native_config",
                    "patch": {"dataFilters": {ROUTE_PARAM: _spec()}},
                }
            ],
        },
        user={},
    )

    filters = out["nativeConfig"].get("dataFilters") or {}
    assert filters[ROUTE_PARAM]["expression"]["version"] == 1


def test_prepare_patch_native_config_data_filters_fails_closed():
    """AST inválida em param declarado: o gate de validação (mesmo
    validate_data_filters do runtime) falha fechado no PREPARE."""
    slide = _slide_with_route()
    repo = _repo_with_slide(slide)
    catalog = _FakeCatalog({ROUTE_OP: _real_route()})
    svc = PresentationPatchService(
        catalog=catalog,
        repo=repo,
        resolution=_FakeResolution(),
    )

    with pytest.raises(PresentationPatchError):
        svc.preview(
            {
                "target": {"playlistId": str(uuid4()), "slideId": slide["id"]},
                "ops": [
                    {
                        "op": "patch_native_config",
                        "patch": {
                            "dataFilters": {
                                ROUTE_PARAM: _spec({"kind": "definitivamente_invalido"})
                            }
                        },
                    }
                ],
            },
            user={},
        )


# ----------------------------------------------------------------- MDD roundtrip


def _build_mdd_with_defaults(data_defaults: dict, operation_id: str) -> bytes:
    """Pacote mínimo válido: playlist.dataDefaults + 1 slide com a rota."""
    manifest = {
        "format": "minha_delpi_deck",
        "schemaVersion": "1.0",
        "exportedAt": "2026-01-01T00:00:00+00:00",
        "stats": {},
    }
    playlist = {"name": "Importada", "dataDefaults": data_defaults}
    slides = [
        {
            "id": str(uuid4()),
            "slideType": "native",
            "title": "Tela",
            "nativeConfig": {
                "version": 5,
                "blocks": [
                    {
                        "id": "kpi1",
                        "type": "data_kpi",
                        "dataBinding": {"operationId": operation_id, "params": {}},
                    }
                ],
            },
        }
    ]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(MANIFEST_FILENAME, json.dumps(manifest))
        zf.writestr(PLAYLIST_PATH, json.dumps(playlist))
        zf.writestr("deck/sections.json", "[]")
        zf.writestr(SLIDES_PATH, json.dumps(slides))
        zf.writestr("deck/media.json", "[]")
        zf.writestr("deck/data_bindings_index.json", "[]")
    return buffer.getvalue()


def _deck_service(playlist_repo):
    from tv_app.application.services.tv_deck_binding_validator import (
        TvDeckBindingValidator,
    )

    catalog = MagicMock()
    catalog.get_route.return_value = None
    return TvDeckPackageService(
        playlist_repo=playlist_repo,
        media_repo=MagicMock(),
        media_storage=MagicMock(),
        binding_validator=TvDeckBindingValidator(catalog=catalog),
        max_bytes=10 * 1024 * 1024,
        preview_store=_PreviewStore(ttl_seconds=60),
    )


def test_mdd_import_preserves_expression_spec_in_data_defaults():
    spec = _spec()
    payload = _build_mdd_with_defaults(
        {ROUTE_PARAM: spec, "branch": "01"}, ROUTE_OP
    )

    repo = _FakePlaylistRepo(slides=[])
    repo.create = lambda **kw: {"id": str(uuid4())}  # type: ignore[attr-defined]
    repo.update = lambda playlist_id, **kw: repo.update_calls.append(kw) or {  # type: ignore[attr-defined]
        "id": str(playlist_id),
        "publicToken": "tok",
    }
    repo.import_sections_from_deck = lambda *a, **kw: {}  # type: ignore[attr-defined]
    repo.import_slides_from_deck = lambda *a, **kw: []  # type: ignore[attr-defined]
    repo.list_sections = lambda *a, **kw: []  # type: ignore[attr-defined]

    service = _deck_service(repo)
    preview = service.preview_import(payload)
    assert preview["valid"] is True

    service.apply_import(
        import_token=preview["importToken"],
        created_by="user-b",
        binding_policy="lenient",
    )

    written = repo.update_calls[-1]["data_defaults"]
    assert written[ROUTE_PARAM] == spec
    assert written["branch"] == "01"


def test_mdd_import_rejects_expression_for_param_absent_from_package_routes():
    payload = _build_mdd_with_defaults(
        {"param_inexistente_xyz": _spec()}, ROUTE_OP
    )

    repo = _FakePlaylistRepo(slides=[])
    repo.create = lambda **kw: {"id": str(uuid4())}  # type: ignore[attr-defined]
    repo.import_sections_from_deck = lambda *a, **kw: {}  # type: ignore[attr-defined]
    repo.import_slides_from_deck = lambda *a, **kw: []  # type: ignore[attr-defined]

    service = _deck_service(repo)
    preview = service.preview_import(payload)
    with pytest.raises(TvDeckPackageError):
        service.apply_import(
            import_token=preview["importToken"],
            created_by="user-b",
            binding_policy="lenient",
        )
