from abc import ABC, abstractmethod
from si_app.application.dto.supplies.get_inventory_turnover_request import (
    GetInventoryTurnoverRequest,
)


class InventoryTurnoverQueryRepositoryPort(ABC):

    @abstractmethod
    def get_cpv_context(self, request: GetInventoryTurnoverRequest) -> dict:
        raise NotImplementedError