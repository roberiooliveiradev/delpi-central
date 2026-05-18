# app/domain/ports/financial/financial_query_repository_port.py
from abc import ABC, abstractmethod

from si_app.application.dto.financial.get_rol_request import GetRolRequest
from si_app.application.dto.financial.list_rol_by_branch_request import (
    ListRolByBranchRequest,
)


class FinancialQueryRepositoryPort(ABC):

    @abstractmethod
    def get_rol(self, request: GetRolRequest) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_rol_by_branch(self, request: ListRolByBranchRequest) -> dict[str, dict]:
        raise NotImplementedError