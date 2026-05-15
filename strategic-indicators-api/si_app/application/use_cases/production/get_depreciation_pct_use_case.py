from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.ports.production.depreciation_repository_port import DepreciationRepositoryPort
from si_app.domain.ports.financial.financial_query_repository_port import FinancialQueryRepositoryPort
from si_app.application.dto.financial.get_rol_request import GetRolRequest

class GetDepreciationPctUseCase:
    def __init__(
        self,
        depreciation_repository: DepreciationRepositoryPort,
        financial_query_repository: FinancialQueryRepositoryPort
    ):
        self._depreciation_repository = depreciation_repository
        self._financial_query_repository = financial_query_repository

    def execute(self, production_request: ProductionRequest, rol_request: GetRolRequest) -> dict:
        depreciation_cost = self._depreciation_repository.get_depreciation_cost(production_request)
        average_depreciation_cost = (
            sum(dc.cost for dc in depreciation_cost if dc.cost is not None) / len(depreciation_cost)
            if depreciation_cost else 0
        )

        rol_object = self._financial_query_repository.get_rol(rol_request)
        rol = rol_object.get("rol_with_ipi", 0)

        depreciation_pct = (average_depreciation_cost / rol) * 100 if rol else None

        return {"depreciation_pct": depreciation_pct}