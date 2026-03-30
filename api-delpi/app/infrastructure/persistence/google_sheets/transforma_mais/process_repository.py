from __future__ import annotations

from typing import List

from app.application.dto.transforma_mais.raw_data import TransformaMaisRawData
from app.domain.ports.transforma_mais.process_query_port import ProcessQueryRepositoryPort
from app.infrastructure.persistence.google_sheets.transforma_mais.sheet_sources import (
    TransformaMaisSources,
)
from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient


class ProcessRepository(ProcessQueryRepositoryPort):
    def __init__(
        self,
        client: GoogleSheetsClient,
        sources: TransformaMaisSources,
    ):
        self.client = client
        self.sources = sources

    def load_raw_data(self) -> TransformaMaisRawData:
        return TransformaMaisRawData(
            processos=self._read_active_tab("processos"),
            revisoes=self._read_active_tab("revisao"),
            medicoes=self._read_active_tab("medicoes"),
            investimentos=self._read_active_tab("investimentos"),
            recursos_compartilhados=self._read_active_tab("recursos_compartilhados"),
            revisao_recursos_compartilhados=self._read_active_tab("revisao_recursos_compartilhados"),
        )

    def _read_active_tab(self, tab_name: str) -> List[dict]:
        rows = self.client.read_csv_rows(
            sheet_id=self.sources.sheet_id,
            gid=self.sources.gid_for(tab_name),
        )
        return [row for row in rows if not self._is_deleted(row)]

    def _is_deleted(self, row: dict) -> bool:
        deleted = row.get("deletado")
        if deleted is None:
            return False
        return str(deleted).strip().upper() == "TRUE"