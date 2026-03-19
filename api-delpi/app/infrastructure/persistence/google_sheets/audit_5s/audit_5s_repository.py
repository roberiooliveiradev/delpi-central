# app/infrastructure/persistence/google_sheets/auditoria_5s/audit_5s_repository.py
from datetime import datetime
from typing import Optional

from app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from app.application.dto.auditoria_5s.audit_5s_summary_response import (
    Audit5SSummaryResponse,
)
from app.domain.entities.audit_5s.audit_5s import Audit5S
from app.domain.ports.audit_5s.audit_5s_query_port import (
    Audit5SQueryRepositoryPort,
)
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)


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

    def _format_date_pt_br(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None

        raw = str(value).strip()

        patterns = [
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%d",
        ]

        for pattern in patterns:
            try:
                parsed = datetime.strptime(raw, pattern)
                return parsed.strftime("%d/%m/%Y")
            except ValueError:
                continue

        parsed_by_utils = self.utils.parse_date(raw)
        if parsed_by_utils:
            return parsed_by_utils.strftime("%d/%m/%Y")

        return raw

    def _map_row_to_model(self, row: dict) -> Optional[dict]:
        audit_id = self.utils.first_non_empty(row, ["id"])
        audit_date = self.utils.first_non_empty(row, ["data"])
        score = row.get("media_linha_percent")

        if not audit_id and not audit_date and score in {None, ""}:
            return None

        return {
            "id": str(audit_id or "").strip(),
            "date": self._format_date_pt_br(audit_date),
            "average_line_score": self.utils.to_float(score),
            "evaluated_area": self.utils.empty_to_none(row.get("area_avaliada")),
            "auditor": self.utils.empty_to_none(row.get("auditor")),
            "audited": self.utils.empty_to_none(row.get("auditado")),
            "inspection_number": self.utils.empty_to_none(row.get("n_da_inspecao")),
            "shift": self.utils.empty_to_none(row.get("turno")),
        }

    def _is_in_date_range(
        self,
        value: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> bool:
        parsed_value = self.utils.parse_date(value)
        if parsed_value is None:
            return False

        parsed_start = self.utils.parse_date(start_date) if start_date else None
        parsed_end = self.utils.parse_date(end_date) if end_date else None

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
            item = self._map_row_to_model(row)
            if item is not None:
                normalized_rows.append(item)

        filtered_rows = [
            row for row in normalized_rows
            if self._is_in_date_range(
                value=row["date"],
                start_date=request.start_date,
                end_date=request.end_date,
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
            start_date=self._format_filter_date(request.start_date),
            end_date=self._format_filter_date(request.end_date),
            average_score=average_score,
            list_audits=audits,
        )
    
    def _format_filter_date(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        parsed = self.utils.parse_date(value)
        return parsed.strftime("%d/%m/%Y") if parsed else value