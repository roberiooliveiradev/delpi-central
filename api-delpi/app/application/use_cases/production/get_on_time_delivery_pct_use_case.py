from app.application.dto.production.production_request import ProductionRequest
from app.domain.ports.production.on_time_delivery_repository_port import OnTimeDeliveryRepositoryPort


class GetOnTimeDeliveryPctUseCase:
    def __init__(
        self,
        on_time_delivery_repository: OnTimeDeliveryRepositoryPort
    ):
        self._on_time_delivery_repository = on_time_delivery_repository

    def execute(self, production_request: ProductionRequest) -> dict:
        on_time_delivery = self._on_time_delivery_repository.get_on_time_delivery(production_request)

        return {
            "on_time_delivery_pct": (
                on_time_delivery.on_time_delivery_pct
                if on_time_delivery and on_time_delivery.on_time_delivery_pct is not None
                else None
            )
        }