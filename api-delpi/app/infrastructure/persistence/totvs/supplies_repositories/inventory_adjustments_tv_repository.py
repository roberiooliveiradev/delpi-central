"""Leitura agregada para TV do mesmo universo de ajustes de inventário.

Origem e classificação CANÔNICAS: InventoryAdjustmentsRepository (SD3,
D3_DOC='INVENT', estornos excluídos e CF RE0/DE0). O detalhe é agregado no
SQL, nunca via uma página arbitrária de lançamentos.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from app.infrastructure.persistence.totvs.supplies_repositories.inventory_adjustments_repository import (
    InventoryAdjustmentsRepository,
    _NATURE,
    _RECOGNIZED_NATURE_PREDICATE,
    _SHORTAGE_PREDICATE,
    _SURPLUS_PREDICATE,
)

_CENT = Decimal("0.01")
_QTY = Decimal("0.000001")


def _rounded(value: Any, quantum: Decimal) -> float:
    return float(Decimal(str(value or 0)).quantize(quantum, rounding=ROUND_HALF_UP))


class InventoryAdjustmentsTvRepository(InventoryAdjustmentsRepository):
    """TOP-N divergências da semana, no grão filial+produto+armazém+natureza.

    Nunca mistura furo e sobra de um mesmo produto: compensar ajustes
    contrários apagaria justamente os desvios que o GR Diário quer visualizar.
    """

    def fetch_weekly_product_divergences(
        self,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None,
        warehouse: str | None,
        top_limit: int,
    ) -> dict[str, Any]:
        if top_limit < 1 or top_limit > 50:
            raise ValueError("top_limit deve estar entre 1 e 50.")
        where, params = self._filter_sql(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=branch,
            product_code=None,
            warehouse=warehouse,
            nature=None,
        )

        # Pré-agregação evita que o join de descrição do produto multiplique
        # o valor do movimento. SUM em Decimal antes do arredondamento.
        sql = f"""
        WITH AGG AS (
            SELECT
                RTRIM(SD3.D3_FILIAL) AS branch,
                RTRIM(SD3.D3_COD) AS product_code,
                RTRIM(SD3.D3_LOCAL) AS warehouse,
                {_NATURE} AS nature,
                COUNT(*) AS movement_count,
                SUM(ABS(CAST(SD3.D3_QUANT AS DECIMAL(28, 6))))
                    AS quantity,
                SUM(ABS(CAST(SD3.D3_CUSTO1 AS DECIMAL(28, 6))))
                    AS gross_value,
                SUM(CASE WHEN {_SHORTAGE_PREDICATE}
                         THEN -ABS(CAST(SD3.D3_QUANT AS DECIMAL(28, 6)))
                         WHEN {_SURPLUS_PREDICATE}
                         THEN ABS(CAST(SD3.D3_QUANT AS DECIMAL(28, 6)))
                         ELSE 0 END) AS signed_quantity,
                SUM(CASE WHEN {_SHORTAGE_PREDICATE}
                         THEN -ABS(CAST(SD3.D3_CUSTO1 AS DECIMAL(28, 6)))
                         WHEN {_SURPLUS_PREDICATE}
                         THEN ABS(CAST(SD3.D3_CUSTO1 AS DECIMAL(28, 6)))
                         ELSE 0 END) AS signed_value,
                SUM(CASE WHEN SD3.D3_CUSTO1 IS NULL THEN 1 ELSE 0 END)
                    AS unpriced_movements
            FROM SD3010 SD3 WITH (NOLOCK)
            WHERE {where}
              AND {_RECOGNIZED_NATURE_PREDICATE}
            GROUP BY
                SD3.D3_FILIAL, SD3.D3_COD, SD3.D3_LOCAL, {_NATURE}
        )
        SELECT TOP (?)
            A.branch, A.product_code, A.warehouse, A.nature,
            ISNULL(B1.B1_DESC, '') AS product_description,
            ISNULL(B1.B1_UM, '') AS unit,
            A.movement_count, A.quantity, A.gross_value,
            A.signed_quantity, A.signed_value, A.unpriced_movements,
            COUNT(*) OVER () AS total_groups
        FROM AGG A
        OUTER APPLY (
            SELECT TOP (1) S.B1_DESC, S.B1_UM
            FROM SB1010 S WITH (NOLOCK)
            WHERE S.B1_COD = A.product_code AND S.D_E_L_E_T_ = ''
            ORDER BY CASE WHEN RTRIM(S.B1_FILIAL) = A.branch THEN 0 ELSE 1 END,
                     S.R_E_C_N_O_ DESC
        ) B1
        ORDER BY A.gross_value DESC, A.product_code, A.branch, A.warehouse, A.nature
        """
        with self as repository:
            rows = repository.execute_query(sql, (*params, top_limit))

        items = []
        for row in rows:
            nature = str(row.get("nature") or "").strip()
            items.append(
                {
                    "branch": str(row.get("branch") or "").strip(),
                    "product_code": str(row.get("product_code") or "").strip(),
                    "product_description": str(row.get("product_description") or "").strip(),
                    "unit": str(row.get("unit") or "").strip(),
                    "warehouse": str(row.get("warehouse") or "").strip(),
                    "nature": nature,
                    "nature_label": "Falta" if nature == "shortage" else "Sobra",
                    "movement_count": int(row.get("movement_count") or 0),
                    "quantity": _rounded(row.get("quantity"), _QTY),
                    "signed_quantity": _rounded(row.get("signed_quantity"), _QTY),
                    "value_brl": _rounded(row.get("gross_value"), _CENT),
                    "signed_value_brl": _rounded(row.get("signed_value"), _CENT),
                    "unpriced_movements": int(row.get("unpriced_movements") or 0),
                }
            )

        total_groups = int(rows[0].get("total_groups") or 0) if rows else 0
        return {
            "items": items,
            "total_groups": total_groups,
            "returned": len(items),
            "truncated": total_groups > len(items),
        }
