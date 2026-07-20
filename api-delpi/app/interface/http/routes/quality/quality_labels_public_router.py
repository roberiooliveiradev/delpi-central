from __future__ import annotations

from fastapi import APIRouter

from app.composition.quality_labels_composer import build_quality_labels_service
from app.core.responses import error_response, not_found_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

# Rota pública (sem JWT) — liberada no auth_middleware por prefixo /public/quality-labels/.
router = APIRouter(prefix="/public/quality-labels", tags=["Quality Labels (público)"])


@router.get("/inspection/{token}", operation_id="get_public_quality_label_inspection")
def get_public_inspection(token: str):
    try:
        service = build_quality_labels_service()
        data = service.get_public(token=token)
        if data is None:
            return not_found_response("Inspeção não encontrada ou indisponível.")
        return api_delpi_success(
            data,
            operation_id="get_public_quality_label_inspection",
            message="Inspeção recuperada com sucesso.",
        )
    except Exception as exc:
        log_error(f"Erro ao consultar inspeção pública de qualidade: {exc}")
        return error_response("Erro interno ao consultar a inspeção.", status_code=500)
