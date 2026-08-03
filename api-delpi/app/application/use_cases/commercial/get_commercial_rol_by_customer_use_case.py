"""Use case — ranking de ROL por cliente."""

from __future__ import annotations

from app.application.dto.commercial.get_rol_by_customer_request import (
    GetRolByCustomerRequest,
)
from app.domain.entities.commercial.rol_by_customer import RolByCustomerResult
from app.domain.ports.commercial.commercial_rol_by_customer_repository_port import (
    CommercialRolByCustomerRepositoryPort,
)


class GetCommercialRolByCustomerUseCase:
    def __init__(
        self,
        repository: CommercialRolByCustomerRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(self, request: GetRolByCustomerRequest) -> RolByCustomerResult:
        request.validate()
        return self._repository.get_rol_by_customer(request)
