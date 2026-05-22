from datetime import date
from typing import Optional

from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient
from app.domain.ports.kaizen.kaizen_query_port import KaizenQueryRepositoryPort
from app.domain.entities.kaizen.kaizen import Kaizen
from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.application.dto.kaizen.kaizen_summary_response import KaizenSummaryResponse
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.shared.utils.spreadsheet_date import parse_spreadsheet_date


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

    def _is_deleted(self, value) -> bool:
        if value is None:
            return False
        normalized = str(value).strip().lower()
        return normalized in {"true", "1", "sim", "yes", "x"}

    def _map_row_to_summary_model(self, row: dict) -> Optional[dict]:
        title = self.utils.empty_to_none(row.get("descricao"))
        implemented_date = self.utils.empty_to_none(row.get("data"))

        if not title and not implemented_date:
            return None

        branch = self.utils.empty_to_none(row.get("filial"))

        return {
            "id": f"{branch or ''}-{implemented_date or ''}-{title or ''}".strip("-"),
            "title": title or "",
            "date_implemented": implemented_date,
            "status": self.utils.empty_to_none(row.get("status")),
            "accountable": self.utils.empty_to_none(row.get("responsavel")),
            "sector": self.utils.empty_to_none(row.get("area_setor")),
            "investment": self.utils.to_float(row.get("custo_investimento")),
            "daily_savings": self.utils.to_float(row.get("ganho_diario")),
            "branch": branch,
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

    def _parse_date_safe(self, value: Optional[str]):
        return parse_spreadsheet_date(value)

    def _implemented_in_range(
        self,
        implemented_at: Optional[str],
        range_start: Optional[str],
        range_end: Optional[str],
    ) -> bool:
        """Kaizen entra no período quando a data de implantação (coluna data) cai no intervalo."""
        impl_date = self._parse_date_safe(implemented_at)
        if impl_date is None:
            return False

        start = self._parse_date_safe(range_start) if range_start else None
        end = self._parse_date_safe(range_end) if range_end else None

        if start is not None and impl_date < start:
            return False
        if end is not None and impl_date > end:
            return False

        return True

    def _contributes_savings_in_range(
        self,
        implemented_at: Optional[str],
        range_start: Optional[str],
        range_end: Optional[str],
    ) -> bool:
        """
        Ganhos do mês: kaizen implantado até o fim do período e com dias ativos
        dentro do intervalo (inclui implantações anteriores ao início do mês).
        """
        impl_date = self._parse_date_safe(implemented_at)
        if impl_date is None:
            return False

        end = self._parse_date_safe(range_end) if range_end else None
        if end is not None and impl_date > end:
            return False

        return (
            self._days_active_in_range(
                implemented_at=implemented_at,
                range_start=range_start,
                range_end=range_end,
            )
            > 0
        )

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
            if self._is_deleted(row.get("deleted")):
                continue

            item = self._map_row_to_summary_model(row)
            if item is not None:
                normalized_rows.append(item)

        implemented_rows = [
            row for row in normalized_rows
            if self._is_implemented(row["status"])
        ]

        count_rows: list[dict] = []
        savings_rows: list[dict] = []
        for row in implemented_rows:
            title_ok = True
            status_ok = True
            branch_ok = True

            if request.title:
                title_ok = request.title.strip().lower() in (row.get("title") or "").strip().lower()

            if request.status:
                status_ok = (row.get("status") or "").strip().lower() == request.status.strip().lower()

            if request.branch:
                branch_ok = (row.get("branch") or "").strip() == request.branch.strip()

            if not (title_ok and status_ok and branch_ok):
                continue

            if self._implemented_in_range(
                row.get("date_implemented"),
                request.date_start,
                request.date_end,
            ):
                count_rows.append(row)

            if self._contributes_savings_in_range(
                row.get("date_implemented"),
                request.date_start,
                request.date_end,
            ):
                savings_rows.append(row)

        kaizens = [
            Kaizen(
                id=row["id"],
                title=row["title"],
                date_implemented=row["date_implemented"],
                status=row["status"],
                accountable=row["accountable"],
                sector=row["sector"],
                investment=row["investment"],
                daily_savings=row["daily_savings"],
                branch=row.get("branch"),
            )
            for row in count_rows
        ]

        total_savings = sum(
            self._calculate_kaizen_total_savings(
                row=row,
                range_start=request.date_start,
                range_end=request.date_end,
            )
            for row in savings_rows
        )

        return KaizenSummaryResponse(
            date_start=request.date_start,
            date_end=request.date_end,
            total_kaizens=len(kaizens),
            total_savings=round(total_savings, 2),
            list_kaizen=kaizens,
        )