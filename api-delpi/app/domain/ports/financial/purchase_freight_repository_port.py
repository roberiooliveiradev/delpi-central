from abc import ABC, abstractmethod

from app.application.dto.financial.purchase_freight_links_request import (
    PurchaseFreightLinksRequest,
)


class PurchaseFreightRepositoryPort(ABC):

    @abstractmethod
    def list_purchase_freight_links(
        self,
        request: PurchaseFreightLinksRequest,
        *,
        limit: int,
    ) -> list[dict]:
        """Devolve o fecho de vínculos: até ``limit + 1`` linhas para detectar corte."""
        raise NotImplementedError
