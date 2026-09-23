"""Filtros SQL das movimentações internas SD3 — uma definição para a rota e os testes."""

from __future__ import annotations

from typing import Optional

from app.domain.totvs.protheus_internal_movements import warehouse_transfer_cfs_for_kind
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def bind_internal_movement_filters(
    qb: QueryBuilder,
    *,
    code: str,
    date_start: Optional[str],
    date_end: Optional[str],
    branch: Optional[str],
    location: Optional[str],
    tm: Optional[str],
    op: Optional[str],
    kind: Optional[str] = None,
) -> None:
    qb.raw("SD3.D_E_L_E_T_ = ''")
    qb.raw("RTRIM(ISNULL(SD3.D3_ESTORNO, '')) <> 'S'")
    qb.eq("SD3.D3_COD", code)
    qb.date_range("SD3.D3_EMISSAO", date_start, date_end)
    qb.eq("SD3.D3_FILIAL", branch)
    qb.eq("SD3.D3_LOCAL", location)
    qb.eq("SD3.D3_TM", tm)
    qb.eq("SD3.D3_OP", op)
    cfs = warehouse_transfer_cfs_for_kind(kind)
    if cfs:
        qb.in_list("RTRIM(LTRIM(SD3.D3_CF))", cfs)
