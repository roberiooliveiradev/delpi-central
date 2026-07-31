"""Escopo — ordens de produção PCP (VW_PCP_ORDENS_PRODUCAO)."""

from __future__ import annotations

PCP_ORDERS_VIEW = "dbo.VW_PCP_ORDENS_PRODUCAO"

VALID_PCP_ORDERS_BRANCHES = frozenset({"01", "02"})

RANK_BY_PRODUCT = "product"
RANK_BY_WAREHOUSE = "warehouse"
RANK_BY_OP = "op"

RANK_BY_VALUES = (RANK_BY_PRODUCT, RANK_BY_WAREHOUSE, RANK_BY_OP)

METRIC_ORDER_QTY = "order_qty"
METRIC_REPORTED_QTY = "reported_qty"
METRIC_BALANCE = "balance"
METRIC_DELAY_DAYS = "delay_days"

METRIC_VALUES = (
    METRIC_ORDER_QTY,
    METRIC_REPORTED_QTY,
    METRIC_BALANCE,
    METRIC_DELAY_DAYS,
)

DEFAULT_MONTHS_WINDOW = 12
MAX_MONTHS_WINDOW = 24
DEFAULT_RANKING_LIMIT = 10
MAX_RANKING_LIMIT = 50
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

ITEMS_SORT_VALUES = (
    "delivery_desc",
    "delivery_asc",
    "issue_desc",
    "issue_asc",
    "delay_desc",
    "delay_asc",
    "qty_desc",
    "qty_asc",
    "op_asc",
    "op_desc",
)
DEFAULT_ITEMS_SORT = "delivery_desc"

# Flags na view: FL_OP_EM_ABERTO / FL_OP_MAE = bit 0/1; FL_ATRASADA / FL_TEM_SALDO = Sim/Não
FLAG_YES_TEXT = "Sim"
