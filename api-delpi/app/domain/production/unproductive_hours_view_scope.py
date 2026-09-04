"""Escopo — horas improdutivas (VW_BI_RT_HORAS_IMPRODUTIVAS)."""

from __future__ import annotations

from app.domain.services.pagination_tier_service import PaginationTierService

UNPRODUCTIVE_HOURS_VIEW = "dbo.VW_BI_RT_HORAS_IMPRODUTIVAS"

VALID_UNPRODUCTIVE_HOURS_BRANCHES = frozenset({"01", "02"})

FONTE_CUSTO_SEM_CUSTO = "SEM CUSTO"

OPERADOR_SEM_NOME_LABEL = "Sem nome cadastrado"

RANK_BY_STOP_REASON = "stop_reason"
RANK_BY_RESOURCE = "resource"
RANK_BY_COST_CENTER = "cost_center"
RANK_BY_OPERATOR = "operator"
RANK_BY_PRODUCT = "product"
RANK_BY_OPERATION = "operation"

RANK_BY_VALUES = (
    RANK_BY_STOP_REASON,
    RANK_BY_RESOURCE,
    RANK_BY_COST_CENTER,
    RANK_BY_OPERATOR,
    RANK_BY_PRODUCT,
    RANK_BY_OPERATION,
)

METRIC_HOURS = "hours"
METRIC_COST = "cost"
METRIC_VALUES = (METRIC_HOURS, METRIC_COST)

DEFAULT_MONTHS_WINDOW = 12
MAX_MONTHS_WINDOW = 24
DEFAULT_RANKING_LIMIT = 10
MAX_RANKING_LIMIT = 50
DEFAULT_PAGE_SIZE = PaginationTierService.require_int("page_50_200", None)
MAX_PAGE_SIZE = int(PaginationTierService.max_size("page_50_200") or 0)
ITEMS_SORT_VALUES = (
    "date_desc",
    "date_asc",
    "hours_desc",
    "hours_asc",
    "cost_desc",
    "cost_asc",
)
DEFAULT_ITEMS_SORT = "date_desc"
