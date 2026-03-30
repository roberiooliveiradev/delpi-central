# app/application/use_cases/financial/get_rol_use_case.py
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.domain.ports.financial.financial_query_repository_port import FinancialQueryRepositoryPort


class GetRolUseCase:

    def __init__(self, repository: FinancialQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: GetRolRequest) -> dict:
        return self._repository.get_rol(request)