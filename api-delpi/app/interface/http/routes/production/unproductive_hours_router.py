"""Rotas — horas improdutivas de produção."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from app.interface.http.pagination_query import (
    LIMIT_QUERY,
    PAGE_SIZE_QUERY,
)


from delpi_auth.authorization import require_any_permission

from app.application.dto.production.unproductive_hours_request import (
    UnproductiveHoursItemsRequest,
    UnproductiveHoursPeriod,
    UnproductiveHoursQueryRequest,
    UnproductiveHoursRankingRequest,
)
from app.application.security.api_delpi_permissions import UNPRODUCTIVE_HOURS_ACCESS
from app.composition.unproductive_hours_composer import (
    build_get_production_unproductive_hours_items_use_case,
    build_get_production_unproductive_hours_ranking_use_case,
    build_get_production_unproductive_hours_summary_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.domain.production.unproductive_hours_view_scope import (
    DEFAULT_ITEMS_SORT,
    DEFAULT_RANKING_LIMIT,
    ITEMS_SORT_VALUES,
    MAX_PAGE_SIZE,
    MAX_RANKING_LIMIT,
    METRIC_HOURS,
    METRIC_VALUES,
    RANK_BY_VALUES,
)
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.period_query_params import (
    END_DATE_QUERY,
    LEGACY_DATE_END_QUERY,
    LEGACY_DATE_START_QUERY,
    START_DATE_QUERY,
    resolve_period_dates,
)
from app.interface.http.query_param_enums import BRANCH_QUERY_OPTIONAL
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/production/unproductive-hours",
    tags=["Produção — Horas improdutivas"],
)

_STOP_REASON_PATTERN = r"^[A-Za-z0-9]{1,6}$"
_CODE_PATTERN = r"^.{0,40}$"

_SUMMARY_FIELDS = {
    "total_appointments": {"label": "Total appointments", "type": "integer"},
    "total_hours": {"label": "Total hours", "type": "number"},
    "total_cost": {"label": "Total cost (BRL)", "type": "number"},
    "avg_cost_per_hour": {"label": "Avg cost/hour (BRL)", "type": "number"},
    "totalApontamentos": {"label": "Total de apontamentos", "type": "integer"},
    "totalHoras": {"label": "Total de horas", "type": "number"},
    "totalCusto": {"label": "Custo total (R$)", "type": "number"},
    "custoMedioHora": {"label": "Custo médio/hora (R$)", "type": "number"},
    "registrosSemCusto": {"label": "Registros sem custo", "type": "integer"},
    "horasSemCusto": {"label": "Horas sem custo", "type": "number"},
    "percentualHorasSemCusto": {"label": "% horas sem custo", "type": "number"},
}

_ITEM_FIELDS = {
    "reference_date": {"label": "Reference date", "type": "string", "format": "date"},
    "branch": {"label": "Branch", "type": "string"},
    "hours": {"label": "Hours", "type": "number"},
    "stop_reason": {"label": "Stop reason", "type": "string"},
    "stop_reason_description": {"label": "Stop reason description", "type": "string"},
    "dataReferencia": {"label": "Data de referência", "type": "string", "format": "date"},
    "filial": {"label": "Filial", "type": "string"},
    "op": {"label": "OP", "type": "string"},
    "produto": {"label": "Produto", "type": "string"},
    "operacao": {"label": "Operação", "type": "string"},
    "recurso": {"label": "Recurso", "type": "string"},
    "centroCusto": {"label": "Centro de custo", "type": "string"},
    "codigoOperador": {"label": "Código do operador", "type": "string"},
    "nomeOperador": {"label": "Nome do operador", "type": "string"},
    "motivo": {"label": "Motivo", "type": "string"},
    "motivoDescricao": {"label": "Descrição do motivo", "type": "string"},
    "observacao": {"label": "Observação", "type": "string"},
    "tempoHoras": {"label": "Horas", "type": "number"},
    "valorParada": {"label": "Valor da parada (R$)", "type": "number"},
    "fonteCusto": {"label": "Fonte de custo", "type": "string"},
}

_RANKING_FIELDS = {
    "rank": {"label": "Posição", "type": "integer"},
    "motivo": {"label": "Motivo", "type": "string"},
    "motivoDescricao": {"label": "Descrição do motivo", "type": "string"},
    "recurso": {"label": "Recurso", "type": "string"},
    "centroCusto": {"label": "Centro de custo", "type": "string"},
    "codigoOperador": {"label": "Código do operador", "type": "string"},
    "nomeOperador": {"label": "Nome do operador", "type": "string"},
    "produto": {"label": "Produto", "type": "string"},
    "operacao": {"label": "Operação", "type": "string"},
    "totalApontamentos": {"label": "Total de apontamentos", "type": "integer"},
    "totalHoras": {"label": "Total de horas", "type": "number"},
    "totalCusto": {"label": "Custo total (R$)", "type": "number"},
    "horasSemCusto": {"label": "Horas sem custo", "type": "number"},
}


def _build_period(
    *,
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
    date_start: str | None,
    date_end: str | None,
) -> UnproductiveHoursPeriod:
    resolved_start, resolved_end = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    return UnproductiveHoursPeriod.resolve(
        branch=branch,
        start_date=resolved_start,
        end_date=resolved_end,
    )


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_unproductive_hours_summary",
        path="/production/unproductive-hours/summary",
    ),
)
@require_any_permission(UNPRODUCTIVE_HOURS_ACCESS)
def get_production_unproductive_hours_summary(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    stop_reason: Optional[str] = Query(
        default=None,
        description="Stop reason code from the view (e.g. RT, OT, MT). Empty = all reasons.",
        pattern=_STOP_REASON_PATTERN,
    ),
    resource: Optional[str] = Query(
        default=None,
        description="Production resource code filter.",
        pattern=_CODE_PATTERN,
    ),
    cost_center: Optional[str] = Query(
        default=None,
        description="Cost center code filter.",
        pattern=_CODE_PATTERN,
    ),
    operator_code: Optional[str] = Query(
        default=None,
        description="Operator code filter.",
        pattern=_CODE_PATTERN,
    ),
):
    try:
        period = _build_period(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        request = UnproductiveHoursQueryRequest(
            period=period,
            stop_reason=stop_reason,
            resource=resource,
            cost_center=cost_center,
            operator_code=operator_code,
        )
        result = build_get_production_unproductive_hours_summary_use_case().execute(
            request
        )
        return api_delpi_success(
            result,
            operation_id="get_production_unproductive_hours_summary",
            message="Resumo de horas improdutivas buscado com sucesso.",
            fields=_SUMMARY_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar resumo de horas improdutivas: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de banco ao buscar resumo de horas improdutivas: {exc}")
        return error_response(
            "Erro de conexão com o banco ao buscar resumo de horas improdutivas.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar resumo de horas improdutivas: {exc}")
        return error_response(
            "Erro interno ao buscar resumo de horas improdutivas.",
            status_code=500,
        )


@router.get(
    "/items",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_unproductive_hours_items",
        path="/production/unproductive-hours/items",
    ),
)
@require_any_permission(UNPRODUCTIVE_HOURS_ACCESS)
def get_production_unproductive_hours_items(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    stop_reason: Optional[str] = Query(
        default=None,
        description="Stop reason code from the view (e.g. RT, OT, MT). Empty = all reasons.",
        pattern=_STOP_REASON_PATTERN,
    ),
    resource: Optional[str] = Query(
        default=None,
        description="Production resource code filter.",
        pattern=_CODE_PATTERN,
    ),
    cost_center: Optional[str] = Query(
        default=None,
        description="Cost center code filter.",
        pattern=_CODE_PATTERN,
    ),
    operator_code: Optional[str] = Query(
        default=None,
        description="Operator code filter.",
        pattern=_CODE_PATTERN,
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = PAGE_SIZE_QUERY("page_50_200", description="Rows per page (max 200)."),
    sort: str = Query(
        default=DEFAULT_ITEMS_SORT,
        description="Sort key for unproductive hours items.",
        enum=list(ITEMS_SORT_VALUES),
        pattern="^(" + "|".join(ITEMS_SORT_VALUES) + ")$",
    ),
):
    try:
        period = _build_period(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        request = UnproductiveHoursItemsRequest(
            period=period,
            stop_reason=stop_reason,
            resource=resource,
            cost_center=cost_center,
            operator_code=operator_code,
            page=page,
            page_size=page_size,
            sort=sort,
        )
        result = build_get_production_unproductive_hours_items_use_case().execute(
            request
        )
        return api_delpi_success(
            result,
            operation_id="get_production_unproductive_hours_items",
            message="Itens de horas improdutivas buscados com sucesso.",
            fields=_ITEM_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar itens de horas improdutivas: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de banco ao buscar itens de horas improdutivas: {exc}")
        return error_response(
            "Erro de conexão com o banco ao buscar itens de horas improdutivas.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar itens de horas improdutivas: {exc}")
        return error_response(
            "Erro interno ao buscar itens de horas improdutivas.",
            status_code=500,
        )


@router.get(
    "/ranking",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_unproductive_hours_ranking",
        path="/production/unproductive-hours/ranking",
    ),
)
@require_any_permission(UNPRODUCTIVE_HOURS_ACCESS)
def get_production_unproductive_hours_ranking(
    rank_by: str = Query(
        ...,
        description=(
            "Ranking dimension: stop_reason, resource, cost_center, "
            "operator, product or operation."
        ),
        enum=list(RANK_BY_VALUES),
        pattern="^(" + "|".join(RANK_BY_VALUES) + ")$",
    ),
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    stop_reason: Optional[str] = Query(
        default=None,
        description="Stop reason code from the view (e.g. RT, OT, MT). Empty = all reasons.",
        pattern=_STOP_REASON_PATTERN,
    ),
    resource: Optional[str] = Query(
        default=None,
        description="Production resource code filter.",
        pattern=_CODE_PATTERN,
    ),
    cost_center: Optional[str] = Query(
        default=None,
        description="Cost center code filter.",
        pattern=_CODE_PATTERN,
    ),
    operator_code: Optional[str] = Query(
        default=None,
        description="Operator code filter.",
        pattern=_CODE_PATTERN,
    ),
    metric: str = Query(
        default=METRIC_HOURS,
        description="Ranking metric: hours or cost (descending).",
        enum=list(METRIC_VALUES),
        pattern="^(" + "|".join(METRIC_VALUES) + ")$",
    ),
    limit: int = LIMIT_QUERY("limit_ranking_10_50", description="Top N rows (max 50)."),
):
    try:
        period = _build_period(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            date_start=date_start,
            date_end=date_end,
        )
        request = UnproductiveHoursRankingRequest(
            period=period,
            stop_reason=stop_reason,
            resource=resource,
            cost_center=cost_center,
            operator_code=operator_code,
            rank_by=rank_by,
            metric=metric,
            limit=limit,
        )
        result = build_get_production_unproductive_hours_ranking_use_case().execute(
            request
        )
        return api_delpi_success(
            result,
            operation_id="get_production_unproductive_hours_ranking",
            message="Ranking de horas improdutivas buscado com sucesso.",
            fields=_RANKING_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao buscar ranking de horas improdutivas: {exc}")
        return error_response(str(exc), status_code=400)
    except DatabaseConnectionError as exc:
        log_error(f"Erro de banco ao buscar ranking de horas improdutivas: {exc}")
        return error_response(
            "Erro de conexão com o banco ao buscar ranking de horas improdutivas.",
            status_code=503,
        )
    except Exception as exc:
        log_error(f"Erro ao buscar ranking de horas improdutivas: {exc}")
        return error_response(
            "Erro interno ao buscar ranking de horas improdutivas.",
            status_code=500,
        )
