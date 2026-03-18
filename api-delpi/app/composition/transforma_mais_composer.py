# app/composition/transforma_mais_composer.py

import os

from app.application.use_cases.transforma_mais.list_process_use_case import ListProcessUseCase
from app.application.use_cases.transforma_mais.get_process_summary_use_case import GetProcessSummaryUseCase
from app.infrastructure.persistence.google_sheets.transforma_mais.process_repository import ProcessRepository
from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient


DEFAULT_TRANSFORMA_MAIS_SHEET_ID = "1pqXRoXjSS91TxVqHioCPWKQVfY2ZAg-w"
DEFAULT_TRANSFORMA_MAIS_SHEET_GID = "127374664"
DEFAULT_GOOGLE_SHEETS_TIMEOUT = 10


def _build_repository() -> ProcessRepository:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))
    sheet_id = os.getenv("TRANSFORMA_MAIS_SHEET_ID", DEFAULT_TRANSFORMA_MAIS_SHEET_ID)
    gid = os.getenv("TRANSFORMA_MAIS_SHEET_GID", DEFAULT_TRANSFORMA_MAIS_SHEET_GID)

    client = GoogleSheetsClient(timeout=timeout)

    return ProcessRepository(
        client=client,
        sheet_id=sheet_id,
        gid=gid,
    )


def transforma_mais_list_process_composer() -> ListProcessUseCase:
    repository = _build_repository()
    return ListProcessUseCase(repository=repository)


def transforma_mais_get_process_summary_composer() -> GetProcessSummaryUseCase:
    repository = _build_repository()
    return GetProcessSummaryUseCase(repository=repository)