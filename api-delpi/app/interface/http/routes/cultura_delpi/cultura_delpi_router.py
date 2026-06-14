from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field, field_validator

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    CULTURA_DELPI_READ_PERMISSIONS,
    CULTURA_DELPI_WRITE_PERMISSIONS,
)
from app.composition.cultura_delpi_composer import build_cultura_delpi_repository
from app.core.responses import error_response
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.infrastructure.persistence.plugins.repositories.cultura_delpi.postgres_cultura_delpi_repository import (
    PostgresCulturaDelpiRepository,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.shared.utils.person_name import format_person_name
from app.utils.logger import log_error

router = APIRouter(tags=["Cultura DELPI"])


class CulturaDelpiContentBody(BaseModel):
    proposito: str = Field(default="")
    missao: str = Field(default="")
    visao: str = Field(default="")
    valores: list[str] = Field(default_factory=list)

    @field_validator("proposito", "missao", "visao", mode="before")
    @classmethod
    def validate_text_fields(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("deve ser string")
        return value.strip()

    @field_validator("valores", mode="before")
    @classmethod
    def validate_valores(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("deve ser lista de strings")
        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("cada valor deve ser string")
            normalized.append(item.strip())
        return normalized


def _current_user_id() -> str | None:
    user = get_current_user()
    if user is None:
        return None
    user_id = getattr(user, "id", None)
    return str(user_id) if user_id else None


def _current_user_name() -> str:
    user = get_current_user()
    if user is None:
        return "Usuário"
    name = getattr(user, "name", None)
    if isinstance(name, str) and name.strip():
        return format_person_name(name)
    email = getattr(user, "email", None)
    if isinstance(email, str) and email.strip():
        return email.strip()
    return "Usuário"


def _empty_content_payload() -> dict[str, object]:
    return {
        "proposito": "",
        "missao": "",
        "visao": "",
        "valores": [],
        "updatedAt": None,
        "updatedByUserId": None,
        "updatedByName": None,
    }


def _content_payload(repo: PostgresCulturaDelpiRepository) -> dict[str, object]:
    row = repo.get_content()
    if row is None:
        return _empty_content_payload()
    return repo.row_to_payload(row)


@router.get("/content")
@require_any_permission(CULTURA_DELPI_READ_PERMISSIONS)
def get_cultura_delpi_content():
    try:
        repo = build_cultura_delpi_repository()
        data = _content_payload(repo)
        return api_delpi_success(
            data,
            operation_id="get_cultura_delpi_content",
            message="Conteúdo Cultura DELPI recuperado com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao consultar conteúdo Cultura DELPI: {exc}")
        return error_response(
            "Erro interno ao consultar conteúdo Cultura DELPI.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao consultar conteúdo Cultura DELPI: {exc}")
        return error_response(
            "Erro interno ao consultar conteúdo Cultura DELPI.",
            status_code=500,
        )


@router.put("/content")
@require_any_permission(CULTURA_DELPI_WRITE_PERMISSIONS)
def update_cultura_delpi_content(
    body: Annotated[CulturaDelpiContentBody, Body(...)],
):
    try:
        repo = build_cultura_delpi_repository()
        row = repo.update_content(
            proposito=body.proposito,
            missao=body.missao,
            visao=body.visao,
            valores=body.valores,
            updated_by_user_id=_current_user_id(),
            updated_by_name=_current_user_name(),
        )
        data = repo.row_to_payload(row)
        return api_delpi_success(
            data,
            operation_id="update_cultura_delpi_content",
            message="Conteúdo Cultura DELPI atualizado com sucesso.",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao atualizar conteúdo Cultura DELPI: {exc}")
        return error_response(
            "Erro interno ao atualizar conteúdo Cultura DELPI.",
            status_code=500,
        )
    except Exception as exc:
        log_error(f"Erro inesperado ao atualizar conteúdo Cultura DELPI: {exc}")
        return error_response(
            "Erro interno ao atualizar conteúdo Cultura DELPI.",
            status_code=500,
        )
