"""CRUD da biblioteca de templates de slide (Postgres)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, File, Query, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field

from tv_app.application.services.slide_template_library_service import (
    SlideTemplateConflictError,
    SlideTemplateForbiddenError,
    SlideTemplateLibraryService,
    SlideTemplateNotFoundError,
    SlideTemplateValidationError,
)
from tv_app.core.responses import fail, ok
from tv_app.core.security import (
    TV_READ,
    TV_TEMPLATES_MANAGE,
    TV_WRITE,
    actor_sub_from_request,
    assert_permission,
    can,
)
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/slide-templates", tags=["SlideTemplates"])
_service = SlideTemplateLibraryService()


def _actor(request: Request) -> str | None:
    return actor_sub_from_request(request)


class CreateTemplateBody(BaseModel):
    label: str
    description: str | None = None
    nativeConfig: dict[str, Any]
    nativeScreenKey: str = "custom_message"
    durationSec: int | None = 45
    key: str | None = None
    publishNow: bool = False


class PatchTemplateBody(BaseModel):
    version: int = Field(..., ge=1)
    label: str | None = None
    description: str | None = None
    nativeConfig: dict[str, Any] | None = None
    nativeScreenKey: str | None = None
    durationSec: int | None = None


class FromSlideBody(BaseModel):
    label: str
    description: str | None = None
    nativeConfig: dict[str, Any]
    nativeScreenKey: str = "custom_message"
    durationSec: int | None = 45


def _deny(exc: Exception) -> Any:
    if isinstance(exc, PermissionError) and not isinstance(exc, SlideTemplateForbiddenError):
        return fail(str(exc), 403)
    if isinstance(exc, SlideTemplateForbiddenError):
        return fail(str(exc), 403)
    if isinstance(exc, SlideTemplateNotFoundError):
        return fail("Template não encontrado.", 404)
    if isinstance(exc, SlideTemplateConflictError):
        return fail(str(exc), 409, data={"current": exc.current})
    if isinstance(exc, SlideTemplateValidationError):
        return fail(str(exc), 422)
    raise exc


@router.get("")
def list_slide_templates(
    request: Request,
    status: str | None = Query(default=None),
    q: str | None = Query(default=None),
    isSystem: bool | None = Query(default=None),
):
    user = resolve_user(request)
    status_norm = (status or "").strip().lower() or None

    # Consumidores: só published (read/write).
    if status_norm == "published" and not can(user, TV_TEMPLATES_MANAGE):
        try:
            assert_permission(user, TV_READ)
        except PermissionError as exc:
            return fail(str(exc), 403)
        # write também ok via TV_READ hierarchy? Prefer allow READ or WRITE
        if not (can(user, TV_READ) or can(user, TV_WRITE)):
            return fail("Você não tem permissão para esta ação.", 403)
        return ok({"items": _service.list_published()})

    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)

    if status_norm and status_norm not in ("draft", "published", "archived"):
        return fail("status inválido.", 422)
    return ok(
        {
            "items": _service.list_library(
                status=status_norm,
                q=q,
                is_system=isSystem,
            )
        }
    )


@router.post("")
def create_slide_template(request: Request, body: CreateTemplateBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
        item = _service.create(
            label=body.label,
            description=body.description,
            native_config=body.nativeConfig,
            native_screen_key=body.nativeScreenKey,
            duration_sec=body.durationSec,
            key=body.key,
            publish_now=body.publishNow,
            owner_user_id=_actor(request),
            updated_by=_actor(request),
        )
    except Exception as exc:
        return _deny(exc)
    return ok(item, status_code=201)


@router.post("/from-slide")
def create_from_slide(request: Request, body: FromSlideBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
        item = _service.from_slide(
            label=body.label,
            description=body.description,
            native_config=body.nativeConfig,
            native_screen_key=body.nativeScreenKey,
            duration_sec=body.durationSec,
            owner_user_id=_actor(request),
            updated_by=_actor(request),
        )
    except Exception as exc:
        return _deny(exc)
    return ok(item, status_code=201)


@router.post("/import/preview")
async def import_preview(request: Request, file: UploadFile = File(...)):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    raw = await file.read()
    if not raw:
        return fail("Arquivo vazio.", 400)
    try:
        preview = _service.import_preview(raw)
    except Exception as exc:
        return _deny(exc)
    return ok(preview)


@router.post("/import/apply")
async def import_apply(
    request: Request,
    file: UploadFile = File(...),
    publishNow: bool = Query(default=False),
):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
    except PermissionError as exc:
        return fail(str(exc), 403)
    raw = await file.read()
    if not raw:
        return fail("Arquivo vazio.", 400)
    try:
        item = _service.import_apply(
            raw,
            publish_now=publishNow,
            owner_user_id=_actor(request),
            updated_by=_actor(request),
        )
    except Exception as exc:
        return _deny(exc)
    return ok(item, status_code=201)


@router.get("/{template_id}")
def get_slide_template(request: Request, template_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
        item = _service.get(template_id)
    except Exception as exc:
        return _deny(exc)
    return ok(item)


@router.patch("/{template_id}")
def patch_slide_template(request: Request, template_id: UUID, body: PatchTemplateBody):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
        item = _service.update(
            template_id,
            expected_version=body.version,
            label=body.label,
            description=body.description,
            native_config=body.nativeConfig,
            native_screen_key=body.nativeScreenKey,
            duration_sec=body.durationSec,
            updated_by=_actor(request),
        )
    except Exception as exc:
        return _deny(exc)
    return ok(item)


@router.delete("/{template_id}")
def delete_slide_template(request: Request, template_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
        item = _service.delete(template_id)
    except Exception as exc:
        return _deny(exc)
    return ok(item)


@router.post("/{template_id}/publish")
def publish_slide_template(request: Request, template_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
        item = _service.publish(template_id, updated_by=_actor(request))
    except Exception as exc:
        return _deny(exc)
    return ok(item)


@router.post("/{template_id}/unpublish")
def unpublish_slide_template(request: Request, template_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
        item = _service.unpublish(template_id, updated_by=_actor(request))
    except Exception as exc:
        return _deny(exc)
    return ok(item)


@router.post("/{template_id}/archive")
def archive_slide_template(request: Request, template_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
        item = _service.archive(template_id, updated_by=_actor(request))
    except Exception as exc:
        return _deny(exc)
    return ok(item)


@router.post("/{template_id}/clone")
def clone_slide_template(request: Request, template_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
        item = _service.clone(
            template_id,
            updated_by=_actor(request),
            owner_user_id=_actor(request),
        )
    except Exception as exc:
        return _deny(exc)
    return ok(item, status_code=201)


@router.get("/{template_id}/export")
def export_slide_template(request: Request, template_id: UUID):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_TEMPLATES_MANAGE)
        payload, filename = _service.export_mdd(
            template_id,
            exported_by=_actor(request),
        )
    except Exception as exc:
        return _deny(exc)
    return Response(
        content=payload,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
