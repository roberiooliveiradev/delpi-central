from __future__ import annotations

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import Response

from tv_app.application.services.branch_access_scope_service import BranchAccessScopeService
from tv_app.application.services.native_screen_cache_service import native_data_cache_stats
from tv_app.application.services.slide_preset_service import (
    SlidePresetNotFoundError,
    export_preset_mdd,
    list_slide_presets,
    resolve_preset_slide,
)
from tv_app.application.services.slide_template_mdd_service import (
    SlideTemplateMddError,
    build_slide_template_mdd,
    parse_slide_template_mdd,
)
from tv_app.application.services.tv_dashboard_content_service import ui_content_bundle
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_READ, TV_WRITE, assert_permission
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


@router.get("/slide-presets/{preset_key}/export")
def slide_preset_export_mdd(request: Request, preset_key: str):
    """Download do template catalogado como pacote MDD (`.mdd`)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    try:
        payload, filename = export_preset_mdd(preset_key)
    except SlidePresetNotFoundError:
        return fail("Preset de tela não encontrado.", 404)
    except SlideTemplateMddError as exc:
        return fail(str(exc), 422)
    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/slide-templates/export")
async def export_slide_as_template_mdd(request: Request):
    """Empacota o nativeConfig atual do editor como `.mdd` (download)."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    try:
        body = await request.json()
    except Exception:
        return fail("JSON inválido.", 400)
    if not isinstance(body, dict):
        return fail("Corpo inválido.", 400)
    native_config = body.get("nativeConfig")
    if not isinstance(native_config, dict):
        return fail("nativeConfig obrigatório.", 422)
    key = str(body.get("key") or "slide_template").strip() or "slide_template"
    label = str(body.get("label") or key).strip()
    title = str(body.get("title") or label).strip()
    description = body.get("description")
    if description is not None:
        description = str(description)
    duration = body.get("durationSec")
    try:
        payload, filename = build_slide_template_mdd(
            key=key,
            label=label,
            description=description,
            title=title,
            duration_sec=int(duration) if duration is not None else 45,
            native_config=native_config,
            native_screen_key=str(body.get("nativeScreenKey") or "custom_message"),
            exported_by=getattr(user, "sub", None) or getattr(user, "id", None),
        )
    except (TypeError, ValueError, SlideTemplateMddError) as exc:
        return fail(str(exc), 422)
    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/slide-templates/import")
async def import_slide_template_mdd(
    request: Request,
    file: UploadFile = File(...),
):
    """Importa `.mdd` e devolve nativeConfig para aplicar no editor."""
    user = resolve_user(request)
    try:
        assert_permission(user, TV_WRITE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    raw = await file.read()
    if not raw:
        return fail("Arquivo vazio.", 400)
    try:
        parsed = parse_slide_template_mdd(raw)
    except SlideTemplateMddError as exc:
        return fail(str(exc), 422)
    return ok(parsed)


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
