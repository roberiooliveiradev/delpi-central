from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.ports.production.production_cost_repository_port import ProductionCostRepositoryPort
from si_app.domain.ports.financial.financial_query_repository_port import FinancialQueryRepositoryPort
from si_app.application.dto.financial.get_rol_request import GetRolRequest

class GetProductionCostPctUseCase:
    def __init__(
        self,
        production_cost_repository: ProductionCostRepositoryPort,
        financial_query_repository: FinancialQueryRepositoryPort
    ):
        self._production_cost_repository = production_cost_repository
        self._financial_query_repository = financial_query_repository

    def execute(self, production_request: ProductionRequest, rol_request: GetRolRequest) -> dict:
        production_cost = self._production_cost_repository.get_production_cost(production_request)
        average_production_cost = (
            sum(pc.cost for pc in production_cost if pc.cost is not None) / len(production_cost)
            if production_cost else 0
        )

        rol_object = self._financial_query_repository.get_rol(rol_request)
        rol = rol_object.get("rol_with_ipi", 0)

        production_cost_pct = (average_production_cost / rol) * 100 if rol else None

        return {"production_cost_pct": production_cost_pct}