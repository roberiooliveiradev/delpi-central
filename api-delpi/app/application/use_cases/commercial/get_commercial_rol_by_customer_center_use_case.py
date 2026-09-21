"""Use case — ROL comercial classificado pelo centro atual do cliente."""

from __future__ import annotations

from app.application.dto.commercial.get_rol_by_customer_center_request import (
    GetRolByCustomerCenterRequest,
)
from app.domain.entities.commercial.rol_by_customer_center import (
    RolByCustomerCenterResult,
)
from app.domain.ports.commercial.commercial_rol_by_customer_center_repository_port import (
    CommercialRolByCustomerCenterRepositoryPort,
)


class GetCommercialRolByCustomerCenterUseCase:
    def __init__(
        self,
        repository: CommercialRolByCustomerCenterRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        request: GetRolByCustomerCenterRequest,
    ) -> RolByCustomerCenterResult:
        request.validate()
        return self._repository.get_rol_by_customer_center(request)
