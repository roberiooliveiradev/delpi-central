from __future__ import annotations

from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient
from app.domain.ports.production.depreciation_repository_port import DepreciationRepositoryPort
from app.application.dto.production.production_request import ProductionRequest
from app.domain.entities.production.depreciation_cost import DepreciationCost

class DepreciationRepository(DepreciationRepositoryPort):
    def __init__(self, client: GoogleSheetsClient, sheet_id: str, gid: str):
        self.client = client
        self.sheet_id = sheet_id
        self.gid = gid

    def get_depreciation_cost(self, request: ProductionRequest) -> list[DepreciationCost]:
        rows = self.client.read_csv_rows(sheet_id=self.sheet_id, gid=self.gid)
        depreciation_costs = []

        for row in rows:
            if self._matches_request(row, request):
                try:
                    depreciation_cost = DepreciationCost(
                        branch=row.get("filial"),
                        date=row.get("data"),
                        cost=float(row.get("depreciacao", 0)),
                    )
                    depreciation_costs.append(depreciation_cost)
                except ValueError:
                    continue

        return depreciation_costs

    def _matches_request(self, row: dict, request: ProductionRequest) -> bool:
        if request.branch and row.get("filial") != request.branch:
            return False
        if request.start_date and row.get("data") < request.start_date:
            return False
        if request.end_date and row.get("data") > request.end_date:
            return False
        return True