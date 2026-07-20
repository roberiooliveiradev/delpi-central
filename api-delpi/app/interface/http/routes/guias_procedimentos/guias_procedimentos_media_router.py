"""Rotas de mídias e anexos — Guias e Procedimentos (admin + leitura)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import BaseModel, Field

from delpi_auth.authorization import require_any_permission
from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    GUIAS_PROCEDIMENTOS_MANAGE,
    GUIAS_PROCEDIMENTOS_READ_PERMISSIONS,
    GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS,
)
from app.application.services.guias_procedimentos.guide_media_file_response import (
    build_file_response,
)
from app.application.services.guias_procedimentos.guide_media_storage import (
    GuiasMediaStorageError,
)
from app.application.use_cases.guias_procedimentos.admin_guias_use_cases import (
    ActorContext,
)
from app.composition.guias_procedimentos_composer import (
    build_archive_attachment_use_case,
    build_archive_media_use_case,
    build_create_external_video_use_case,
    build_list_admin_procedure_attachments_use_case,
    build_list_admin_procedure_media_use_case,
    build_list_readable_procedure_attachments_use_case,
    build_list_readable_procedure_media_use_case,
    build_resolve_attachment_file_use_case,
    build_resolve_media_file_use_case,
    build_update_attachment_metadata_use_case,
    build_update_media_metadata_use_case,
    build_upload_procedure_attachment_use_case,
    build_upload_procedure_image_use_case,
    build_upload_procedure_video_use_case,
)
from app.core.responses import error_response, not_found_response
from app.domain.services.guias_procedimentos.exceptions import (
    GuiasConflictError,
    GuiasNotFoundError,
    GuiasValidationError,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

admin_media_router = APIRouter(tags=["Guias e Procedimentos — Admin Media"])
read_media_router = APIRouter(tags=["Guias e Procedimentos — Media"])


class ExternalVideoBody(BaseModel):
    url: str = Field(..., min_length=8, max_length=2000)
    title: str = Field(default="", max_length=300)
    order_index: int = Field(default=0, ge=0)


class MediaMetadataBody(BaseModel):
    title: str = Field(default="", max_length=300)
    alt_text: str = Field(default="", max_length=500)
    order_index: int = Field(default=0, ge=0)


class AttachmentMetadataBody(BaseModel):
    title: str = Field(default="", max_length=300)
    order_index: int = Field(default=0, ge=0)


def _actor() -> ActorContext:
    user = get_current_user()
    if user is None:
        return ActorContext(None, None)
    user_id = getattr(user, "id", None)
    name = getattr(user, "name", None)
    if isinstance(name, str) and name.strip():
        display = format_person_name(name)
    else:
        email = getattr(user, "email", None)
        display = email.strip() if isinstance(email, str) and email.strip() else None
    return ActorContext(str(user_id) if user_id else None, display)


def _can_manage() -> bool:
    user = get_current_user()
    if user is None:
        return False
    return has_permission(user, GUIAS_PROCEDIMENTOS_MANAGE)


def _handle_domain(exc: Exception):
    if isinstance(exc, GuiasNotFoundError):
        return not_found_response(str(exc))
    if isinstance(exc, GuiasConflictError):
        return error_response(str(exc), status_code=409, code="CONFLICT", recoverable=False)
    if isinstance(exc, (GuiasValidationError, GuiasMediaStorageError)):
        return error_response(str(exc), status_code=422, code="VALIDATION_ERROR")
    if isinstance(exc, PluginsRepositoryError):
        log_error(f"Erro de persistência guias media: {exc}")
        return error_response("Erro interno de persistência.", status_code=500)
    log_error(f"Erro inesperado guias media: {exc}")
    return error_response("Erro interno.", status_code=500)


# --- admin ---


@admin_media_router.get("/admin/procedures/{procedure_id}/media", operation_id="list_guias_procedimentos_admin_procedure_media")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def list_admin_procedure_media(procedure_id: UUID):
    try:
        data = build_list_admin_procedure_media_use_case().execute(str(procedure_id))
        return api_delpi_success(
            data,
            operation_id="list_guias_procedimentos_admin_procedure_media",
            message="Mídias recuperadas com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@admin_media_router.get("/admin/procedures/{procedure_id}/attachments", operation_id="list_guias_procedimentos_admin_procedure_attachments")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def list_admin_procedure_attachments(procedure_id: UUID):
    try:
        data = build_list_admin_procedure_attachments_use_case().execute(
            str(procedure_id)
        )
        return api_delpi_success(
            data,
            operation_id="list_guias_procedimentos_admin_procedure_attachments",
            message="Anexos recuperados com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@admin_media_router.post("/admin/procedures/{procedure_id}/media/images", operation_id="upload_guias_procedimentos_admin_procedure_image")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
async def upload_procedure_image(
    procedure_id: UUID,
    file: UploadFile = File(...),
    title: Annotated[str, Form()] = "",
    alt_text: Annotated[str, Form()] = "",
    order_index: Annotated[int, Form()] = 0,
):
    try:
        content = await file.read()
        data = build_upload_procedure_image_use_case().execute(
            str(procedure_id),
            original_name=file.filename or "image.bin",
            content=content,
            mime_type=file.content_type,
            title=title,
            alt_text=alt_text,
            order_index=order_index,
            actor=_actor(),
        )
        return api_delpi_success(
            data,
            operation_id="upload_guias_procedimentos_admin_procedure_image",
            message="Imagem enviada com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@admin_media_router.post("/admin/procedures/{procedure_id}/media/videos", operation_id="upload_guias_procedimentos_admin_procedure_video")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
async def upload_procedure_video(
    procedure_id: UUID,
    file: UploadFile = File(...),
    title: Annotated[str, Form()] = "",
    order_index: Annotated[int, Form()] = 0,
):
    try:
        content = await file.read()
        data = build_upload_procedure_video_use_case().execute(
            str(procedure_id),
            original_name=file.filename or "video.bin",
            content=content,
            mime_type=file.content_type,
            title=title,
            order_index=order_index,
            actor=_actor(),
        )
        return api_delpi_success(
            data,
            operation_id="upload_guias_procedimentos_admin_procedure_video",
            message="Vídeo enviado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@admin_media_router.post("/admin/procedures/{procedure_id}/media/external-videos", operation_id="create_guias_procedimentos_admin_external_video")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def create_external_video(procedure_id: UUID, body: ExternalVideoBody):
    try:
        data = build_create_external_video_use_case().execute(
            str(procedure_id),
            url=body.url,
            title=body.title,
            order_index=body.order_index,
            actor=_actor(),
        )
        return api_delpi_success(
            data,
            operation_id="create_guias_procedimentos_admin_external_video",
            message="Vídeo externo cadastrado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@admin_media_router.post("/admin/procedures/{procedure_id}/attachments", operation_id="upload_guias_procedimentos_admin_procedure_attachment")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
async def upload_procedure_attachment(
    procedure_id: UUID,
    file: UploadFile = File(...),
    title: Annotated[str, Form()] = "",
    order_index: Annotated[int, Form()] = 0,
):
    try:
        content = await file.read()
        data = build_upload_procedure_attachment_use_case().execute(
            str(procedure_id),
            original_name=file.filename or "attachment.bin",
            content=content,
            mime_type=file.content_type,
            title=title,
            order_index=order_index,
            actor=_actor(),
        )
        return api_delpi_success(
            data,
            operation_id="upload_guias_procedimentos_admin_procedure_attachment",
            message="Anexo enviado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@admin_media_router.put("/admin/media/{media_id}", operation_id="update_guias_procedimentos_admin_media")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def update_media_metadata(media_id: UUID, body: MediaMetadataBody):
    try:
        data = build_update_media_metadata_use_case().execute(
            str(media_id),
            title=body.title,
            alt_text=body.alt_text,
            order_index=body.order_index,
            actor=_actor(),
        )
        return api_delpi_success(
            data,
            operation_id="update_guias_procedimentos_admin_media",
            message="Mídia atualizada com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@admin_media_router.post("/admin/media/{media_id}/archive", operation_id="archive_guias_procedimentos_admin_media")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def archive_media(media_id: UUID):
    try:
        data = build_archive_media_use_case().execute(str(media_id), actor=_actor())
        return api_delpi_success(
            data,
            operation_id="archive_guias_procedimentos_admin_media",
            message="Mídia arquivada com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@admin_media_router.put("/admin/attachments/{attachment_id}", operation_id="update_guias_procedimentos_admin_attachment")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def update_attachment_metadata(attachment_id: UUID, body: AttachmentMetadataBody):
    try:
        data = build_update_attachment_metadata_use_case().execute(
            str(attachment_id),
            title=body.title,
            order_index=body.order_index,
            actor=_actor(),
        )
        return api_delpi_success(
            data,
            operation_id="update_guias_procedimentos_admin_attachment",
            message="Anexo atualizado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@admin_media_router.post("/admin/attachments/{attachment_id}/archive", operation_id="archive_guias_procedimentos_admin_attachment")
@require_any_permission(GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS)
def archive_attachment(attachment_id: UUID):
    try:
        data = build_archive_attachment_use_case().execute(
            str(attachment_id), actor=_actor()
        )
        return api_delpi_success(
            data,
            operation_id="archive_guias_procedimentos_admin_attachment",
            message="Anexo arquivado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


# --- leitura protegida ---


@read_media_router.get("/procedures/{procedure_id}/media", operation_id="list_guias_procedimentos_procedure_media")
@require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)
def list_readable_procedure_media(procedure_id: UUID):
    try:
        data = build_list_readable_procedure_media_use_case().execute(
            str(procedure_id),
            can_manage=_can_manage(),
        )
        return api_delpi_success(
            data,
            operation_id="list_guias_procedimentos_procedure_media",
            message="Mídias recuperadas com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@read_media_router.get("/procedures/{procedure_id}/attachments", operation_id="list_guias_procedimentos_procedure_attachments")
@require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)
def list_readable_procedure_attachments(procedure_id: UUID):
    try:
        data = build_list_readable_procedure_attachments_use_case().execute(
            str(procedure_id),
            can_manage=_can_manage(),
        )
        return api_delpi_success(
            data,
            operation_id="list_guias_procedimentos_procedure_attachments",
            message="Anexos recuperados com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@read_media_router.get("/media/{media_id}/file", operation_id="download_guias_procedimentos_media_file")
@require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)
def download_media_file(media_id: UUID, request: Request):
    try:
        resolved = build_resolve_media_file_use_case().execute(
            str(media_id),
            can_manage=_can_manage(),
        )
        enable_range = resolved.get("media_kind") == "video_file"
        return build_file_response(
            path=resolved["path"],
            request=request,
            media_type=resolved.get("mime_type"),
            filename=str(resolved.get("filename") or "file"),
            enable_range=enable_range,
        )
    except Exception as exc:
        return _handle_domain(exc)


@read_media_router.get("/attachments/{attachment_id}/file", operation_id="download_guias_procedimentos_attachment_file")
@require_any_permission(GUIAS_PROCEDIMENTOS_READ_PERMISSIONS)
def download_attachment_file(attachment_id: UUID, request: Request):
    try:
        resolved = build_resolve_attachment_file_use_case().execute(
            str(attachment_id),
            can_manage=_can_manage(),
        )
        return build_file_response(
            path=resolved["path"],
            request=request,
            media_type=resolved.get("mime_type"),
            filename=str(resolved.get("filename") or "file"),
            enable_range=False,
        )
    except Exception as exc:
        return _handle_domain(exc)
