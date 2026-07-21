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
    build_next_purchase_text,
    build_sample_observation,
    build_third_party_observation,
    compose_observation_parts,
    finished_product_code_at_first_shortage,
    has_open_projection_commitment,
    is_sample_finished_product,
    should_annotate_third_party_observation,
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

        third_party_codes = [
            str(material.get("product_code") or "").strip()
            for material in materials
            if should_annotate_third_party_observation(
                branch=branch_code,
                material_type=material.get("material_type"),
            )
            and str(material.get("product_code") or "").strip()
        ]
        third_party_names: dict[str, str] = {}
        if third_party_codes:
            third_party_names = self._repository.fetch_last_inbound_party_names(
                branch=branch_code,
                product_codes=third_party_codes,
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
            # Sem empenho elegível: saldo negativo residual não é ruptura operacional.
            if not has_open_projection_commitment(enriched_commitments):
                continue
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

            product_unit = str(material.get("unit") or "").strip()
            observation_parts: list[str] = []
            if should_annotate_third_party_observation(
                branch=branch_code,
                material_type=material.get("material_type"),
            ):
                observation_parts.append(
                    build_third_party_observation(third_party_names.get(code))
                )
            finished_at_shortage = finished_product_code_at_first_shortage(projection)
            if is_sample_finished_product(finished_at_shortage):
                observation_parts.append(
                    build_sample_observation(finished_at_shortage)
                )
            observation = compose_observation_parts(*observation_parts)
            rows.append(
                {
                    "product_code": code,
                    "product_description": str(
                        material.get("product_description") or ""
                    ).strip(),
                    "branch": branch_code,
                    "unit": product_unit,
                    "available_stock": float(material.get("available_stock") or 0),
                    "first_shortage_date": first_shortage,
                    "shortage_balance": balance_at_first_shortage(projection),
                    "next_purchase": build_next_purchase_text(
                        enriched_orders=enriched_orders,
                        product_unit=product_unit,
                        summary=summary,
                    ),
                    "observation": observation,
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
