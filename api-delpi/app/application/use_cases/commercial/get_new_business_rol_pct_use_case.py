from app.application.dto.commercial.new_business_rol_pct_request import NewBusinessRolPctRequest
from app.domain.ports.commercial.new_business_rol_pct_repository_port import (
    NewBusinessRolPctRepositoryPort,
)


class GetNewBusinessRolPctUseCase:
    def __init__(self, *, new_business_rol_pct_repository: NewBusinessRolPctRepositoryPort):
        self._new_business_rol_pct_repository = new_business_rol_pct_repository

    def execute(self, request: NewBusinessRolPctRequest) -> dict:
        indicator = self._new_business_rol_pct_repository.get_new_business_rol_pct(request)

        return {
            "branch": indicator.branch,
            "start_date": indicator.start_date,
            "end_date": indicator.end_date,
            "total_rol": indicator.total_rol,
            "new_business_rol": indicator.new_business_rol,
            "weg_rol": indicator.weg_rol,
            "new_business_rol_pct": indicator.new_business_rol_pct,
        }
