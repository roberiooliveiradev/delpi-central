from __future__ import annotations

from fastapi import APIRouter, Request

from tv_app.application.services.data.tv_data_config_validation_service import TvDataConfigValidationService
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_READ, assert_permission
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/data-routes", tags=["TV Data Routes"])
_catalog = TvDataRouteCatalogService()
_validation = TvDataConfigValidationService(_catalog)


@router.get("")
def list_data_routes(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok({"items": [_validation.enrich_route_for_api(route) for route in _catalog.list_routes()]})
