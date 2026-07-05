from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request

from tv_app.application.services.branch_access_scope_service import BranchAccessScopeService
from tv_app.application.services.native_screen_cache_service import native_data_cache_stats
from tv_app.application.services.slide_preset_service import list_slide_presets
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_READ, assert_permission
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Content"])

CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_dashboard_content.json"


@lru_cache(maxsize=1)
def _load_ui_content() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


@router.get("/content/ui")
def ui_content(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok(_load_ui_content())


@router.get("/slide-presets")
def slide_presets(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok({"items": list_slide_presets()})


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
