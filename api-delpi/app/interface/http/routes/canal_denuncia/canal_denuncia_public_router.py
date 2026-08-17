"""Rotas públicas (sem JWT) — formulário aberto do Canal de Denúncia."""

from __future__ import annotations

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field, field_validator

from app.composition.canal_denuncia_composer import (
    build_create_anonymous_denuncia_use_case,
)
from app.core.responses import error_response
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(prefix="/public/canal-denuncia", tags=["Canal de Denúncia — público"])

_OPERATION_ID = "create_public_canal_denuncia"


class PublicDenunciaBody(BaseModel):
    description: str = Field(..., min_length=10, max_length=8000)
    website: str | None = Field(default=None, max_length=200)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("description deve ser string")
        normalized = value.strip()
        if len(normalized) < 10:
            raise ValueError("description deve ter ao menos 10 caracteres")
        return normalized


@router.post("/denuncias", operation_id=_OPERATION_ID)
def create_public_canal_denuncia(body: PublicDenunciaBody = Body(...)):
    if (body.website or "").strip():
        return api_delpi_success(
            {"id": None, "createdAt": None, "accepted": True},
            operation_id=_OPERATION_ID,
            message="Denúncia registrada com sucesso.",
        )
    try:
        use_case = build_create_anonymous_denuncia_use_case()
        data = use_case.execute(description=body.description)
        return api_delpi_success(
            data,
            operation_id=_OPERATION_ID,
            message="Denúncia registrada com sucesso.",
        )
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao registrar denúncia pública: {exc}")
        return error_response("Erro interno ao registrar denúncia.", status_code=500)
