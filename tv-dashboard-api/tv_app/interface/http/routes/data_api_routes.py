from __future__ import annotations

from typing import Any

from uuid import UUID

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from tv_app.application.services.data.tv_data_config_validation_service import TvDataConfigValidationService
from tv_app.application.services.data.tv_data_openapi_catalog_service import TvDataOpenApiCatalogService
from tv_app.application.services.data.tv_data_preview_service import TvDataPreviewService
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_MANAGE, TV_READ, assert_permission
from tv_app.infrastructure.persistence.repositories.playlist_repository import PlaylistRepository
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/data", tags=["TV Dados"])
_catalog = TvDataRouteCatalogService()
_validation = TvDataConfigValidationService(_catalog)
_preview = TvDataPreviewService(_catalog)
_openapi = TvDataOpenApiCatalogService(_catalog)
_playlists = PlaylistRepository()


class PreviewDataBlockBody(BaseModel):
    block: dict[str, Any]
    nativeConfig: dict[str, Any] = Field(default_factory=dict)
    playlistId: str | None = None


class ValidateDataConfigBody(BaseModel):
    nativeConfig: dict[str, Any] = Field(default_factory=dict)


@router.get("/routes")
def list_data_routes_v2(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items = [_validation.enrich_route_for_api(route) for route in _catalog.list_routes()]
    return ok({"items": items, "total": len(items)})


@router.get("/routes/{operation_id}")
def get_data_route(request: Request, operation_id: str):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    route = _catalog.get_route(operation_id)
    if not route:
        return fail("Fonte de dados não encontrada no catálogo.", 404)
    return ok(_validation.enrich_route_for_api(route))


@router.get("/openapi/candidates")
def list_openapi_get_candidates(request: Request, include_catalog: bool = False):
    """Rotas GET da api-delpi — curadoria para expandir o catálogo TV (não import automático)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items = _openapi.list_candidates(include_allowlisted=include_catalog)
    return ok({"items": items, "total": len(items), "httpMethod": "GET"})


@router.post("/preview-block")
def preview_data_block_v2(request: Request, body: PreviewDataBlockBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)

    playlist_defaults: dict[str, Any] | None = None
    if body.playlistId:
        try:
            playlist_uuid = UUID(body.playlistId)
        except ValueError:
            return fail("Programação inválida.", 422)
        playlist = _playlists.get_by_id(playlist_uuid)
        if not playlist:
            return fail("Programação não encontrada.", 404)
        defaults = playlist.get("dataDefaults")
        playlist_defaults = defaults if isinstance(defaults, dict) else {}

    auth = request.headers.get("Authorization")
    try:
        cfg = _validation.sanitize(body.nativeConfig)
        block = _preview.preview_block(
            body.block,
            native_config=cfg,
            authorization=auth,
            user=user,
            playlist_defaults=playlist_defaults,
        )
    except ValueError as exc:
        return fail(str(exc), 422)
    except Exception as exc:  # noqa: BLE001
        return fail(str(exc), 502)
    return ok({"block": block})


@router.post("/validate-config")
def validate_data_config(request: Request, body: ValidateDataConfigBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    cfg = _validation.sanitize(body.nativeConfig)
    result = _validation.validate(cfg, user=user)
    return ok(result)
