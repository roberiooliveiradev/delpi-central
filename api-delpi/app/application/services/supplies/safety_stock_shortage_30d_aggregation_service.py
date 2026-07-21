"""Agregação batch — rupturas projetadas na janela (Delpi Reports)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.domain.services.reports.safety_stock_shortage_30d_rules import (
    DEFAULT_HORIZON_DAYS,
    VALID_BRANCHES,
    balance_at_first_shortage,
    observation_from_summary,
    shortage_date_in_horizon,
)
from app.domain.services.supplies.safety_stock_purchase_coverage_service import (
    enrich_open_purchase_orders,
)
from app.domain.services.supplies.safety_stock_stock_projection_service import (
    build_stock_projection,
    enrich_open_commitments,
)


def _group_by_product(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        code = str(row.get("product_code") or "").strip()
        if code:
            grouped[code].append(row)
    return grouped


class SafetyStockShortage30dAggregationService:
    """3 SQL/filial + projeção in-process (sem N+1 de details)."""

    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._repository = repository

    def collect_rows(
        self,
        *,
        branch: str,
        horizon_days: int = DEFAULT_HORIZON_DAYS,
        include_blocked: bool = False,
        product_group: str | None = None,
        unit: str | None = None,
        search: str | None = None,
        include_without_safety_stock: bool = True,
        as_of_date: date | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        branch_code = str(branch or "").strip()
        if branch_code not in VALID_BRANCHES:
            raise ValueError("branch deve ser 01 ou 02.")
        horizon = int(horizon_days)
        if horizon < 1 or horizon > 365:
            raise ValueError("horizonDays deve estar entre 1 e 365.")

        as_of = as_of_date or date.today()
        materials = self._repository.fetch_materials_for_projection_batch(
            branch=branch_code,
            include_blocked=include_blocked,
            product_group=product_group,
            unit=unit,
            search=search,
            include_without_safety_stock=include_without_safety_stock,
        )
        orders_by_code = _group_by_product(
            self._repository.fetch_open_purchase_orders_for_branch(branch=branch_code)
        )
        commitments_by_code = _group_by_product(
            self._repository.fetch_open_commitments_for_branch(branch=branch_code)
        )

        rows: list[dict[str, Any]] = []
        for material in materials:
            code = str(material.get("product_code") or "").strip()
            if not code:
                continue

            unit_kwargs = {
                "primary_unit": material.get("unit"),
                "secondary_unit": material.get("secondary_unit"),
                "conversion_factor": material.get("conversion_factor"),
                "conversion_type": material.get("conversion_type"),
            }
            enriched_orders, _coverage_totals = enrich_open_purchase_orders(
                orders=orders_by_code.get(code, []),
                **unit_kwargs,
            )
            enriched_commitments, commitment_totals = enrich_open_commitments(
                commitments=commitments_by_code.get(code, []),
                **unit_kwargs,
            )
            projection = build_stock_projection(
                available_stock=float(material.get("available_stock") or 0),
                safety_stock=float(material.get("safety_stock") or 0),
                enriched_orders=enriched_orders,
                enriched_commitments=enriched_commitments,
                commitment_totals=commitment_totals,
                as_of_date=as_of,
            )
            summary = projection.get("summary") or {}
            first_shortage = summary.get("first_shortage_date")
            if not shortage_date_in_horizon(
                first_shortage if isinstance(first_shortage, str) else None,
                as_of=as_of,
                horizon_days=horizon,
            ):
                continue

            rows.append(
                {
                    "product_code": code,
                    "product_description": str(
                        material.get("product_description") or ""
                    ).strip(),
                    "branch": branch_code,
                    "available_stock": float(material.get("available_stock") or 0),
                    "first_shortage_date": first_shortage,
                    "shortage_balance": balance_at_first_shortage(projection),
                    "observation": observation_from_summary(summary),
                }
            )

        rows.sort(key=lambda item: (item["first_shortage_date"], item["product_code"]))
        meta = {
            "branch": branch_code,
            "horizonDays": horizon,
            "asOfDate": as_of.isoformat(),
            "materialsScanned": len(materials),
            "shortageCount": len(rows),
        }
        return rows, meta
