"""Ajustes de inventário — SD3 doc='INVENT' com proveniência SB7.

Fonte dos fatos classificados: ``InventoryAdjustmentClassification``
(domain). O repositório apenas referencia as expressões — nunca
duplica a regra de natureza/sinal.
"""

from __future__ import annotations

from typing import Any, Optional

from app.domain.ports.supplies.inventory_adjustments_repository_port import (
    InventoryAdjustmentsRepositoryPort,
)
from app.domain.services.supplies.inventory_adjustment_service import (
    InventoryAdjustmentClassification,
    nature_label,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pagination import paginate
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

_NATURE = InventoryAdjustmentClassification.NATURE_SQL_EXPRESSION
_SIGNED_QTY = InventoryAdjustmentClassification.SIGNED_QUANTITY_SQL_EXPRESSION
_SIGNED_VAL = InventoryAdjustmentClassification.SIGNED_VALUE_SQL_EXPRESSION

_BASE_WHERE = """
    SD3.D_E_L_E_T_ = ''
    AND RTRIM(ISNULL(SD3.D3_ESTORNO, '')) <> 'S'
    AND RTRIM(LTRIM(SD3.D3_DOC)) = 'INVENT'
"""

# Proveniência determinística SB7 por filial+produto+armazém+data
# (comprovada em dados; TOP 1 torna o join estável mesmo com doc repetido).
_INVENTORY_DOC_SUBQUERY = """
    (SELECT TOP 1 RTRIM(LTRIM(S.B7_DOC))
       FROM SB7010 S WITH (NOLOCK)
      WHERE S.D_E_L_E_T_ = ''
        AND S.B7_FILIAL = SD3.D3_FILIAL
        AND S.B7_COD = SD3.D3_COD
        AND S.B7_LOCAL = SD3.D3_LOCAL
        AND S.B7_DATA = SD3.D3_EMISSAO
      ORDER BY S.B7_DOC)
"""

_COUNTED_QTY_SUBQUERY = """
    (SELECT SUM(S.B7_QUANT)
       FROM SB7010 S WITH (NOLOCK)
      WHERE S.D_E_L_E_T_ = ''
        AND S.B7_FILIAL = SD3.D3_FILIAL
        AND S.B7_COD = SD3.D3_COD
        AND S.B7_LOCAL = SD3.D3_LOCAL
        AND S.B7_DATA = SD3.D3_EMISSAO)
"""


def _bind_filters(
    qb: QueryBuilder,
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: Optional[str],
    product_code: Optional[str],
    warehouse: Optional[str],
    nature: Optional[str],
) -> None:
    qb.raw(_BASE_WHERE)
    qb.raw("SD3.D3_EMISSAO >= ?", date_start)
    qb.raw("SD3.D3_EMISSAO < ?", date_end_exclusive)
    qb.eq("SD3.D3_FILIAL", branch)
    qb.eq("SD3.D3_COD", product_code)
    qb.eq("SD3.D3_LOCAL", warehouse)
    if nature:
        qb.raw(f"{_NATURE} = ?", nature)


def _summary_select(dim_sql: str) -> str:
    dim = f"{dim_sql} AS bucket," if dim_sql else ""
    return f"""
        SELECT
            {dim}
            COUNT(*) AS adjustment_count,
            SUM(CASE WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'DE0' THEN 1 ELSE 0 END)
                AS shortage_count,
            SUM(CASE WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'RE0' THEN 1 ELSE 0 END)
                AS surplus_count,
            SUM(SD3.D3_QUANT) AS gross_adjustment_quantity,
            SUM({_SIGNED_QTY}) AS net_adjustment_quantity,
            SUM(ABS(SD3.D3_CUSTO1)) AS gross_adjustment_value,
            SUM({_SIGNED_VAL}) AS net_adjustment_value,
            SUM(CASE WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'DE0' THEN SD3.D3_QUANT ELSE 0 END)
                AS shortage_quantity,
            SUM(CASE WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'DE0' THEN ABS(SD3.D3_CUSTO1) ELSE 0 END)
                AS shortage_value,
            SUM(CASE WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'RE0' THEN SD3.D3_QUANT ELSE 0 END)
                AS surplus_quantity,
            SUM(CASE WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'RE0' THEN ABS(SD3.D3_CUSTO1) ELSE 0 END)
                AS surplus_value
        FROM SD3010 SD3 WITH (NOLOCK)
    """


class InventoryAdjustmentsRepository(
    BaseRepository,
    InventoryAdjustmentsRepositoryPort,
):
    def _filter_sql(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: Optional[str],
        product_code: Optional[str],
        warehouse: Optional[str],
        nature: Optional[str],
    ) -> tuple[str, tuple]:
        qb = QueryBuilder()
        _bind_filters(
            qb,
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            product_code=product_code,
            warehouse=warehouse,
            nature=nature,
        )
        return qb.build()

    def fetch_adjustment_items(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: Optional[str],
        product_code: Optional[str],
        warehouse: Optional[str],
        nature: Optional[str],
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        where, params = self._filter_sql(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            product_code=product_code,
            warehouse=warehouse,
            nature=nature,
        )
        paging = paginate(page, page_size)

        count_sql = f"""
        SELECT COUNT(*) AS total
        FROM SD3010 SD3 WITH (NOLOCK)
        WHERE {where}
        """

        data_sql = f"""
        SELECT
            SD3.D3_EMISSAO AS issue_date,
            SD3.D3_FILIAL AS branch,
            SD3.D3_COD AS product_code,
            SB1.B1_DESC AS product_description,
            SB1.B1_UM AS unit,
            SD3.D3_LOCAL AS warehouse,
            RTRIM(LTRIM(SD3.D3_DOC)) AS document,
            SD3.D3_TM AS movement_type,
            SD3.D3_CF AS cf,
            'inventory_adjustment' AS movement_category,
            {_NATURE} AS inventory_adjustment_nature,
            CASE
              WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'RE0' THEN 'inbound'
              WHEN RTRIM(LTRIM(SD3.D3_CF)) = 'DE0' THEN 'outbound'
            END AS movement_direction,
            SD3.D3_QUANT AS quantity,
            {_SIGNED_QTY} AS signed_quantity,
            SD3.D3_CUSTO1 AS movement_value,
            {_SIGNED_VAL} AS signed_value,
            {_INVENTORY_DOC_SUBQUERY} AS inventory_document,
            {_COUNTED_QTY_SUBQUERY} AS counted_quantity
        FROM SD3010 SD3 WITH (NOLOCK)
        LEFT JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = SD3.D3_COD
           AND SB1.D_E_L_E_T_ = ''
        WHERE {where}
        ORDER BY SD3.D3_EMISSAO DESC, SD3.R_E_C_N_O_ DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:
            total_row = repo.execute_one(count_sql, params)
            total = int(total_row["total"]) if total_row else 0
            rows = repo.execute_query(
                data_sql, params + (paging["offset"], paging["page_size"])
            )

        items = []
        for row in rows:
            item_nature = str(row.get("inventory_adjustment_nature") or "")
            items.append(
                {
                    "issue_date": row.get("issue_date"),
                    "branch": row.get("branch"),
                    "product_code": row.get("product_code"),
                    "product_description": row.get("product_description"),
                    "unit": row.get("unit"),
                    "warehouse": row.get("warehouse"),
                    "document": row.get("document"),
                    "movement_category": "inventory_adjustment",
                    "movement_direction": row.get("movement_direction"),
                    "movement_label": "Ajuste de inventário",
                    "inventory_adjustment_nature": item_nature or None,
                    "nature_label": nature_label(item_nature),
                    "quantity": float(row.get("quantity") or 0),
                    "signed_quantity": float(row.get("signed_quantity") or 0),
                    "movement_value": float(row.get("movement_value") or 0),
                    "signed_value": float(row.get("signed_value") or 0),
                    "inventory_document": row.get("inventory_document"),
                    "counted_quantity": (
                        float(row["counted_quantity"])
                        if row.get("counted_quantity") is not None
                        else None
                    ),
                }
            )

        return {"items": items, "total": total}

    def fetch_adjustment_summary(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: Optional[str],
        product_code: Optional[str],
        warehouse: Optional[str],
        nature: Optional[str],
    ) -> dict[str, Any]:
        where, params = self._filter_sql(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            product_code=product_code,
            warehouse=warehouse,
            nature=nature,
        )

        totals_sql = _summary_select("") + f"WHERE {where}"
        month_sql = (
            _summary_select("SUBSTRING(SD3.D3_EMISSAO, 1, 6)")
            + f"WHERE {where} GROUP BY SUBSTRING(SD3.D3_EMISSAO, 1, 6)"
            + " ORDER BY bucket"
        )
        branch_sql = (
            _summary_select("SD3.D3_FILIAL")
            + f"WHERE {where} GROUP BY SD3.D3_FILIAL ORDER BY bucket"
        )
        nature_sql = (
            _summary_select(_NATURE)
            + f"WHERE {where} GROUP BY {_NATURE} ORDER BY bucket"
        )

        with self as repo:
            totals = repo.execute_one(totals_sql, params) or {}
            month_rows = repo.execute_query(month_sql, params)
            branch_rows = repo.execute_query(branch_sql, params)
            nature_rows = repo.execute_query(nature_sql, params)

        def bucket(row: dict[str, Any]) -> dict[str, Any]:
            return {
                "adjustment_count": int(row.get("adjustment_count") or 0),
                "shortage_count": int(row.get("shortage_count") or 0),
                "surplus_count": int(row.get("surplus_count") or 0),
                "gross_quantity": float(row.get("gross_adjustment_quantity") or 0),
                "net_quantity": float(row.get("net_adjustment_quantity") or 0),
                "gross_value": float(row.get("gross_adjustment_value") or 0),
                "net_value": float(row.get("net_adjustment_value") or 0),
                "shortage_quantity": float(row.get("shortage_quantity") or 0),
                "shortage_value": float(row.get("shortage_value") or 0),
                "surplus_quantity": float(row.get("surplus_quantity") or 0),
                "surplus_value": float(row.get("surplus_value") or 0),
            }

        summary = bucket(totals)
        summary.pop("bucket", None)

        by_month = []
        for row in month_rows:
            ym = str(row.get("bucket") or "")
            entry = {"month": f"{ym[:4]}-{ym[4:6]}" if len(ym) == 6 else ym}
            entry.update(bucket(row))
            by_month.append(entry)

        by_branch = []
        for row in branch_rows:
            entry = {"branch": row.get("bucket")}
            entry.update(bucket(row))
            by_branch.append(entry)

        by_nature = []
        for row in nature_rows:
            token = str(row.get("bucket") or "")
            entry = {
                "nature": token or None,
                "nature_label": nature_label(token),
            }
            entry.update(bucket(row))
            by_nature.append(entry)

        return {
            "summary": summary,
            "by_month": by_month,
            "by_branch": by_branch,
            "by_nature": by_nature,
        }
