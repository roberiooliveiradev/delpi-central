"""Port — ROL comercial classificado pelo centro do cliente (SA7/ZC0)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.commercial.get_rol_by_customer_center_request import (
    GetRolByCustomerCenterRequest,
)
from app.domain.entities.commercial.rol_by_customer_center import (
    RolByCustomerCenterResult,
)


class CommercialRolByCustomerCenterRepositoryPort(ABC):
    @abstractmethod
    def get_rol_by_customer_center(
        self,
        request: GetRolByCustomerCenterRequest,
    ) -> RolByCustomerCenterResult:
        raise NotImplementedError
