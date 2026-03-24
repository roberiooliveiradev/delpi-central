# app/interface/http/routes/quality/kaizen_routes.py

from fastapi import APIRouter, HTTPException, Query

from delpi_auth.authorization import require_permission

from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.composition.kaizen_composer import kaizen_get_summary_composer

router = APIRouter()


@router.get("/summary")
@require_permission("api-delpi.access")
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

        return {
            "success": True,
            "data": summary.to_dict(),
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar resumo de kaizens da planilha: {str(exc)}"
        )