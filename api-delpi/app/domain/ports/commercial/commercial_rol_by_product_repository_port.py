"""Port — ROL comercial por produto / família."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.commercial.get_rol_by_product_request import (
    GetRolByProductRequest,
)
from app.domain.entities.commercial.rol_by_product import RolByProductResult


class CommercialRolByProductRepositoryPort(ABC):
    @abstractmethod
    def get_rol_by_product(
        self,
        request: GetRolByProductRequest,
    ) -> RolByProductResult:
        raise NotImplementedError
