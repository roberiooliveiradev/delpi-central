# app/interface/http/routes/engineering/engineering_router.py

from typing import Optional

from fastapi import APIRouter, Query
from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    ENGINEERING_LMP_ACCESS,
    MINI_APPLICATORS_ACCESS,
)

from app.application.dto.transforma_mais.process_request import ProcessRequest
from app.application.dto.transforma_mais.process_summary_request import (
    ProcessSummaryRequest,
)
from app.application.dto.mini_applicators.list_ferramentas_request import (
    ListMiniApplicatorsFerramentasRequest,
)
from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.application.services.response_meta_builder import ResponseMetaBuilder
from app.composition.engineering_composer import (
    build_engineering_get_lmp_history_events_use_case,
    build_engineering_get_lmp_history_flow_use_case,
    build_engineering_get_lmp_use_case,
    build_engineering_get_transforma_mais_summary_use_case,
    build_engineering_list_lmps_dashboard_use_case,
    build_engineering_list_lmps_use_case,
    build_engineering_list_transforma_mais_processes_use_case,
    build_get_mini_applicators_ferramenta_use_case,
    build_get_mini_applicators_golpes_use_case,
    build_list_mini_applicators_componentes_use_case,
    build_list_mini_applicators_ferramentas_use_case,
    build_list_mini_applicators_pecas_use_case,
)
from app.core.responses import error_response
from app.interface.http.kpi_field_labels import (
    ENGINEERING_LMP_DETAIL_FIELD_LABELS,
    ENGINEERING_LMP_FIELD_LABELS,
    ENGINEERING_TRANSFORMA_MAIS_FIELD_LABELS,
    kpi_fields,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.engineering.lmp_route_helpers import (
    build_get_lmp_history_request,
    build_get_lmp_request,
    build_list_lmp_request,
)
from app.interface.http.openapi_agent_metadata import (
    LMP_BY_SALE,
    LMP_HISTORY_EVENTS,
    LMP_HISTORY_FLOW,
    LMP_DASHBOARD,
    LMP_DASHBOARD_CHARTS,
    LMP_DASHBOARD_ITEMS,
    LMP_DASHBOARD_SUMMARY,
    LMP_LIST,
    TRANSFORMA_MAIS_LIST,
    TRANSFORMA_MAIS_SUMMARY,
    MINI_APPLICATORS_FERRAMENTAS_LIST,
    MINI_APPLICATORS_FERRAMENTA_GET,
    MINI_APPLICATORS_PECAS_LIST,
    MINI_APPLICATORS_GOLPES_GET,
    MINI_APPLICATORS_COMPONENTES_LIST,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric
from app.utils.logger import log_error

router = APIRouter(prefix="/engineering", tags=["Engenharia"])


@router.get("/lmps", **LMP_LIST)
@require_any_permission(ENGINEERING_LMP_ACCESS)
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
        dto = build_list_lmp_request(
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
@require_any_permission(ENGINEERING_LMP_ACCESS)
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
        dto = build_list_lmp_request(
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
            fields=kpi_fields(ENGINEERING_LMP_FIELD_LABELS),
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
@require_any_permission(ENGINEERING_LMP_ACCESS)
def lmps_dashboard_summary_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: str = Query("Todos"),
    branch: Optional[str] = None,
    listing_type: Optional[str] = Query(None),
):
    try:
        dto = build_list_lmp_request(
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
            fields=kpi_fields(ENGINEERING_LMP_FIELD_LABELS),
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
@require_any_permission(ENGINEERING_LMP_ACCESS)
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
        dto = build_list_lmp_request(
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
@require_any_permission(ENGINEERING_LMP_ACCESS)
def lmps_dashboard_charts_route(
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    status: str = Query("Todos"),
    branch: Optional[str] = None,
    listing_type: Optional[str] = Query(None),
):
    try:
        dto = build_list_lmp_request(
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


@router.get("/lmps/{sale_number}/history/events", **LMP_HISTORY_EVENTS)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def get_lmp_history_events_route(
    sale_number: str,
    date_start: Optional[str] = Query(
        default=None,
        description="Início do período (YYYYMMDD ou ISO). Alinha escopo ao dashboard.",
    ),
    date_end: Optional[str] = Query(
        default=None,
        description="Fim do período (YYYYMMDD ou ISO). Alinha escopo ao dashboard.",
    ),
    branch: Optional[str] = Query(
        default=None,
        description="Filial TOTVS (01/02). Recomendado quando a OV existe em mais de uma filial.",
    ),
    revision: Optional[str] = Query(
        default=None,
        description="Filtra eventos de uma revisão específica da OV.",
    ),
):
    try:
        dto = build_get_lmp_history_request(
            sale_number,
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            revision=revision,
        )

        use_case = build_engineering_get_lmp_history_events_use_case()
        result = use_case.execute(dto)
        resolved_branch = result.get("branch") or branch

        return api_delpi_success(
            result,
            operation_id="get_lmp_history_events",
            message=f"Histórico de eventos da OV {sale_number} carregado com sucesso.",
            related_routes=ResponseMetaBuilder.lmp_related_routes(
                sale_number,
                branch=resolved_branch,
            ),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar histórico da OV {sale_number}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar histórico da OV {sale_number}: {exc}")
        return error_response("Erro interno ao buscar histórico da OV.", status_code=500)


@router.get("/lmps/{sale_number}/history/flow", **LMP_HISTORY_FLOW)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def get_lmp_history_flow_route(
    sale_number: str,
    date_start: Optional[str] = Query(
        default=None,
        description="Início do período (YYYYMMDD ou ISO). Alinha escopo ao dashboard.",
    ),
    date_end: Optional[str] = Query(
        default=None,
        description="Fim do período (YYYYMMDD ou ISO). Alinha escopo ao dashboard.",
    ),
    branch: Optional[str] = Query(
        default=None,
        description="Filial TOTVS (01/02). Recomendado quando a OV existe em mais de uma filial.",
    ),
    revision: Optional[str] = Query(
        default=None,
        description="Filtra transições de uma revisão específica da OV.",
    ),
):
    try:
        dto = build_get_lmp_history_request(
            sale_number,
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            revision=revision,
        )

        use_case = build_engineering_get_lmp_history_flow_use_case()
        result = use_case.execute(dto)
        resolved_branch = result.get("branch") or branch

        return api_delpi_success(
            result,
            operation_id="get_lmp_history_flow",
            message=f"Fluxo de engenharia da OV {sale_number} carregado com sucesso.",
            related_routes=ResponseMetaBuilder.lmp_related_routes(
                sale_number,
                branch=resolved_branch,
            ),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar fluxo da OV {sale_number}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar fluxo da OV {sale_number}: {exc}")
        return error_response("Erro interno ao buscar fluxo da OV.", status_code=500)


@router.get("/lmps/{sale_number}", **LMP_BY_SALE)
@require_any_permission(ENGINEERING_LMP_ACCESS)
def get_lmp_route(
    sale_number: str,
    date_start: Optional[str] = Query(
        default=None,
        description="Início do período (YYYYMMDD ou ISO). Alinha escopo ao dashboard.",
    ),
    date_end: Optional[str] = Query(
        default=None,
        description="Fim do período (YYYYMMDD ou ISO). Alinha escopo ao dashboard.",
    ),
    branch: Optional[str] = Query(
        default=None,
        description="Filial TOTVS (01/02). Recomendado quando a OV existe em mais de uma filial.",
    ),
):
    try:
        dto = build_get_lmp_request(
            sale_number,
            date_start=date_start,
            date_end=date_end,
            branch=branch,
        )

        use_case = build_engineering_get_lmp_use_case()
        result = use_case.execute(dto)
        resolved_branch = result.get("branch") or branch

        return api_delpi_success(
            result,
            operation_id="get_lmp_by_sale_number",
            message=f"LMP da ordem de venda {sale_number} carregada com sucesso.",
            fields=kpi_fields(ENGINEERING_LMP_DETAIL_FIELD_LABELS),
            related_routes=ResponseMetaBuilder.lmp_related_routes(
                sale_number,
                branch=resolved_branch,
            ),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar LMP {sale_number}: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar LMP {sale_number}: {exc}")
        return error_response("Erro interno ao buscar LMP.", status_code=500)


@router.get("/transforma-mais/processes", **TRANSFORMA_MAIS_LIST)
@require_any_permission(ENGINEERING_LMP_ACCESS)
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
@require_any_permission(ENGINEERING_LMP_ACCESS)
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
            fields=kpi_fields(ENGINEERING_TRANSFORMA_MAIS_FIELD_LABELS),
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


@router.get("/mini-applicators/ferramentas", **MINI_APPLICATORS_FERRAMENTAS_LIST)
@require_any_permission(MINI_APPLICATORS_ACCESS)
def list_mini_applicators_ferramentas_route(
    codigo: Optional[str] = Query(None),
    descricao: Optional[str] = Query(None),
    filial: Optional[str] = Query(None),
    page: Optional[int] = Query(1, ge=1),
    page_size: Optional[int] = Query(50, ge=1, le=200),
    sort_by: Optional[str] = Query(None),
    sort_dir: Optional[str] = Query("asc", pattern="^(asc|desc)$"),
    incluir_bloqueados: bool = Query(False),
):
    try:
        request = ListMiniApplicatorsFerramentasRequest(
            codigo=codigo,
            descricao=descricao,
            filial=filial,
            page=page or 1,
            page_size=page_size or 50,
            sort_by=sort_by,
            sort_dir=sort_dir or "asc",
            incluir_bloqueados=incluir_bloqueados,
        )
        use_case = build_list_mini_applicators_ferramentas_use_case()
        result = use_case.execute(request)
        return api_delpi_success(
            result.to_dict(),
            operation_id="list_mini_applicators_ferramentas",
            message="Ferramentas listadas.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao listar ferramentas mini-aplicadores: {exc}")
        return error_response(
            "Erro interno ao listar ferramentas mini-aplicadores.",
            status_code=500,
        )


@router.get("/mini-applicators/ferramentas/{codigo}", **MINI_APPLICATORS_FERRAMENTA_GET)
@require_any_permission(MINI_APPLICATORS_ACCESS)
def get_mini_applicators_ferramenta_route(codigo: str):
    try:
        use_case = build_get_mini_applicators_ferramenta_use_case()
        result = use_case.execute(codigo)
        if result is None:
            return error_response(
                "Ferramenta não encontrada.",
                status_code=404,
                code="MINI_APPLICATOR_TOOL_NOT_FOUND",
            )
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_mini_applicators_ferramenta",
            message="Ferramenta encontrada.",
        )
    except Exception as exc:
        log_error(f"Erro ao buscar ferramenta mini-aplicador {codigo}: {exc}")
        return error_response(
            "Erro interno ao buscar ferramenta mini-aplicador.",
            status_code=500,
        )


@router.get("/mini-applicators/ferramentas/{codigo}/pecas", **MINI_APPLICATORS_PECAS_LIST)
@require_any_permission(MINI_APPLICATORS_ACCESS)
def list_mini_applicators_pecas_route(codigo: str):
    try:
        use_case = build_list_mini_applicators_pecas_use_case()
        items = use_case.execute(codigo)
        return api_delpi_success(
            {"items": items, "total": len(items)},
            operation_id="list_mini_applicators_pecas",
            message="Peças listadas.",
        )
    except Exception as exc:
        log_error(f"Erro ao listar peças mini-aplicador {codigo}: {exc}")
        return error_response(
            "Erro interno ao listar peças do mini-aplicador.",
            status_code=500,
        )


@router.get("/mini-applicators/ferramentas/{codigo}/golpes", **MINI_APPLICATORS_GOLPES_GET)
@require_any_permission(MINI_APPLICATORS_ACCESS)
def get_mini_applicators_golpes_route(
    codigo: str,
    filial: str = Query(..., min_length=2, max_length=2),
    data_inicial: str = Query(...),
    data_final: str = Query(...),
):
    try:
        use_case = build_get_mini_applicators_golpes_use_case()
        result = use_case.execute(
            filial=filial,
            codigo_ferramenta=codigo,
            data_inicial=data_inicial,
            data_final=data_final,
        )
        return api_delpi_success(
            result,
            operation_id="get_mini_applicators_golpes",
            message="Golpes calculados.",
        )
    except Exception as exc:
        log_error(f"Erro ao calcular golpes mini-aplicador {codigo}: {exc}")
        return error_response(
            "Erro interno ao calcular golpes do mini-aplicador.",
            status_code=500,
        )


@router.get("/mini-applicators/ferramentas/{codigo}/componentes", **MINI_APPLICATORS_COMPONENTES_LIST)
@require_any_permission(MINI_APPLICATORS_ACCESS)
def list_mini_applicators_componentes_route(
    codigo: str,
    filial: str = Query(..., min_length=2, max_length=2),
):
    try:
        use_case = build_list_mini_applicators_componentes_use_case()
        items = use_case.execute(codigo_ferramenta=codigo, filial=filial)
        return api_delpi_success(
            {"items": items, "total": len(items)},
            operation_id="list_mini_applicators_componentes",
            message="Componentes listados.",
        )
    except Exception as exc:
        log_error(f"Erro ao listar componentes mini-aplicador {codigo}: {exc}")
        return error_response(
            "Erro interno ao listar componentes do mini-aplicador.",
            status_code=500,
        )