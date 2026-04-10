from __future__ import annotations

from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient
from app.domain.ports.production.production_cost_repository_port import ProductionCostRepositoryPort
from app.application.dto.production.production_request import ProductionRequest
from app.domain.entities.production.production_cost import ProductionCost
from app.shared.utils.spreadsheet_date import spreadsheet_date_in_range


class ProductionCostRepository(ProductionCostRepositoryPort):
    def __init__(self, client: GoogleSheetsClient, sheet_id: str, gid: str):
        self.client = client
        self.sheet_id = sheet_id
        self.gid = gid

    def get_production_cost(self, request: ProductionRequest) -> list[ProductionCost]:
        rows = self.client.read_csv_rows(sheet_id=self.sheet_id, gid=self.gid)
        production_costs = []

        for row in rows:
            if self._matches_request(row, request):
                try:
                    production_cost = ProductionCost(
                        branch=row.get("filial"),
                        date=row.get("data"),
                        cost=float(row.get("custo_de_producao", 0)),
                    )
                    production_costs.append(production_cost)
                except ValueError:
                    continue

        return production_costs

    def _matches_request(self, row: dict, request: ProductionRequest) -> bool:
        if request.branch and row.get("filial") != request.branch:
            return False

        return spreadsheet_date_in_range(
            row.get("data"),
            start_date=request.start_date,
            end_date=request.end_date,
        )