"""Filtros SQL das movimentações internas SD3 — uma definição para a rota e os testes."""

from __future__ import annotations

from typing import Optional

from app.domain.totvs.protheus_internal_movements import movement_kind_filters
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
    spec = movement_kind_filters(kind)
    if spec:
        cfs = spec.get("cf_in")
        if cfs:
            qb.in_list("RTRIM(LTRIM(SD3.D3_CF))", cfs)
        cf_eq = spec.get("cf_eq")
        if cf_eq:
            qb.raw("RTRIM(LTRIM(SD3.D3_CF)) = ?", cf_eq)
        doc_eq = spec.get("doc_eq")
        if doc_eq:
            qb.raw("RTRIM(LTRIM(SD3.D3_DOC)) = ?", doc_eq)
        doc_ne = spec.get("doc_ne")
        if doc_ne:
            qb.raw("RTRIM(LTRIM(SD3.D3_DOC)) <> ?", doc_ne)
        tm_eq = spec.get("tm_eq")
        if tm_eq:
            qb.raw("RTRIM(LTRIM(SD3.D3_TM)) = ?", tm_eq)
        if spec.get("requires_production_order"):
            qb.raw("RTRIM(LTRIM(SD3.D3_OP)) <> ''")
