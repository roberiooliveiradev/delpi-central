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
from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.composition.engineering_composer import (
    build_engineering_get_lmp_use_case,
    build_engineering_get_transforma_mais_summary_use_case,
    build_engineering_list_lmps_dashboard_use_case,
    build_engineering_list_lmps_use_case,
    build_engineering_list_transforma_mais_processes_use_case,
)
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.openapi_agent_metadata import (
    LMP_BY_SALE,
    LMP_DASHBOARD,
    LMP_DASHBOARD_CHARTS,
    LMP_DASHBOARD_ITEMS,
    LMP_DASHBOARD_SUMMARY,
    LMP_LIST,
    TRANSFORMA_MAIS_LIST,
    TRANSFORMA_MAIS_SUMMARY,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric
from app.utils.logger import log_error

router = APIRouter(prefix="/engineering", tags=["Engenharia"])


@router.get("/lmps", **LMP_LIST)
@require_any_permission(
    ["api-delpi.access", "dashboard-engineering.view", "dashboard-lmps.view"]
)
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
        description="Incluir contagem de PI via BOM (mais lento). Padrão: false.",
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

        return api_delpi_success(
            result.to_dict(),
            operation_id="list_lmps",
            message="LMPs listadas com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao listar LMPs: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao listar LMPs: {exc}")
        return error_response("Erro interno ao listar LMPs.", status_code=500)


@router.get("/lmps/dashboard", **LMP_DASHBOARD)
@require_any_permission(
    ["api-delpi.access", "dashboard-engineering.view", "dashboard-lmps.view"]
)
def list_lmps_dashboard_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: str = Query("Todos"),
    branch: Optional[str] = None,
    listing_type: Optional[str] = Query(
        None,
        description="Filtro de tipo: Todos, LMP, Amostra ou Outro.",
    ),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(50, ge=1, le=500),
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
        payload = use_case.execute(dto, status_filter=status)
        summary = payload.get("summary")
        if isinstance(summary, dict):
            payload = {
                **payload,
                "summary": enrich_dashboard_metric(
                    summary,
                    source_key=goal_keys.ENGINEERING_LMP,
                    start_date=date_start,
                    end_date=date_end,
                    branch=branch,
                ),
            }
        result = payload

        return api_delpi_success(
            result,
            operation_id="list_lmps_dashboard",
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


@router.get("/lmps/dashboard/summary", **LMP_DASHBOARD_SUMMARY)
@require_any_permission(
    ["api-delpi.access", "dashboard-engineering.view", "dashboard-lmps.view"]
)
def lmps_dashboard_summary_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: str = Query("Todos"),
    branch: Optional[str] = None,
    listing_type: Optional[str] = Query(None),
):
    try:
        dto = ListLMPRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            listing_type=listing_type,
        )

        use_case = build_engineering_list_lmps_dashboard_use_case()
        summary = use_case.execute_summary(dto, status_filter=status)
        summary = enrich_dashboard_metric(
            summary,
            source_key=goal_keys.ENGINEERING_LMP,
            start_date=date_start,
            end_date=date_end,
            branch=branch,
        )

        return api_delpi_success(
            summary,
            operation_id="get_lmps_dashboard_summary",
            message="KPIs do dashboard de LMPs carregados com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao carregar summary de LMPs: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar summary de LMPs: {exc}")
        return error_response(
            "Erro interno ao carregar KPIs de LMPs.",
            status_code=500,
        )


@router.get("/lmps/dashboard/items", **LMP_DASHBOARD_ITEMS)
@require_any_permission(
    ["api-delpi.access", "dashboard-engineering.view", "dashboard-lmps.view"]
)
def lmps_dashboard_items_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: str = Query("Todos"),
    branch: Optional[str] = None,
    listing_type: Optional[str] = Query(None),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(50, ge=1, le=500),
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
        result = use_case.execute_items(dto, status_filter=status)

        return api_delpi_success(
            result,
            operation_id="list_lmps_dashboard_items",
            message="Itens do dashboard de LMPs carregados com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao carregar items de LMPs: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar items de LMPs: {exc}")
        return error_response(
            "Erro interno ao carregar itens de LMPs.",
            status_code=500,
        )


@router.get("/lmps/dashboard/charts", **LMP_DASHBOARD_CHARTS)
@require_any_permission(
    ["api-delpi.access", "dashboard-engineering.view", "dashboard-lmps.view"]
)
def lmps_dashboard_charts_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: str = Query("Todos"),
    branch: Optional[str] = None,
    listing_type: Optional[str] = Query(None),
):
    try:
        dto = ListLMPRequest(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            listing_type=listing_type,
        )

        use_case = build_engineering_list_lmps_dashboard_use_case()
        charts = use_case.execute_charts(dto, status_filter=status)

        return api_delpi_success(
            charts,
            operation_id="get_lmps_dashboard_charts",
            message="Gráficos do dashboard de LMPs carregados com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao carregar charts de LMPs: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar charts de LMPs: {exc}")
        return error_response(
            "Erro interno ao carregar gráficos de LMPs.",
            status_code=500,
        )


@router.get("/lmps/{sale_number}", **LMP_BY_SALE)
@require_any_permission(
    ["api-delpi.access", "dashboard-engineering.view", "dashboard-lmps.view"]
)
def get_lmp_route(sale_number: str):
    try:
        dto = GetLMPRequest(sale_number=sale_number)

        use_case = build_engineering_get_lmp_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="get_lmp_by_sale_number",
            message=f"LMP da ordem de venda {sale_number} carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar LMP {sale_number}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar LMP {sale_number}: {exc}")
        return error_response("Erro interno ao buscar LMP.", status_code=500)


@router.get("/transforma-mais/processes", **TRANSFORMA_MAIS_LIST)
@require_any_permission(["api-delpi.access", "dashboard-engineering.view", "dashboard-lmps.view"])
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

        return api_delpi_success(
            {
                "total": len(processes),
                "items": [process.to_dict() for process in processes],
            },
            operation_id="list_transforma_mais_processes",
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


@router.get("/transforma-mais/processes/summary", **TRANSFORMA_MAIS_SUMMARY)
@require_any_permission(["api-delpi.access", "dashboard-engineering.view", "dashboard-lmps.view"])
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

        summary_result = use_case.execute(request)
        summary_payload = (
            summary_result.to_dict()
            if hasattr(summary_result, "to_dict")
            else summary_result
        )
        summary = enrich_dashboard_metric(
            summary_payload,
            source_key=goal_keys.ENGINEERING_TRANSFORMA_MAIS,
            start_date=start_date,
            end_date=end_date,
            branch=filial_id,
        )

        return api_delpi_success(
            summary,
            operation_id="get_transforma_mais_summary",
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