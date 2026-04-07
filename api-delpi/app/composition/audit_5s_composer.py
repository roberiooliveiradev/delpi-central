# app/composition/audit_5s_composer.py
import os

from app.application.use_cases.audit_5s.get_audit_5s_summary_use_case import (
    GetAudit5SSummaryUseCase,
)
from app.infrastructure.persistence.google_sheets.audit_5s.audit_5s_repository import (
    Audit5SRepository,
)
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)


DEFAULT_AUDIT_5S_SHEET_ID = "1s6orCcQ_ntXKlHEOoZWXHhlnTiP6RQXX"
DEFAULT_AUDIT_5S_SHEET_GID = "882327936"
DEFAULT_GOOGLE_SHEETS_TIMEOUT = 10


def _build_repository() -> Audit5SRepository:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))
    sheet_id = os.getenv("AUDIT_5S_SHEET_ID", DEFAULT_AUDIT_5S_SHEET_ID)
    gid = os.getenv("AUDIT_5S_SHEET_GID", DEFAULT_AUDIT_5S_SHEET_GID)

    client = GoogleSheetsClient(timeout=timeout)
    utils = Utils()

    return Audit5SRepository(
        client=client,
        sheet_id=sheet_id,
        gid=gid,
        utils=utils,
    )


def audit_5s_get_summary_composer() -> GetAudit5SSummaryUseCase:
    repository = _build_repository()
    return GetAudit5SSummaryUseCase(repository=repository)