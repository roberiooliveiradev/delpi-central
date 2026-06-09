from app.application.dto.product.product_cost_impact_request import ProductCostImpactRequest
from app.application.services.product.product_cost_impact_service import build_cost_impact_simulation
from app.domain.ports.product.product_cost_impact_repository_port import (
    ProductCostImpactRepositoryPort,
)


class GetProductCostImpactSimulationUseCase:

    DEFAULT_MAX_DEPTH = 50

    def __init__(self, repository: ProductCostImpactRepositoryPort):
        self._repository = repository

    def execute(self, request: ProductCostImpactRequest) -> dict:
        if request.adjustment_percent < -100:
            raise ValueError("adjustment_percent não pode ser menor que -100.")

        max_depth = request.max_depth or self.DEFAULT_MAX_DEPTH
        header = self._repository.fetch_product_cost_header(request.code)

        if header and header.get("product_type") not in (None, "", "PA"):
            raise ValueError(
                "Simulador de impacto de custos disponível apenas para produto acabado (PA)."
            )

        items = self._repository.fetch_raw_material_cost_items(request.code, max_depth)

        return build_cost_impact_simulation(
            product=header,
            items=items,
            price_source=request.price_source,
            adjustment_percent=request.adjustment_percent,
            top_n=request.top_n,
        )
