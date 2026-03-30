# app/domain/ports/financial/financial_query_repository_port.py
from abc import ABC, abstractmethod
from app.application.dto.financial.get_rol_request import GetRolRequest


class FinancialQueryRepositoryPort(ABC):

    @abstractmethod
    def get_rol(self, request: GetRolRequest) -> dict:
        raise NotImplementedError