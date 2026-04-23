from __future__ import annotations

from typing import List

from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)
from app.infrastructure.persistence.google_sheets.utils import Utils


class FinancialFixedCostRepository:
    def __init__(
        self,
        client: GoogleSheetsClient,
        sheet_id: str,
        gid: str,
    ) -> None:
        self.client = client
        self.sheet_id = sheet_id
        self.gid = gid
        self.utils = Utils()

    def load_rows(self) -> List[dict]:
        rows = self.client.read_csv_rows(
            sheet_id=self.sheet_id,
            gid=self.gid,
        )

        normalized_rows: List[dict] = []

        for row in rows:
            if self._is_deleted(row):
                continue

            normalized_rows.append(
                {
                    "filial": row.get("filial"),
                    "data": row.get("data"),
                    "custos_fixos": self.utils.to_float(row.get("custos_fixos")),
                }
            )

        return normalized_rows

    def _is_deleted(self, row: dict) -> bool:
        deleted = row.get("deleted")
        if deleted is None:
            return False
        return str(deleted).strip().upper() == "TRUE"