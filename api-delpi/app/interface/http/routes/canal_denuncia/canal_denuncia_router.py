from __future__ import annotations

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field, field_validator

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    CANAL_DENUNCIA_SUBMIT_PERMISSIONS,
)
from app.composition.canal_denuncia_composer import (
    build_create_anonymous_denuncia_use_case,
)
from app.core.responses import error_response
from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(tags=["Canal de Denúncia"])


class CreateAnonymousDenunciaBody(BaseModel):
    description: str = Field(..., min_length=10, max_length=8000)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("description deve ser string")
        normalized = value.strip()
        if len(normalized) < 10:
            raise ValueError("description deve ter ao menos 10 caracteres")
        return normalized


@router.post("/denuncias", operation_id="create_canal_denuncia")
@require_any_permission(CANAL_DENUNCIA_SUBMIT_PERMISSIONS)
def create_anonymous_denuncia(body: CreateAnonymousDenunciaBody = Body(...)):
    """Registra denúncia anônima. Autenticação necessária; identidade não é persistida."""
    try:
        use_case = build_create_anonymous_denuncia_use_case()
        data = use_case.execute(description=body.description)
        return api_delpi_success(
            data,
            operation_id="create_canal_denuncia",
            message="Denúncia registrada com sucesso.",
        )
    except PluginsRepositoryError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao registrar denúncia: {exc}")
        return error_response("Erro interno ao registrar denúncia.", status_code=500)
