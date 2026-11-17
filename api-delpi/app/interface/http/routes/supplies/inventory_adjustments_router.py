"""Rotas — ajustes de inventário (furo/sobra) a partir de SD3 doc='INVENT' + SB7."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_permission

from app.application.dto.supplies.inventory_adjustments_request import (
    InventoryAdjustmentsRequest,
)
from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.application.services.supplies.inventory_adjustments_tv_service import (
    InventoryAdjustmentsTvService,
)
from app.composition.supplies_composer import (
    build_get_inventory_adjustments_summary_use_case,
    build_list_inventory_adjustments_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.pagination_query import PAGE_SIZE_QUERY, TOP_LIMIT_QUERY
from app.interface.http.period_query_params import (
    END_DATE_QUERY,
    LEGACY_DATE_END_QUERY,
    LEGACY_DATE_START_QUERY,
    START_DATE_QUERY,
    resolve_period_dates,
)
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    GRANULARITY_QUERY_MONTH,
    GRANULARITY_QUERY_WEEK,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/inventory-adjustments",
    tags=["Suprimentos — Ajustes de inventário"],
)


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_inventory_adjustments_summary",
        path="/supplies/inventory-adjustments/summary",
    ),
)
@require_permission(API_DELPI_ACCESS)
def get_inventory_adjustments_summary(
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    product_code: Optional[str] = Query(default=None),
    warehouse: Optional[str] = Query(default=None),
    nature: Optional[str] = Query(
        default=None,
        description="shortage = furo de inventário | surplus = sobra de inventário",
    ),
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    try:
        request = InventoryAdjustmentsRequest(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            product_code=product_code,
            warehouse=warehouse,
            nature=nature,
        )
        result = build_get_inventory_adjustments_summary_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_inventory_adjustments_summary",
            message="Resumo de ajustes de inventário carregado com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em inventory-adjustments/summary: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível em inventory-adjustments/summary: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para os ajustes de inventário.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro em inventory-adjustments/summary: {exc}")
        return error_response(
            "Erro interno ao carregar resumo de ajustes de inventário.",
            status_code=500,
        )


@router.get(
    "",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_supplies_inventory_adjustments",
        path="/supplies/inventory-adjustments",
    ),
)
@require_permission(API_DELPI_ACCESS)
def list_inventory_adjustments(
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    product_code: Optional[str] = Query(default=None),
    warehouse: Optional[str] = Query(default=None),
    nature: Optional[str] = Query(
        default=None,
        description="shortage = furo de inventário | surplus = sobra de inventário",
    ),
    page: int = Query(1, ge=1),
    page_size: int = PAGE_SIZE_QUERY("page_50_500"),
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    try:
        request = InventoryAdjustmentsRequest(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            product_code=product_code,
            warehouse=warehouse,
            nature=nature,
            page=page,
            page_size=page_size,
        )
        result = build_list_inventory_adjustments_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="list_supplies_inventory_adjustments",
            message="Ajustes de inventário carregados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação em inventory-adjustments: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Banco indisponível em inventory-adjustments: {exc}")
        return error_response(
            "Não foi possível consultar o TOTVS para os ajustes de inventário.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro em inventory-adjustments: {exc}")
        return error_response(
            "Erro interno ao carregar ajustes de inventário.",
            status_code=500,
        )


# ── GLPI #1598 | fontes próprias para o TV Dashboard ──────────────────────
# MESMA permissão das rotas de inventário existentes: api-delpi.access.
# Os dados são consultados sob demanda; nenhuma tela/playlist é criada aqui.


def _tv_response(*, operation_id: str, action: str, **filters):
    try:
        service = InventoryAdjustmentsTvService()
        payload = getattr(service, action)(**filters)
        return api_delpi_success(
            payload,
            operation_id=operation_id,
            message="Dados de divergência de inventário para TV carregados.",
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError:
        log_error("Banco indisponível ao buscar divergências para TV.")
        return error_response(
            "Não foi possível consultar os ajustes no Protheus.", status_code=503
        )
    except Exception:
        log_error("Erro ao consultar divergências de inventário para a TV.")
        return error_response(
            "Falha interna na consulta do painel de inventário.", status_code=500
        )


@router.get(
    "/tv/summary",
    operation_id="get_supplies_inventory_adjustments_tv_summary",
    summary="Indicadores anuais e mensais de divergência de inventário",
    description="Fonte de dados somente leitura para os gráficos do GR Diário no TV Dashboard.",
)
@require_permission(API_DELPI_ACCESS)
def get_inventory_adjustments_tv_summary(
    as_of: Optional[str] = Query(
        default=None,
        description="Referência (YYYY-MM-DD, horário de São Paulo). Vazio = hoje.",
    ),
    granularity: str = GRANULARITY_QUERY_MONTH(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    warehouse: Optional[str] = Query(default=None),
):
    """KPIs: divergência bruta acumulada no ano e no mês, faltas, sobras e líquido."""
    return _tv_response(
        operation_id="get_supplies_inventory_adjustments_tv_summary",
        action="summary",
        as_of=as_of,
        branch=branch,
        granularity=granularity,
        start_date=start_date,
        end_date=end_date,
        warehouse=warehouse,
    )


@router.get(
    "/tv/monthly-series",
    operation_id="get_supplies_inventory_adjustments_tv_monthly_series",
    summary="Série mensal de faltas e sobras de inventário",
    description="Fonte de dados somente leitura para os gráficos do GR Diário no TV Dashboard.",
)
@require_permission(API_DELPI_ACCESS)
def get_inventory_adjustments_tv_monthly_series(
    as_of: Optional[str] = Query(default=None, description="YYYY-MM-DD. Vazio = hoje."),
    granularity: str = GRANULARITY_QUERY_MONTH(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    warehouse: Optional[str] = Query(default=None),
):
    """Pontos mensais (jan–mês atual) com valores brutos, faltas, sobras e líquido."""
    return _tv_response(
        operation_id="get_supplies_inventory_adjustments_tv_monthly_series",
        action="monthly_series",
        as_of=as_of,
        branch=branch,
        granularity=granularity,
        start_date=start_date,
        end_date=end_date,
        warehouse=warehouse,
    )


@router.get(
    "/tv/weekly-items",
    operation_id="get_supplies_inventory_adjustments_tv_weekly_items",
    summary="Itens com saldo líquido de inventário consolidado por produto",
    description=(
        "GR Diário: uma linha por filial e produto, compensando faltas e sobras "
        "de todos os armazéns selecionados no período. Quantidade e R$ líquidos."
    ),
)
@require_permission(API_DELPI_ACCESS)
def get_inventory_adjustments_tv_weekly_items(
    as_of: Optional[str] = Query(default=None, description="YYYY-MM-DD. Vazio = hoje."),
    granularity: str = GRANULARITY_QUERY_WEEK(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    warehouse: Optional[str] = Query(default=None),
    top_limit: int = TOP_LIMIT_QUERY(
        "top_limit_10_50",
        description="Quantidade de linhas do ranking (1 a 50; padrão 10).",
    ),
):
    """Ranking do período, com uma linha por filial × produto e saldo líquido."""
    return _tv_response(
        operation_id="get_supplies_inventory_adjustments_tv_weekly_items",
        action="weekly_items",
        as_of=as_of,
        branch=branch,
        granularity=granularity,
        start_date=start_date,
        end_date=end_date,
        warehouse=warehouse,
        top_limit=top_limit,
    )
