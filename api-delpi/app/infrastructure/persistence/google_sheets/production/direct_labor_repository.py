from __future__ import annotations

from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient
from app.domain.ports.production.direct_labor_repository_port import DirectLaborRepositoryPort
from app.application.dto.production.production_request import ProductionRequest
from app.domain.entities.production.direct_labor_cost import DirectLaborCost
from app.shared.utils.spreadsheet_date import spreadsheet_date_in_range


class DirectLaborRepository(DirectLaborRepositoryPort):
    def __init__(self, client: GoogleSheetsClient, sheet_id: str, gid: str):
        self.client = client
        self.sheet_id = sheet_id
        self.gid = gid

    def get_direct_labor_cost(self, request: ProductionRequest) -> list[DirectLaborCost]:
        rows = self.client.read_csv_rows(sheet_id=self.sheet_id, gid=self.gid)
        direct_labor_costs = []

        for row in rows:
            if self._matches_request(row, request):
                try:
                    direct_labor_cost = DirectLaborCost(
                        branch=row.get("filial"),
                        date=row.get("data"),
                        cost=float(row.get("custo_mao_de_obra_direta", 0)),
                    )
                    direct_labor_costs.append(direct_labor_cost)
                except ValueError:
                    continue

        return direct_labor_costs

    def _matches_request(self, row: dict, request: ProductionRequest) -> bool:
        if request.branch and row.get("filial") != request.branch:
            return False

        return spreadsheet_date_in_range(
            row.get("data"),
            start_date=request.start_date,
            end_date=request.end_date,
        )