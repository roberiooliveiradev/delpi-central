from __future__ import annotations

from abc import ABC, abstractmethod

from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.entities.production.on_time_delivery import OnTimeDelivery


class OnTimeDeliveryRepositoryPort(ABC):
    @abstractmethod
    def get_on_time_delivery(
        self,
        request: ProductionRequest,
    ) -> OnTimeDelivery:
        raise NotImplementedError

    @abstractmethod
    def list_on_time_delivery_by_branch(
        self,
        request: ProductionRequest,
    ) -> list[dict]:
        raise NotImplementedError