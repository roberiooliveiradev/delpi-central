from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.production.production_request import ProductionRequest
from app.domain.entities.production.on_time_delivery import OnTimeDelivery


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