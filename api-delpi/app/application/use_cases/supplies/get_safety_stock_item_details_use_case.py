"""Detalhe de matéria-prima com cobertura de compras, empenhos e extrato projetado."""

from __future__ import annotations

from app.application.dto.supplies.safety_stock_request import SafetyStockItemDetailsRequest
from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.domain.services.supplies.safety_stock_purchase_coverage_service import (
    build_purchase_coverage,
    enrich_open_purchase_orders,
)
from app.domain.services.supplies.safety_stock_stock_projection_service import (
    build_collection_block,
    build_stock_projection,
    enrich_open_commitments,
)


class GetSafetyStockItemDetailsUseCase:
    def __init__(self, repository: SafetyStockQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: SafetyStockItemDetailsRequest) -> dict | None:
        detail = self._repository.fetch_item_detail(
            branch=request.branch,
            product_code=request.product_code,
        )
        if detail is None:
            return None

        unit_kwargs = {
            "primary_unit": detail.get("unit"),
            "secondary_unit": detail.get("secondary_unit"),
            "conversion_factor": detail.get("conversion_factor"),
            "conversion_type": detail.get("conversion_type"),
        }

        orders = self._repository.fetch_open_purchase_orders(
            branch=request.branch,
            product_code=request.product_code,
        )
        enriched_orders, coverage_totals = enrich_open_purchase_orders(
            orders=orders,
            **unit_kwargs,
        )
        coverage = build_purchase_coverage(
            deficit_quantity=float(detail.get("deficit_quantity") or 0),
            enriched_orders=enriched_orders,
            coverage_totals=coverage_totals,
        )

        commitments = self._repository.fetch_open_commitments(
            branch=request.branch,
            product_code=request.product_code,
        )
        enriched_commitments, commitment_totals = enrich_open_commitments(
            commitments=commitments,
            **unit_kwargs,
        )

        stock_projection = build_stock_projection(
            available_stock=float(detail.get("available_stock") or 0),
            safety_stock=float(detail.get("safety_stock") or 0),
            enriched_orders=enriched_orders,
            enriched_commitments=enriched_commitments,
            commitment_totals=commitment_totals,
        )

        open_commitments_summary = {
            "eligible_open_quantity": commitment_totals.get("eligible_open_quantity"),
            "next_commitment_date": commitment_totals.get("next_commitment_date"),
            "incompatible_unit_commitment_count": commitment_totals.get(
                "incompatible_unit_commitment_count"
            ),
            "eligible_warehouses": commitment_totals.get("eligible_warehouses"),
            "warnings": commitment_totals.get("warnings") or [],
        }

        return {
            "product": {
                "product_code": detail["product_code"],
                "product_description": detail["product_description"],
                "product_type": detail["product_type"],
                "unit": detail["unit"],
                "secondary_unit": detail.get("secondary_unit") or "",
                "conversion_factor": detail.get("conversion_factor"),
                "conversion_type": detail.get("conversion_type") or "",
                "product_group": detail["product_group"],
                "branch": detail["branch"],
                "blocked": detail["blocked"],
                "status": detail["status"],
            },
            "stock": {
                "safety_stock": detail["safety_stock"],
                "available_stock": detail["available_stock"],
                "primary_stock": detail["primary_stock"],
                "warehouse_50_stock": detail["warehouse_50_stock"],
                "warehouse_98_stock": detail["warehouse_98_stock"],
                "warehouse_99_stock": detail["warehouse_99_stock"],
                "work_in_process_stock": detail["work_in_process_stock"],
                "work_in_process_committed": detail["work_in_process_committed"],
                "work_in_process_available": detail["work_in_process_available"],
                "deficit_quantity": detail["deficit_quantity"],
            },
            "purchase_coverage": coverage,
            "open_purchase_orders": build_collection_block(enriched_orders),
            "open_commitments": build_collection_block(
                enriched_commitments,
                summary=open_commitments_summary,
            ),
            "stock_projection": stock_projection,
        }
