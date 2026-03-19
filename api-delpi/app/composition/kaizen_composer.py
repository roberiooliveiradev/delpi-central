# app/composition/kaizen_composer.py

import os

from app.application.use_cases.kaizen.get_kaizen_summary_use_case import GetKaizenSummaryUseCase
from app.infrastructure.persistence.google_sheets.kaizen.kaizen_repository import KaizenRepository
from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient
from app.infrastructure.persistence.google_sheets.utils import Utils


DEFAULT_KAIZEN_SHEET_ID = "16KddGcWtir5RfR-gv1ba7yrjtdjW2M4KQ1TV40xadRY"
DEFAULT_KAIZEN_SHEET_GID = "0"
DEFAULT_GOOGLE_SHEETS_TIMEOUT = 10


def _build_repository() -> KaizenRepository:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))
    sheet_id = os.getenv("KAIZEN_SHEET_ID", DEFAULT_KAIZEN_SHEET_ID)
    gid = os.getenv("KAIZEN_SHEET_GID", DEFAULT_KAIZEN_SHEET_GID)

    client = GoogleSheetsClient(timeout=timeout)
    utils = Utils()

    return KaizenRepository(
        client=client,
        sheet_id=sheet_id,
        gid=gid,
        utils=utils,
    )


def kaizen_get_summary_composer() -> GetKaizenSummaryUseCase:
    repository = _build_repository()
    return GetKaizenSummaryUseCase(repository=repository)