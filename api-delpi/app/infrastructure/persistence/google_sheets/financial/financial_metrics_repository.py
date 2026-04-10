from __future__ import annotations

from typing import List

from app.infrastructure.persistence.google_sheets.financial.sheet_sources import (
    FinancialIndicatorsSources,
)
from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)


class FinancialMetricsRepository:
    def __init__(
        self,
        client: GoogleSheetsClient,
        sources: FinancialIndicatorsSources,
    ) -> None:
        self.client = client
        self.sources = sources

    def load_ebitda_rows(self) -> List[dict]:
        return self._read_active_tab("ebitda")

    def load_fixed_cost_rows(self) -> List[dict]:
        return self._read_active_tab("fixed_cost")

    def load_receivables_rows(self) -> List[dict]:
        return self._read_active_tab("receivables")

    def _read_active_tab(self, tab_name: str) -> List[dict]:
        rows = self.client.read_csv_rows(
            sheet_id=self.sources.sheet_id,
            gid=self.sources.gid_for(tab_name),
        )
        return [row for row in rows if not self._is_deleted(row)]

    def _is_deleted(self, row: dict) -> bool:
        deleted = row.get("deleted")
        if deleted is None:
            return False
        return str(deleted).strip().upper() == "TRUE"