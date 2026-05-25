from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.ports.production.direct_labor_repository_port import DirectLaborRepositoryPort
from si_app.domain.ports.financial.financial_query_repository_port import FinancialQueryRepositoryPort
from si_app.application.dto.financial.get_rol_request import GetRolRequest


class GetDirectLaborCostPctUseCase:
    def __init__(
        self,
        direct_labor_repository: DirectLaborRepositoryPort,
        financial_query_repository: FinancialQueryRepositoryPort,
    ):
        self._direct_labor_repository = direct_labor_repository
        self._financial_query_repository = financial_query_repository

    def execute(self, production_request: ProductionRequest, rol_request: GetRolRequest) -> dict:
        direct_labor_costs = self._direct_labor_repository.get_direct_labor_cost(production_request)

        valid_costs = [
            item.cost for item in direct_labor_costs
            if item.cost is not None
        ]
        average_direct_labor_cost = sum(valid_costs) / len(valid_costs) if valid_costs else 0

        rol_object = self._financial_query_repository.get_rol(rol_request)
        rol = rol_object.get("rol", 0)

        direct_labor_cost_pct = (average_direct_labor_cost / rol) * 100 if rol else None

        return {"direct_labor_cost_pct": direct_labor_cost_pct}