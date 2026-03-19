# app/interface/http/routes/audit_5s_routes.py
from fastapi import APIRouter, HTTPException, Query

from delpi_auth.authorization import require_permission

from app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from app.composition.audit_5s_composer import audit_5s_get_summary_composer

router = APIRouter()


@router.get("/summary")
@require_permission("api-delpi.access")
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

        return {
            "success": True,
            "data": summary.to_dict(),
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar resumo das auditorias 5S da planilha: {str(exc)}"
        )