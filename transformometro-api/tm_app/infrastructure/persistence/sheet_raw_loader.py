from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from tm_app.config import settings
from tm_app.domain.raw_data import TransformometroRawData
from tm_app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)
from tm_app.infrastructure.providers.google_sheets.sheet_sources import (
    TransformometroSheetSources,
)

TAB_FILES = {
    "processos": "processos.csv",
    "revisao": "revisao.csv",
    "medicoes": "medicoes.csv",
    "investimentos": "investimentos.csv",
    "recursos_compartilhados": "recursos_compartilhados.csv",
    "revisao_recursos_compartilhados": "revisao_recursos_compartilhados.csv",
}


def _is_deleted(row: dict) -> bool:
    deleted = row.get("deletado")
    if deleted is None:
        return False
    return str(deleted).strip().upper() == "TRUE"


def _read_csv_file(path: Path) -> List[dict]:
    content = path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(content.splitlines())
    client = GoogleSheetsClient()
    return [
        client._normalize_row(row)  # noqa: SLF001 — reutiliza normalização de cabeçalho
        for row in reader
        if row and not _is_deleted(client._normalize_row(row))
    ]


class SheetRawLoader:
    def load_from_csv_dir(self, csv_dir: Path) -> TransformometroRawData:
        if not csv_dir.is_dir():
            raise FileNotFoundError(f"Diretório CSV não encontrado: {csv_dir}")

        data: dict[str, list] = {}
        for tab, filename in TAB_FILES.items():
            path = csv_dir / filename
            data[tab] = _read_csv_file(path) if path.exists() else []

        return TransformometroRawData(
            processos=data["processos"],
            revisoes=data["revisao"],
            medicoes=data["medicoes"],
            investimentos=data["investimentos"],
            recursos_compartilhados=data["recursos_compartilhados"],
            revisao_recursos_compartilhados=data["revisao_recursos_compartilhados"],
        )

    def load_from_google_sheets(self) -> TransformometroRawData:
        sources = settings.build_sheet_sources()
        client = GoogleSheetsClient(timeout=int(settings.GOOGLE_SHEETS_TIMEOUT or 10))

        def read_tab(tab: str) -> list[dict]:
            rows = client.read_csv_rows(sources.sheet_id, sources.gid_for(tab))
            return [row for row in rows if not _is_deleted(row)]

        return TransformometroRawData(
            processos=read_tab("processos"),
            revisoes=read_tab("revisao"),
            medicoes=read_tab("medicoes"),
            investimentos=read_tab("investimentos"),
            recursos_compartilhados=read_tab("recursos_compartilhados"),
            revisao_recursos_compartilhados=read_tab("revisao_recursos_compartilhados"),
        )

    def load(self, *, csv_dir: Path | None = None) -> TransformometroRawData:
        if csv_dir is not None:
            return self.load_from_csv_dir(csv_dir)
        return self.load_from_google_sheets()
