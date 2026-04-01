from app.application.dto.commercial.commercial_target_request import CommercialTargetRequest
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.domain.ports.financial.financial_query_repository_port import FinancialQueryRepositoryPort


class GetRolTargetPctUseCase:
    def __init__(
        self,
        financial_query_repository: FinancialQueryRepositoryPort,
        target_value: float,
    ):
        self._financial_query_repository = financial_query_repository
        self._target_value = target_value

    def execute(self, request: CommercialTargetRequest) -> dict:
        rol_request = GetRolRequest(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        rol_result = self._financial_query_repository.get_rol(rol_request)
        rol_value = rol_result.get("rol_with_ipi", 0)

        rol_target_pct = (rol_value / self._target_value) * 100 if self._target_value else None

        return {
            "branch": request.branch,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "rol": rol_value,
            "target": self._target_value,
            "rol_target_pct": rol_target_pct,
        }