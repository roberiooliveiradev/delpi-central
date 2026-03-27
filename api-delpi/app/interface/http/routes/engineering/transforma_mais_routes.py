# app/interface/http/routes/engineering/transforma_mais_routes.py
from fastapi import APIRouter, Query

from delpi_auth.authorization import require_permission
from app.core.responses import success_response, error_response
from app.utils.logger import log_error

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

        return success_response(
            data={
                "total": len(processes),
                "items": [process.to_dict() for process in processes],
            },
            message="Processos do Transforma Mais listados com sucesso."
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao listar processos do Transforma Mais: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar processos do Transforma Mais: {exc}")
        return error_response(
            "Erro interno ao listar processos do Transforma Mais.",
            status_code=500
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

        return success_response(
            data=summary.to_dict(),
            message="Resumo dos processos do Transforma Mais carregado com sucesso."
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao gerar resumo do Transforma Mais: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao gerar resumo do Transforma Mais: {exc}")
        return error_response(
            "Erro interno ao gerar resumo dos processos do Transforma Mais.",
            status_code=500
        )