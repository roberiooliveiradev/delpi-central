"""Use case — ROL por produto / família de produtos."""

from __future__ import annotations

from app.application.dto.commercial.get_rol_by_product_request import (
    GetRolByProductRequest,
)
from app.domain.entities.commercial.rol_by_product import RolByProductResult
from app.domain.ports.commercial.commercial_rol_by_product_repository_port import (
    CommercialRolByProductRepositoryPort,
)


class GetCommercialRolByProductUseCase:
    def __init__(
        self,
        repository: CommercialRolByProductRepositoryPort,
    ) -> None:
        self._repository = repository

    def execute(self, request: GetRolByProductRequest) -> RolByProductResult:
        request.validate()
        return self._repository.get_rol_by_product(request)
