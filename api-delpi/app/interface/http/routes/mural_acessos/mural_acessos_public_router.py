"""Rotas públicas (sem JWT) — menu do mural via QR."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from fastapi.responses import FileResponse

from app.application.services.mural_acessos.mural_acessos_qr_service import (
    MURAL_ACESSOS_DEFAULT_PUBLIC_TOKEN,
)
from app.composition.mural_acessos_composer import (
    build_list_public_menu_use_case,
    build_resolve_link_image_use_case,
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
from app.utils.logger import log_error

router = APIRouter(prefix="/public/mural-acessos", tags=["Mural de Acessos — público"])


def _handle_domain(exc: Exception):
    if isinstance(exc, MuralAcessosNotFoundError):
        return not_found_response(str(exc))
    if isinstance(exc, MuralAcessosValidationError):
        return error_response(str(exc), status_code=422, code="VALIDATION_ERROR")
    if isinstance(exc, PluginsRepositoryError):
        log_error(f"Erro de persistência mural-acessos público: {exc}")
        return error_response("Erro interno de persistência.", status_code=500)
    log_error(f"Erro inesperado mural-acessos público: {exc}")
    return error_response("Erro interno.", status_code=500)


def _public_menu(token: str, operation_id: str):
    try:
        data = build_list_public_menu_use_case().execute(token)
        return api_delpi_success(
            data,
            operation_id=operation_id,
            message="Menu do mural recuperado com sucesso.",
        )
    except Exception as exc:
        return _handle_domain(exc)


@router.get("/menu", operation_id="list_public_mural_acessos_menu")
def list_public_menu():
    return _public_menu(
        MURAL_ACESSOS_DEFAULT_PUBLIC_TOKEN,
        "list_public_mural_acessos_menu",
    )


@router.get("/menu/{public_token}", operation_id="list_public_mural_acessos_menu_by_token")
def list_public_menu_by_token(public_token: str):
    return _public_menu(public_token, "list_public_mural_acessos_menu_by_token")


@router.get("/links/{link_id}/image", operation_id="get_public_mural_acessos_link_image")
def get_public_link_image(link_id: UUID):
    try:
        path, mime = build_resolve_link_image_use_case().execute(
            str(link_id),
            public_only=True,
        )
        return FileResponse(
            path,
            media_type=mime,
            headers={"Cache-Control": "public, max-age=300"},
        )
    except Exception as exc:
        return _handle_domain(exc)
