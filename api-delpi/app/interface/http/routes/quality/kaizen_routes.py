# app/interface/http/routes/quality/kaizen_routes.py
from fastapi import APIRouter, Query

from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.composition.kaizen_composer import kaizen_get_summary_composer

router = APIRouter()


@router.get("/summary")
@require_permission("api-delpi.quality.access")
def get_kaizen_summary(
    title: str | None = Query(default=None),
    status: str | None = Query(default=None),
    date_start: str | None = Query(default=None),
    date_end: str | None = Query(default=None),
):
    try:
        use_case = kaizen_get_summary_composer()

        request = KaizenSummaryRequest(
            title=title,
            status=status,
            date_start=date_start,
            date_end=date_end,
        )

        summary = use_case.execute(request)

        return success_response(data=summary.to_dict())

    except ValueError as exc:
        log_error(f"Erro de validação ao gerar resumo de kaizens: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao gerar resumo de kaizens: {exc}")
        return error_response(
            "Erro interno ao gerar resumo de kaizens.",
            status_code=500,
        )