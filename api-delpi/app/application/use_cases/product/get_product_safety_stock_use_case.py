"""Consulta geral de estoque de segurança (SBZ010.BZ_ESTSEG) de um produto.

Diferente da análise de Suprimentos (MP-only, consumo, cobertura de compras),
este read é cadastral: aplica a qualquer ``B1_TIPO`` e não executa cálculos
especializados. Distingue valor zero, ausência de registro SBZ e produto
inexistente.
"""

from __future__ import annotations

from app.application.dto.product.get_product_safety_stock_request import (
    GetProductSafetyStockRequest,
)
from app.domain.ports.product.product_safety_stock_repository_port import (
    ProductSafetyStockRepositoryPort,
)
from app.domain.totvs.protheus_branches import (
    PROTHEUS_BRANCH_CODES,
    optional_concrete_branch,
)

SAFETY_STOCK_DATA_REGISTERED = "registered"
SAFETY_STOCK_DATA_MISSING = "missing"


class ProductTypeMismatchError(Exception):
    """Produto existe, mas não pertence ao ``product_type`` filtrado."""


class GetProductSafetyStockUseCase:
    def __init__(self, repository: ProductSafetyStockRepositoryPort) -> None:
        self._repository = repository

    def execute(self, request: GetProductSafetyStockRequest) -> dict | None:
        concrete = optional_concrete_branch(request.branch)
        scope = (concrete,) if concrete else PROTHEUS_BRANCH_CODES

        record = self._repository.fetch_safety_stock(request.code, scope)
        if record is None:
            return None

        if (
            request.product_type is not None
            and record["product_type"] != request.product_type
        ):
            raise ProductTypeMismatchError(
                f"Produto {request.code} é do tipo {record['product_type']}, "
                f"não {request.product_type}."
            )

        by_branch = record.get("safety_stock_by_branch") or {}
        branches = [
            {
                "branch": branch,
                "safety_stock": by_branch.get(branch),
                "safety_stock_data_state": (
                    SAFETY_STOCK_DATA_REGISTERED
                    if branch in by_branch
                    else SAFETY_STOCK_DATA_MISSING
                ),
            }
            for branch in scope
        ]

        return {
            "product_code": record["product_code"],
            "description": record["description"],
            "product_type": record["product_type"],
            "unit": record["unit"],
            "blocked": record["blocked"],
            "branches": branches,
        }
