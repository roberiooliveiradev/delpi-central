"""Detalhe de matéria-prima com cobertura de compras, empenhos e extrato projetado."""

from __future__ import annotations

from app.application.dto.supplies.safety_stock_request import SafetyStockItemDetailsRequest
from app.domain.ports.supplies.safety_stock_query_repository_port import (
    SafetyStockQueryRepositoryPort,
)
from app.domain.services.supplies.safety_stock_consumption_analysis_service import (
    SafetyStockConsumptionAnalysisService,
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

        period_start, period_end, _period_business_days = (
            SafetyStockConsumptionAnalysisService.resolve_period()
        )
        annual_start, annual_end, year_list = (
            SafetyStockConsumptionAnalysisService.resolve_annual_comparison_period(
                as_of=period_end
            )
        )
        monthly_all = self._repository.fetch_consumption_monthly_series(
            branch=request.branch,
            product_code=request.product_code,
            period_start=annual_start.strftime("%Y%m%d"),
        )
        monthly = SafetyStockConsumptionAnalysisService.filter_monthly_series_for_period(
            monthly_all,
            period_start=period_start,
            period_end=period_end,
        )
        period_consumption = sum(
            float(point.get("consumption_quantity") or 0) for point in monthly
        )
        annual_comparison = SafetyStockConsumptionAnalysisService.build_annual_comparison(
            monthly_all,
            years=year_list,
            period_start=annual_start,
            period_end=annual_end,
        )

        peer_branch_stock = None
        if request.peer_branch:
            peer_detail = self._repository.fetch_item_detail(
                branch=request.peer_branch,
                product_code=request.product_code,
            )
            last_consumption_date = self._repository.fetch_last_consumption_date(
                branch=request.peer_branch,
                product_code=request.product_code,
            )
            if peer_detail is not None:
                peer_branch_stock = {
                    "branch": request.peer_branch,
                    "found": True,
                    "available_stock": float(peer_detail.get("available_stock") or 0),
                    "primary_stock": float(peer_detail.get("primary_stock") or 0),
                    "warehouse_98_stock": float(peer_detail.get("warehouse_98_stock") or 0),
                    "warehouse_99_stock": float(peer_detail.get("warehouse_99_stock") or 0),
                    "safety_stock": float(peer_detail.get("safety_stock") or 0),
                    "last_consumption_date": last_consumption_date,
                }
            else:
                peer_branch_stock = {
                    "branch": request.peer_branch,
                    "found": False,
                    "available_stock": 0.0,
                    "primary_stock": 0.0,
                    "warehouse_98_stock": 0.0,
                    "warehouse_99_stock": 0.0,
                    "safety_stock": 0.0,
                    "last_consumption_date": last_consumption_date,
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
            "peer_branch_stock": peer_branch_stock,
            "purchase_coverage": coverage,
            "open_purchase_orders": build_collection_block(enriched_orders),
            "open_commitments": build_collection_block(
                enriched_commitments,
                summary=open_commitments_summary,
            ),
            "stock_projection": stock_projection,
            "monthly_consumption": {
                "items": monthly,
                "total": len(monthly),
                "period_consumption": period_consumption,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
            },
            "annual_comparison": annual_comparison,
        }
