# app/composition/financial_composer.py

from app.application.use_cases.financial.get_rol_use_case import GetRolUseCase
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import FinancialRepository


def build_get_rol_use_case() -> GetRolUseCase:
    repository = FinancialRepository()
    return GetRolUseCase(repository)