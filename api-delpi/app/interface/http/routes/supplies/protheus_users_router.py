from __future__ import annotations

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_auth

from app.application.use_cases.supplies.get_protheus_user_by_email_use_case import (
    GetProtheusUserByEmailUseCase,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/protheus-users",
    tags=["Suprimentos — Usuários Protheus"],
)


@router.get("/by-email")
@require_auth()
def get_protheus_user_by_email_route(email: str = Query(..., min_length=3)):
    try:
        result = GetProtheusUserByEmailUseCase().execute(email=email)
        return api_delpi_success(
            result,
            operation_id="get_supplies_protheus_user_by_email",
            message="Consulta de usuário Protheus por e-mail concluída.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=422)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível ao consultar SYS_USR: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para o usuário Protheus.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao consultar usuário Protheus por e-mail: {exc}")
        return error_response(
            "Erro interno ao consultar usuário Protheus.",
            status_code=500,
        )
