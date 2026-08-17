"""Rotas autenticadas — Mural de Acessos."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, File, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    MURAL_ACESSOS_READ_PERMISSIONS,
    MURAL_ACESSOS_WRITE_PERMISSIONS,
)
from app.application.use_cases.mural_acessos.mural_acessos_use_cases import ActorContext
from app.composition.mural_acessos_composer import (
    build_create_hub_use_case,
    build_create_link_use_case,
    build_delete_hub_use_case,
    build_delete_link_image_use_case,
    build_delete_link_use_case,
    build_get_hub_use_case,
    build_list_hubs_use_case,
    build_list_links_use_case,
    build_reorder_links_use_case,
    build_render_hub_qr_use_case,
    build_resolve_link_image_use_case,
    build_update_hub_use_case,
    build_update_link_use_case,
    build_upload_link_image_use_case,
)
from app.core.responses import error_response, not_found_response
from app.domain.services.mural_acessos.exceptions import (
    MuralAcessosNotFoundError,
    MuralAcessosValidationError,
)
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

router = APIRouter(tags=["Mural de Acessos"])


class LinkBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)
    url: str = Field(..., min_length=8, max_length=2000)
    description: str = Field(default="", max_length=240)
    active: bool = True


class HubBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., min_length=1, max_length=80)
    subtitle: str = Field(default="", max_length=160)
    public_token: str | None = Field(default=None, max_length=40, alias="publicToken")


class ReorderBody(BaseModel):
    ordered_ids: list[UUID] = Field(..., min_length=1)


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


def _hub_payload(body: HubBody) -> dict[str, str | None]:
    return {
        "title": body.title,
        "subtitle": body.subtitle,
        "publicToken": body.public_token,
    }


def _handle_domain(exc: Exception):
    if isinstance(exc, MuralAcessosNotFoundError):
        return not_found_response(str(exc))
    if isinstance(exc, MuralAcessosValidationError):
        return error_response(str(exc), status_code=422, code="VALIDATION_ERROR")
    if isinstance(exc, PluginsRepositoryError):
        log_error(f"Erro de persistência mural-acessos: {exc}")
        return error_response("Erro interno de persistência.", status_code=500)
    log_error(f"Erro inesperado mural-acessos: {exc}")
    return error_response("Erro interno.", status_code=500)


@router.get("/hubs", operation_id="list_mural_acessos_hubs")
@require_any_permission(MURAL_ACESSOS_READ_PERMISSIONS)
def list_hubs():
    try:
        data = build_list_hubs_use_case().execute()
        return api_delpi_success(
            data,
            operation_id="list_mural_acessos_hubs",
            message="Murais recuperados com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.post("/hubs", operation_id="create_mural_acessos_hub")
@require_any_permission(MURAL_ACESSOS_WRITE_PERMISSIONS)
def create_hub(body: Annotated[HubBody, Body(...)]):
    try:
        data = build_create_hub_use_case().execute(_hub_payload(body))
        return api_delpi_success(
            data,
            operation_id="create_mural_acessos_hub",
            message="Mural cadastrado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.get("/hubs/{hub_id}", operation_id="get_mural_acessos_hub")
@require_any_permission(MURAL_ACESSOS_READ_PERMISSIONS)
def get_hub(hub_id: UUID):
    try:
        data = build_get_hub_use_case().execute(str(hub_id))
        return api_delpi_success(
            data,
            operation_id="get_mural_acessos_hub",
            message="Mural recuperado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.put("/hubs/{hub_id}", operation_id="update_mural_acessos_hub")
@require_any_permission(MURAL_ACESSOS_WRITE_PERMISSIONS)
def update_hub(hub_id: UUID, body: Annotated[HubBody, Body(...)]):
    try:
        data = build_update_hub_use_case().execute(str(hub_id), _hub_payload(body))
        return api_delpi_success(
            data,
            operation_id="update_mural_acessos_hub",
            message="Mural atualizado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.delete("/hubs/{hub_id}", operation_id="delete_mural_acessos_hub")
@require_any_permission(MURAL_ACESSOS_WRITE_PERMISSIONS)
def delete_hub(hub_id: UUID):
    try:
        data = build_delete_hub_use_case().execute(str(hub_id))
        return api_delpi_success(
            data,
            operation_id="delete_mural_acessos_hub",
            message="Mural removido com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.get("/hubs/{hub_id}/qr.png", operation_id="get_mural_acessos_hub_qr")
@require_any_permission(MURAL_ACESSOS_READ_PERMISSIONS)
def get_hub_qr(hub_id: UUID):
    try:
        return Response(
            content=build_render_hub_qr_use_case().execute(str(hub_id)),
            media_type="image/png",
            headers={"Cache-Control": "no-store"},
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.get("/hubs/{hub_id}/links", operation_id="list_mural_acessos_links")
@require_any_permission(MURAL_ACESSOS_READ_PERMISSIONS)
def list_links(hub_id: UUID):
    try:
        data = build_list_links_use_case().execute(str(hub_id))
        return api_delpi_success(
            data,
            operation_id="list_mural_acessos_links",
            message="Acessos recuperados com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.post("/hubs/{hub_id}/links", operation_id="create_mural_acessos_link")
@require_any_permission(MURAL_ACESSOS_WRITE_PERMISSIONS)
def create_link(hub_id: UUID, body: Annotated[LinkBody, Body(...)]):
    try:
        data = build_create_link_use_case().execute(
            str(hub_id), body.model_dump(), _actor()
        )
        return api_delpi_success(
            data,
            operation_id="create_mural_acessos_link",
            message="Acesso cadastrado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.put("/hubs/{hub_id}/links/reorder", operation_id="reorder_mural_acessos_links")
@require_any_permission(MURAL_ACESSOS_WRITE_PERMISSIONS)
def reorder_links(hub_id: UUID, body: Annotated[ReorderBody, Body(...)]):
    try:
        data = build_reorder_links_use_case().execute(
            str(hub_id),
            [str(item) for item in body.ordered_ids],
        )
        return api_delpi_success(
            data,
            operation_id="reorder_mural_acessos_links",
            message="Ordem atualizada com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.put("/links/{link_id}", operation_id="update_mural_acessos_link")
@require_any_permission(MURAL_ACESSOS_WRITE_PERMISSIONS)
def update_link(link_id: UUID, body: Annotated[LinkBody, Body(...)]):
    try:
        data = build_update_link_use_case().execute(
            str(link_id),
            body.model_dump(),
            _actor(),
        )
        return api_delpi_success(
            data,
            operation_id="update_mural_acessos_link",
            message="Acesso atualizado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.delete("/links/{link_id}", operation_id="delete_mural_acessos_link")
@require_any_permission(MURAL_ACESSOS_WRITE_PERMISSIONS)
def delete_link(link_id: UUID):
    try:
        data = build_delete_link_use_case().execute(str(link_id))
        return api_delpi_success(
            data,
            operation_id="delete_mural_acessos_link",
            message="Acesso removido com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.post("/links/{link_id}/image", operation_id="upload_mural_acessos_link_image")
@require_any_permission(MURAL_ACESSOS_WRITE_PERMISSIONS)
async def upload_link_image(
    link_id: UUID,
    file: UploadFile = File(...),
):
    try:
        content = await file.read()
        data = build_upload_link_image_use_case().execute(
            link_id=str(link_id),
            original_name=file.filename or "icon.png",
            content=content,
            mime_type=file.content_type,
            actor=_actor(),
        )
        return api_delpi_success(
            data,
            operation_id="upload_mural_acessos_link_image",
            message="Imagem anexada com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.delete("/links/{link_id}/image", operation_id="delete_mural_acessos_link_image")
@require_any_permission(MURAL_ACESSOS_WRITE_PERMISSIONS)
def delete_link_image(link_id: UUID):
    try:
        data = build_delete_link_image_use_case().execute(str(link_id), _actor())
        return api_delpi_success(
            data,
            operation_id="delete_mural_acessos_link_image",
            message="Imagem removida com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.get("/links/{link_id}/image", operation_id="get_mural_acessos_link_image")
@require_any_permission(MURAL_ACESSOS_READ_PERMISSIONS)
def get_link_image(link_id: UUID):
    try:
        path, mime = build_resolve_link_image_use_case().execute(str(link_id))
        return FileResponse(path, media_type=mime)
    except Exception as exc:
        return _handle_domain(exc)
