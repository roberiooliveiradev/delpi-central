"""Use case canônico — quantidade devolvida (SUM QI2_QTDDEV, numerador PPM)."""

from __future__ import annotations

from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.application.dto.ppm.returned_quantity_query_request import (
    ReturnedQuantityQueryRequest,
)
from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort


class GetReturnedQuantityUseCase:
    """Único ponto de regra para total devolvido consumido por PPM e rota canônica."""

    def __init__(self, repository: PpmQueryRepositoryPort):
        self._repository = repository

    def get_totals(
        self,
        request: ReturnedQuantityQueryRequest | PpmSummaryRequest,
    ) -> dict:
        query = self._normalize_request(request)
        totals = self._repository.get_returned_totals(
            ppm_type=query.type,
            branch=query.branch,
            date_start=query.date_start,
            date_end=query.date_end,
            product_prefix=query.product_prefix,
        )
        return {
            "qty_returned_un": float(totals.get("qty_returned_un") or 0),
            "nc_count": int(totals.get("nc_count") or 0),
            "type": query.type,
            "branch": query.branch,
            "start_date": query.date_start,
            "end_date": query.date_end,
            "product_prefix": query.product_prefix,
        }

    @staticmethod
    def _normalize_request(
        request: ReturnedQuantityQueryRequest | PpmSummaryRequest,
    ) -> ReturnedQuantityQueryRequest:
        if isinstance(request, ReturnedQuantityQueryRequest):
            return request
        return ReturnedQuantityQueryRequest.create(
            ppm_type=request.type,
            date_start=request.date_start,
            date_end=request.date_end,
            branch=request.branch,
            product_prefix=request.product_prefix,
        )
