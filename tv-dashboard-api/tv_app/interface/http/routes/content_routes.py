from __future__ import annotations

from fastapi import APIRouter, Request

from tv_app.application.services.branch_access_scope_service import BranchAccessScopeService
from tv_app.application.services.native_screen_cache_service import native_data_cache_stats
from tv_app.application.services.slide_preset_service import (
    SlidePresetNotFoundError,
    list_slide_presets,
    resolve_preset_slide,
)
from tv_app.application.services.tv_dashboard_content_service import ui_content_bundle
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_READ, assert_permission
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Content"])


@router.get("/content/ui")
def ui_content(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(ui_content_bundle())


@router.get("/slide-presets")
def slide_presets(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok({"items": list_slide_presets()})


@router.get("/slide-presets/{preset_key}")
def slide_preset_detail(request: Request, preset_key: str):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    try:
        return ok(resolve_preset_slide(preset_key))
    except SlidePresetNotFoundError:
        return fail("Preset de tela não encontrado.", 404)


@router.get("/content/branch-scope")
def branch_scope(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    scope = BranchAccessScopeService().resolve(user)
    return ok(scope.meta())


@router.get("/health/native-cache")
def native_cache_health():
    return ok(
        {
            "namespace": "tv-dashboard-native-data",
            **native_data_cache_stats(),
        }
    )
