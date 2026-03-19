# app/infrastructure/persistence/google_sheets/kaizen_repository.py
from datetime import date
from typing import Optional, List

from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient
from app.domain.ports.kaizen.kaizen_query_port import KaizenQueryRepositoryPort
from app.domain.entities.kaizen.kaizen import Kaizen
from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.application.dto.kaizen.kaizen_summary_response import KaizenSummaryResponse
from app.infrastructure.persistence.google_sheets.utils import Utils


class KaizenRepository(KaizenQueryRepositoryPort):
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

    def _map_row_to_summary_model(self, row: dict) -> Optional[dict]:
        kaizen_id = row.get("kaizenid") or row.get("id")
        title = row.get("titulo")

        if not kaizen_id and not title:
            return None

        return {
            "id": str(kaizen_id or "").strip(),
            "title": str(title or "").strip(),
            "status": self.utils.empty_to_none(row.get("status")),
            "date_implemented": self.utils.empty_to_none(row.get("dataimplantacao")),
            "accountable": self.utils.empty_to_none(row.get("responsavel")),
            "sector": self.utils.empty_to_none(row.get("area_setor")),
            "investment": self.utils.to_float(row.get("investimento_rs")),
            "daily_savings": self.utils.to_float(row.get("ganhoreal_rs")),
        }

    def _is_implemented(self, status: Optional[str]) -> bool:
        if not status:
            return False

        normalized = (
            str(status)
            .strip()
            .lower()
            .replace("í", "i")
            .replace("ú", "u")
            .replace("ã", "a")
        )

        return normalized == "implantado"

    def _matches_title(self, title: Optional[str], search: Optional[str]) -> bool:
        if not search:
            return True
        if not title:
            return False
        return search.strip().lower() in title.strip().lower()

    def _matches_status(self, status: Optional[str], search: Optional[str]) -> bool:
        if not search:
            return True
        if not status:
            return False
        return status.strip().lower() == search.strip().lower()

    def _is_in_period(
        self,
        date_value: Optional[str],
        date_start: Optional[str],
        date_end: Optional[str],
    ) -> bool:
        parsed = self.utils.parse_date(date_value)
        if parsed is None:
            return False

        start = self.utils.parse_date(date_start) if date_start else None
        end = self.utils.parse_date(date_end) if date_end else None

        if start and parsed < start:
            return False

        if end and parsed > end:
            return False

        return True

    def _parse_date_safe(self, value: Optional[str]) -> Optional[date]:
        return self.utils.parse_date(value)


    def _days_active_in_range(
        self,
        implemented_at: Optional[str],
        range_start: Optional[str],
        range_end: Optional[str],
    ) -> int:
        impl_date = self._parse_date_safe(implemented_at)
        if impl_date is None:
            return 0

        start = self._parse_date_safe(range_start) if range_start else impl_date
        end = self._parse_date_safe(range_end) if range_end else date.today()

        if start is None or end is None:
            return 0

        effective_start = max(impl_date, start)

        if effective_start > end:
            return 0

        return (end - effective_start).days + 1


    def _calculate_kaizen_total_savings(
        self,
        row: dict,
        range_start: Optional[str],
        range_end: Optional[str],
    ) -> float:
        daily_savings = row.get("daily_savings") or 0.0
        active_days = self._days_active_in_range(
            implemented_at=row.get("date_implemented"),
            range_start=range_start,
            range_end=range_end,
        )
        return round(daily_savings * active_days, 2)

    def get_kaizen_summary(self, request: KaizenSummaryRequest) -> KaizenSummaryResponse:
        self.utils.validate_date_range(
            start_date_str=request.date_start,
            end_date_str=request.date_end,
        )

        rows = self.client.read_csv_rows(
            sheet_id=self.sheet_id,
            gid=self.gid,
        )

        normalized_rows = []
        for row in rows:
            item = self._map_row_to_summary_model(row)
            if item is not None:
                normalized_rows.append(item)

        concluded_rows = [
            row for row in normalized_rows
            if self._is_implemented(row["status"])
        ]

        filtered_rows = []
        for row in concluded_rows:
            title_ok = True
            status_ok = True

            if request.title:
                title_ok = request.title.strip().lower() in (row.get("title") or "").strip().lower()

            if request.status:
                status_ok = (row.get("status") or "").strip().lower() == request.status.strip().lower()

            if title_ok and status_ok:
                filtered_rows.append(row)

        kaizens = [Kaizen(**row) for row in filtered_rows]

        total_savings = sum(
            self._calculate_kaizen_total_savings(
                row=row,
                range_start=request.date_start,
                range_end=request.date_end,
            )
            for row in filtered_rows
        )

        return KaizenSummaryResponse(
            date_start=request.date_start,
            date_end=request.date_end,
            total_kaizens=len(kaizens),
            total_savings=round(total_savings, 2),
            list_kaizen=kaizens,
        )