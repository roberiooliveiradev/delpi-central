# app/interface/http/routes/engineering/engineering_router.py

from typing import Optional

from fastapi import APIRouter, Query
from delpi_auth.authorization import require_permission, require_any_permission

from app.application.dto.lmp.get_lmp_request import GetLMPRequest
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.application.dto.transforma_mais.process_request import ProcessRequest
from app.application.dto.transforma_mais.process_summary_request import (
    ProcessSummaryRequest,
)
from app.composition.engineering_composer import (
    build_engineering_get_lmp_use_case,
    build_engineering_get_transforma_mais_summary_use_case,
    build_engineering_list_lmps_dashboard_use_case,
    build_engineering_list_lmps_use_case,
    build_engineering_list_transforma_mais_processes_use_case,
)
from app.core.responses import error_response, success_response
from app.interface.http.openapi_agent_metadata import (
    LMP_BY_SALE,
    LMP_DASHBOARD,
    LMP_LIST,
)
from app.utils.logger import log_error

router = APIRouter(prefix="/engineering", tags=["Engenharia"])


@router.get("/lmps", **LMP_LIST)
@require_any_permission(["api-delpi.access", "dashboard-lmps.view"])
def list_lmps_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    branch: Optional[str] = None,
    listing_type: Optional[str] = Query(
        None,
        description="Filtro de tipo: Todos, LMP, Amostra ou Outro.",
    ),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1),
    include_qtd_pi: Optional[bool] = Query(
        None,
        description="Incluir contagem de PI via BOM (mais lento). Padrão: true.",
    ),
):
    try:
        dto = ListLMPRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            listing_type=listing_type,
            page=page,
            page_size=page_size,
            include_qtd_pi=include_qtd_pi,
        )

        use_case = build_engineering_list_lmps_use_case()
        result = use_case.execute(dto)

        return success_response(
            data=result.to_dict(),
            message="LMPs listadas com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao listar LMPs: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar LMPs: {exc}")
        return error_response("Erro interno ao listar LMPs.", status_code=500)


@router.get("/lmps/dashboard", **LMP_DASHBOARD)
@require_any_permission(["api-delpi.access", "dashboard-lmps.view"])
def list_lmps_dashboard_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: str = Query("Todos"),
    branch: Optional[str] = None,
    listing_type: Optional[str] = Query(
        None,
        description="Filtro de tipo: Todos, LMP, Amostra ou Outro.",
    ),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1),
):
    try:
        dto = ListLMPRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            listing_type=listing_type,
            page=page,
            page_size=page_size,
        )

        use_case = build_engineering_list_lmps_dashboard_use_case()
        result = use_case.execute(dto, status_filter=status)

        return success_response(
            data=result,
            message="Dashboard de LMPs carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao listar dashboard de LMPs: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar dashboard de LMPs: {exc}")
        return error_response(
            "Erro interno ao listar dashboard de LMPs.",
            status_code=500,
        )


@router.get("/lmps/{sale_number}", **LMP_BY_SALE)
@require_any_permission(["api-delpi.access", "dashboard-lmps.view"])
def get_lmp_route(sale_number: str):
    try:
        dto = GetLMPRequest(sale_number=sale_number)

        use_case = build_engineering_get_lmp_use_case()
        result = use_case.execute(dto)

        return success_response(
            data=result,
            message=f"LMP da ordem de venda {sale_number} carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar LMP {sale_number}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar LMP {sale_number}: {exc}")
        return error_response("Erro interno ao buscar LMP.", status_code=500)


@router.get("/transforma-mais/processes")
@require_any_permission(["api-delpi.access", "dashboard-lmps.view"])
def list_processes(
    id: str | None = Query(default=None),
    name_process: str | None = Query(default=None),
    filial_id: str | None = Query(default=None),
    sector_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_engineering_list_transforma_mais_processes_use_case()

        request = ProcessRequest(
            id=id,
            name_process=name_process,
            filial_id=filial_id,
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
            message="Processos do Transforma Mais listados com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao listar processos do Transforma Mais: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar processos do Transforma Mais: {exc}")
        return error_response(
            "Erro interno ao listar processos do Transforma Mais.",
            status_code=500,
        )


@router.get("/transforma-mais/processes/summary")
@require_any_permission(["api-delpi.access", "dashboard-lmps.view"])
def get_process_summary(
    filial_id: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_engineering_get_transforma_mais_summary_use_case()

        request = ProcessSummaryRequest(
            filial_id=filial_id,
            start_date=start_date,
            end_date=end_date,
        )

        summary = use_case.execute(request)

        return success_response(
            data=summary.to_dict(),
            message="Resumo dos processos do Transforma Mais carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao gerar resumo do Transforma Mais: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao gerar resumo do Transforma Mais: {exc}")
        return error_response(
            "Erro interno ao gerar resumo dos processos do Transforma Mais.",
            status_code=500,
        )