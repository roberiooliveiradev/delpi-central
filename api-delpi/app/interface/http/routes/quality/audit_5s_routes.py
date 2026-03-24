# app/interface/http/routes/quality/audit_5s_routes.py
from fastapi import APIRouter, Query

from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from app.composition.audit_5s_composer import audit_5s_get_summary_composer

router = APIRouter()


@router.get("/summary")
@require_permission("api-delpi.quality.access")
def get_audit_5s_summary(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = audit_5s_get_summary_composer()

        request = Audit5SSummaryRequest(
            start_date=start_date,
            end_date=end_date,
        )

        summary = use_case.execute(request)

        return success_response(data=summary.to_dict())

    except ValueError as exc:
        log_error(f"Erro de validação ao gerar resumo das auditorias 5S: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao gerar resumo das auditorias 5S: {exc}")
        return error_response(
            "Erro interno ao gerar resumo das auditorias 5S.",
            status_code=500,
        )