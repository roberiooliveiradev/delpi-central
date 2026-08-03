"""Port — ranking de ROL por cliente."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.commercial.get_rol_by_customer_request import (
    GetRolByCustomerRequest,
)
from app.domain.entities.commercial.rol_by_customer import RolByCustomerResult


class CommercialRolByCustomerRepositoryPort(ABC):
    @abstractmethod
    def get_rol_by_customer(
        self,
        request: GetRolByCustomerRequest,
    ) -> RolByCustomerResult:
        raise NotImplementedError
