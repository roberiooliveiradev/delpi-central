from __future__ import annotations

from si_app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient
from si_app.domain.ports.production.production_cost_repository_port import ProductionCostRepositoryPort
from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.entities.production.production_cost import ProductionCost
from si_app.shared.utils.spreadsheet_date import spreadsheet_date_in_range
from si_app.infrastructure.persistence.google_sheets.utils import Utils


class ProductionCostRepository(ProductionCostRepositoryPort):
    def __init__(self, client: GoogleSheetsClient, sheet_id: str, gid: str):
        self.client = client
        self.sheet_id = sheet_id
        self.gid = gid
        self.utils = Utils()

    def get_production_cost(self, request: ProductionRequest) -> list[ProductionCost]:
        rows = self.client.read_csv_rows(sheet_id=self.sheet_id, gid=self.gid)
        production_costs = []

        for row in rows:
            if self._matches_request(row, request):
                cost = self.utils.to_float(row.get("custo_de_producao"))

                if cost is None:
                    continue

                production_cost = ProductionCost(
                    branch=row.get("filial"),
                    date=row.get("data"),
                    cost=cost,
                )
                production_costs.append(production_cost)

        return production_costs

    def _matches_request(self, row: dict, request: ProductionRequest) -> bool:
        if request.branch and row.get("filial") != request.branch:
            return False

        return spreadsheet_date_in_range(
            row.get("data"),
            start_date=request.start_date,
            end_date=request.end_date,
        )