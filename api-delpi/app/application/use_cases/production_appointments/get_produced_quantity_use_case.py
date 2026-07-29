"""Use case canônico — quantidade produzida (SUM H6_QTDPROD, inspeção final + OP mãe)."""

from __future__ import annotations

from app.application.dto.ppm.produced_quantity_request import ProducedQuantityRequest
from app.application.dto.production_appointments.produced_quantity_query_request import (
    ProducedQuantityQueryRequest,
)
from app.domain.entities.ppm.produced_quantity import (
    ProducedQuantityByProduct,
    ProducedQuantityItem,
    ProducedQuantityReport,
)
from app.domain.ports.production_appointments.production_appointments_repository_port import (
    ProductionAppointmentsRepositoryPort,
)
from app.domain.production.production_appointments.production_appointments_scope import (
    DEFAULT_PRODUCED_PRODUCT_TYPES,
    SHIPPING_PRODUCED_PRODUCT_TYPES,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)


class GetProducedQuantityUseCase:
    """Único ponto de regra para total produzido consumido por PPM, shipping e apontamentos."""

    def __init__(self, repository: ProductionAppointmentsRepositoryPort):
        self._repository = repository

    def execute(
        self,
        request: ProducedQuantityQueryRequest | ProducedQuantityRequest,
    ) -> ProducedQuantityReport:
        query = self._normalize_request(request)
        date_start, date_end_exclusive = ProtheusDateRangeService.resolve_closed_open_period(
            date_start=query.date_start,
            date_end=query.date_end,
        )
        rows = self._repository.list_produced_quantity(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=query.branch,
            products=list(query.products) or None,
            product_types=list(query.product_types),
        )
        items = [
            ProducedQuantityItem(
                branch=str(row.get("branch") or "").strip(),
                product_code=str(row.get("product_code") or "").strip(),
                product_type=str(row.get("product_type") or "").strip(),
                description=str(row.get("description") or "").strip(),
                unit=str(row.get("unit") or "").strip(),
                produced_milheiro=float(row.get("produced_milheiro") or 0),
                produced_un=float(row.get("produced_un") or 0),
                orders_count=int(row.get("orders_count") or 0),
            )
            for row in rows
        ]
        by_product = self._aggregate_by_product(items)
        total_milheiro = sum(item.produced_milheiro for item in items)
        total_un = sum(item.produced_un for item in items)
        return ProducedQuantityReport(
            branch=query.branch,
            start_date=query.date_start,
            end_date=query.date_end,
            products=list(query.products),
            items=items,
            total_produced_milheiro=total_milheiro,
            total_produced_un=total_un,
            by_product=by_product,
        )

    def get_totals(
        self,
        request: ProducedQuantityQueryRequest,
    ) -> dict:
        date_start, date_end_exclusive = ProtheusDateRangeService.resolve_closed_open_period(
            date_start=request.date_start,
            date_end=request.date_end,
        )
        totals = self._repository.get_produced_totals(
            date_start=date_start,
            date_end_exclusive=date_end_exclusive,
            branch=request.branch,
            products=list(request.products) or None,
            product_types=list(request.product_types),
        )
        return {
            "qty_produced_milheiro": float(totals.get("qty_produced_milheiro") or 0),
            "qty_produced_un": float(totals.get("qty_produced_un") or 0),
            "qty_lost_milheiro": float(totals.get("qty_lost_milheiro") or 0),
            "qty_lost_un": float(totals.get("qty_lost_un") or 0),
            "appointment_count": int(totals.get("appointment_count") or 0),
            "orders_count": int(totals.get("orders_count") or 0),
            "branch": request.branch,
            "start_date": request.date_start,
            "end_date": request.date_end,
            "product_types": list(request.product_types),
            "products": list(request.products),
            "inspection_final": True,
            "mother_op": True,
        }

    def list_detail(
        self,
        *,
        date_start: str,
        date_end: str,
        branch: str | None = None,
        product: str | None = None,
        product_types: list[str] | None = None,
    ) -> list[dict]:
        tipos = product_types
        if tipos is None:
            tipos = sorted(SHIPPING_PRODUCED_PRODUCT_TYPES)
        query = ProducedQuantityQueryRequest.create(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            products=[product] if product else None,
            product_types=tipos,
        )
        date_start_p, date_end_exclusive = ProtheusDateRangeService.resolve_closed_open_period(
            date_start=query.date_start,
            date_end=query.date_end,
        )
        rows = self._repository.list_produced_detail(
            date_start=date_start_p,
            date_end_exclusive=date_end_exclusive,
            branch=query.branch,
            products=list(query.products) or None,
            product_types=list(query.product_types),
        )
        return [
            {
                **row,
                "shipped_quantity": str(row.get("shipped_quantity") or 0),
                "inspection_loss_quantity": str(row.get("inspection_loss_quantity") or 0),
            }
            for row in rows
        ]

    @staticmethod
    def _normalize_request(
        request: ProducedQuantityQueryRequest | ProducedQuantityRequest,
    ) -> ProducedQuantityQueryRequest:
        if isinstance(request, ProducedQuantityQueryRequest):
            return request
        return ProducedQuantityQueryRequest.create(
            date_start=request.date_start,
            date_end=request.date_end,
            branch=request.branch,
            products=request.products,
            product_types=sorted(DEFAULT_PRODUCED_PRODUCT_TYPES),
            require_products=True,
        )

    @staticmethod
    def _aggregate_by_product(
        items: list[ProducedQuantityItem],
    ) -> list[ProducedQuantityByProduct]:
        by_product_map: dict[str, ProducedQuantityByProduct] = {}
        for item in items:
            existing = by_product_map.get(item.product_code)
            if existing is None:
                by_product_map[item.product_code] = ProducedQuantityByProduct(
                    product_code=item.product_code,
                    product_type=item.product_type,
                    description=item.description,
                    unit=item.unit,
                    produced_milheiro=item.produced_milheiro,
                    produced_un=item.produced_un,
                    orders_count=item.orders_count,
                    branches=[item.branch] if item.branch else [],
                )
                continue
            existing.produced_milheiro += item.produced_milheiro
            existing.produced_un += item.produced_un
            existing.orders_count += item.orders_count
            if item.branch and item.branch not in existing.branches:
                existing.branches.append(item.branch)
        return sorted(by_product_map.values(), key=lambda row: row.product_code)
