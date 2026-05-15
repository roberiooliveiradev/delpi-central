from typing import Optional

from si_app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from si_app.application.dto.auditoria_5s.audit_5s_summary_response import (
    Audit5SSummaryResponse,
)
from si_app.domain.entities.audit_5s.audit_5s import Audit5S
from si_app.domain.ports.audit_5s.audit_5s_query_port import (
    Audit5SQueryRepositoryPort,
)
from si_app.infrastructure.persistence.google_sheets.utils import Utils
from si_app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)
from si_app.shared.utils.spreadsheet_date import parse_spreadsheet_date


class Audit5SRepository(Audit5SQueryRepositoryPort):
    def __init__(
        self,
        client: GoogleSheetsClient,
        sheet_id: str,
        gid: str,
        utils: Utils,
    ):
        self.client = client
        self.sheet_id = sheet_id
        self.gid = gid
        self.utils = utils

    def _is_deleted(self, value) -> bool:
        if value is None:
            return False
        normalized = str(value).strip().lower()
        return normalized in {"true", "1", "sim", "yes", "x"}

    def _map_row_to_model(self, row: dict) -> Optional[dict]:
        audit_date = self.utils.empty_to_none(row.get("data"))
        score = self.utils.to_float(row.get("nota"))
        branch = self.utils.empty_to_none(row.get("filial"))

        if not audit_date and score is None:
            return None

        return {
            "id": f"{branch or ''}-{audit_date or ''}".strip("-"),
            "date": audit_date,
            "average_line_score": score,
            "evaluated_area": None,
            "auditor": None,
            "audited": None,
            "inspection_number": None,
            "shift": None,
            "branch": branch,
        }

    def _is_in_date_range(
        self,
        value: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> bool:
        parsed_value = parse_spreadsheet_date(value)
        if parsed_value is None:
            return False

        parsed_start = parse_spreadsheet_date(start_date) if start_date else None
        parsed_end = parse_spreadsheet_date(end_date) if end_date else None

        if parsed_start and parsed_value < parsed_start:
            return False
        if parsed_end and parsed_value > parsed_end:
            return False

        return True

    def get_audit_summary(
        self,
        request: Audit5SSummaryRequest,
    ) -> Audit5SSummaryResponse:
        self.utils.validate_date_range(
            start_date_str=request.start_date,
            end_date_str=request.end_date,
        )

        rows = self.client.read_csv_rows(
            sheet_id=self.sheet_id,
            gid=self.gid,
        )

        normalized_rows = []
        for row in rows:
            if self._is_deleted(row.get("deleted")):
                continue

            item = self._map_row_to_model(row)
            if item is not None:
                normalized_rows.append(item)

        filtered_rows = [
            row
            for row in normalized_rows
            if self._is_in_date_range(
                value=row["date"],
                start_date=request.start_date,
                end_date=request.end_date,
            )
            and (
                not request.branch
                or (row.get("branch") or "").strip() == request.branch.strip()
            )
        ]

        audits = [Audit5S(**row) for row in filtered_rows]

        scores = [
            audit.average_line_score
            for audit in audits
            if audit.average_line_score is not None
        ]

        average_score = round(sum(scores) / len(scores), 2) if scores else 0.0

        return Audit5SSummaryResponse(
            start_date=request.start_date,
            end_date=request.end_date,
            average_score=average_score,
            list_audits=audits,
        )