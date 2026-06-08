from __future__ import annotations

from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient
from app.domain.ports.production.direct_labor_repository_port import DirectLaborRepositoryPort
from app.application.dto.production.production_request import ProductionRequest
from app.domain.entities.production.direct_labor_cost import DirectLaborCost
from app.shared.utils.spreadsheet_date import spreadsheet_date_in_range
from app.infrastructure.persistence.google_sheets.utils import Utils


class DirectLaborRepository(DirectLaborRepositoryPort):
    def __init__(self, client: GoogleSheetsClient, sheet_id: str, gid: str):
        self.client = client
        self.sheet_id = sheet_id
        self.gid = gid
        self.utils = Utils()

    def get_direct_labor_cost(self, request: ProductionRequest) -> list[DirectLaborCost]:
        rows = self.client.read_csv_rows(sheet_id=self.sheet_id, gid=self.gid)
        direct_labor_costs = []

        for row in rows:
            if self._matches_request(row, request):
                cost = self.utils.to_float(row.get("custo_mao_de_obra_direta"))

                if cost is None:
                    continue

                direct_labor_cost = DirectLaborCost(
                    branch=row.get("filial"),
                    date=row.get("data"),
                    cost=cost,
                )
                direct_labor_costs.append(direct_labor_cost)

        return direct_labor_costs

    def _matches_request(self, row: dict, request: ProductionRequest) -> bool:
        if request.branch and row.get("filial") != request.branch:
            return False

        return spreadsheet_date_in_range(
            row.get("data"),
            start_date=request.start_date,
            end_date=request.end_date,
        )