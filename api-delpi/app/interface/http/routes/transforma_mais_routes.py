# app/interface/http/routes/transforma_mais_routes.py
from fastapi import APIRouter, HTTPException, Query

from delpi_auth.authorization import require_permission

from app.application.dto.transforma_mais.process_request import ProcessRequest
from app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from app.composition.transforma_mais_composer import (
    transforma_mais_get_process_summary_composer,
    transforma_mais_list_process_composer,
)

router = APIRouter()


@router.get("/processes")
@require_permission("api-delpi.access")
def list_processes(
    id: str | None = Query(default=None),
    name_process: str | None = Query(default=None),
    sector_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = transforma_mais_list_process_composer()

        request = ProcessRequest(
            id=id,
            name_process=name_process,
            sector_name=sector_name,
            status=status,
            start_date=start_date,
            end_date=end_date,
        )

        processes = use_case.execute(request)

        return {
            "success": True,
            "total": len(processes),
            "items": [process.to_dict() for process in processes],
        }

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar processos da planilha: {str(exc)}"
        )


@router.get("/processes/summary")
@require_permission("api-delpi.access")
def get_process_summary(
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = transforma_mais_get_process_summary_composer()

        request = ProcessSummaryRequest(
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
            detail=f"Erro ao gerar resumo dos processos da planilha: {str(exc)}"
        )