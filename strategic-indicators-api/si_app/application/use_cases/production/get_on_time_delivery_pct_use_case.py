from __future__ import annotations

from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.ports.production.on_time_delivery_repository_port import (
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

            return {
                "on_time_delivery_pct": (
                    round(float(on_time_delivery.on_time_delivery_pct), 2)
                    if on_time_delivery
                    and on_time_delivery.on_time_delivery_pct is not None
                    else None
                )
            }

        rows = self._on_time_delivery_repository.list_on_time_delivery_by_branch(
            production_request
        )

        values = []
        for row in rows or []:
            value = row.get("on_time_delivery_pct")
            try:
                if value is not None:
                    values.append(float(value))
            except (TypeError, ValueError):
                continue

        return {
            "on_time_delivery_pct": (
                round(sum(values) / len(values), 2)
                if values
                else None
            )
        }