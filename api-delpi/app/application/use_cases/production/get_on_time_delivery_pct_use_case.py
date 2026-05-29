from __future__ import annotations

from app.application.dto.production.production_request import ProductionRequest
from app.application.shared.numeric_parsing import to_optional_float
from app.domain.ports.production.on_time_delivery_repository_port import (
    OnTimeDeliveryRepositoryPort,
)


class GetOnTimeDeliveryPctUseCase:
    def __init__(
        self,
        on_time_delivery_repository: OnTimeDeliveryRepositoryPort,
    ):
        self._on_time_delivery_repository = on_time_delivery_repository

    def execute(self, production_request: ProductionRequest) -> dict:
        if production_request.branch:
            on_time_delivery = self._on_time_delivery_repository.get_on_time_delivery(
                production_request
            )

            parsed = to_optional_float(
                on_time_delivery.on_time_delivery_pct if on_time_delivery else None
            )

            return {
                "on_time_delivery_pct": (
                    round(parsed, 2) if parsed is not None else None
                )
            }

        rows = self._on_time_delivery_repository.list_on_time_delivery_by_branch(
            production_request
        )

        values = []
        for row in rows or []:
            parsed = to_optional_float(row.get("on_time_delivery_pct"))
            if parsed is not None:
                values.append(parsed)

        return {
            "on_time_delivery_pct": (
                round(sum(values) / len(values), 2)
                if values
                else None
            )
        }