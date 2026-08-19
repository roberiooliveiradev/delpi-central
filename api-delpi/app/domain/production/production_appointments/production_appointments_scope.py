"""Escopo e constantes — Apontamento de Produção (SH6 por CT).

Quantidade real produzida: ``SH6010.H6_QTDPROD``.
Denominador canônico (PPM / shipping / produced-totals): inspeção final + OP mãe.

KPI/série ``qty_produced`` do painel (sem filtro de CT): última operação do
roteiro (``SG2``) do produto acabado (``B1_TIPO = PA``) — apontamento que gera
entrada em estoque. Ranking por CT permanece com todos os centros.
"""

from __future__ import annotations

from app.domain.totvs.protheus_product_types import PRODUCT_TYPE_FINISHED_GOOD

# Mesma convenção de nome SHB do domínio qualidade; sem acoplar rotas PPM.
CT_INSPECAO_NOME_SQL_LIKE = "%INSPE%FINAL%"

PRODUCED_QTY_SCOPE_PA_LAST_ROUTING_OPERATION = "pa_last_routing_operation"
PRODUCED_QTY_SCOPE_WORK_CENTER = "work_center"

# Tipo SB1 cuja última operação de roteiro gera PR0 (entrada de estoque).
PA_STOCK_ENTRY_PRODUCT_TYPE = PRODUCT_TYPE_FINISHED_GOOD


def produced_qty_scope(*, work_center: str | None = None) -> str:
    """Escopo do KPI ``qty_produced`` no summary/série agregada."""
    if str(work_center or "").strip():
        return PRODUCED_QTY_SCOPE_WORK_CENTER
    return PRODUCED_QTY_SCOPE_PA_LAST_ROUTING_OPERATION


def restrict_produced_qty_to_pa_last_routing_operation(
    *,
    work_center: str | None = None,
    group_by: str | None = None,
) -> bool:
    """True quando a soma de produzida deve restringir à última operação do PA.

    Recorte por um CT (detalhe/filtro) e série ``day_work_center`` mantêm o
    volume do próprio centro — senão o detalhe de CT intermediário zeraria.
    """
    if group_by == "day_work_center":
        return False
    return (
        produced_qty_scope(work_center=work_center)
        == PRODUCED_QTY_SCOPE_PA_LAST_ROUTING_OPERATION
    )


# Tipos SB1 no total produzido do PPM (PA + PI). Shipping usa só PA.
DEFAULT_PRODUCED_PRODUCT_TYPES: frozenset[str] = frozenset({"PA", "PI"})
SHIPPING_PRODUCED_PRODUCT_TYPES: frozenset[str] = frozenset({"PA"})

VALID_BRANCHES: frozenset[str] = frozenset({"01", "02"})

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
MAX_BY_OP_LIMIT = 200
DEFAULT_BY_OP_LIMIT = 50

SERIES_GROUP_BY_OPTIONS: frozenset[str] = frozenset({"day", "day_work_center"})

# Granularidade temporal (série de apontamentos e série de OPs finalizadas).
TEMPORAL_GRANULARITY_OPTIONS: frozenset[str] = frozenset({"day", "month"})
FINISHED_OPS_GRANULARITY_OPTIONS = TEMPORAL_GRANULARITY_OPTIONS
SERIES_GRANULARITY_OPTIONS = TEMPORAL_GRANULARITY_OPTIONS

# OP mãe Protheus — sequência 001 (mesmo critério OTD / C2_SEQUEN).
MOTHER_OP_SUFFIX = "001"
