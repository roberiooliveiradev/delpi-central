from __future__ import annotations

from si_app.application.dto.financial.get_rol_request import GetRolRequest
from si_app.application.dto.financial.list_rol_by_branch_request import ListRolByBranchRequest
from si_app.domain.ports.financial.financial_query_repository_port import FinancialQueryRepositoryPort
from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient


class DelpiFinancialGateway(FinancialQueryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_rol(self, request: GetRolRequest) -> dict:
        return self._client.get_rol(
            params={
                "branch": request.branch,
                "start_date": request.start_date,
                "end_date": request.end_date,
            },
            authorization=bearer_authorization_from_context(),
        )

    def list_rol_by_branch(self, request: ListRolByBranchRequest) -> dict[str, dict]:
        auth = bearer_authorization_from_context()
        result: dict[str, dict] = {}
        for branch in request.branches:
            data = self._client.get_rol(
                params={
                    "branch": branch,
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                },
                authorization=auth,
            )
            result[branch] = data
        return result
