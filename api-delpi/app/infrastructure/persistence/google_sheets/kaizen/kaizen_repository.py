from datetime import date
from typing import Optional

from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient
from app.domain.ports.kaizen.kaizen_query_port import KaizenQueryRepositoryPort
from app.domain.entities.kaizen.kaizen import Kaizen, KaizenDetail
from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.application.dto.kaizen.kaizen_summary_response import KaizenSummaryResponse
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.shared.utils.spreadsheet_date import parse_spreadsheet_date
from app.domain.services.kaizen import kaizen_savings_validity


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

    def _first_float(self, row: dict, aliases: list[str]) -> Optional[float]:
        for alias in aliases:
            value = self.utils.to_float(row.get(alias))
            if value is not None:
                return value
        return None

    def _savings_inputs(
        self, row: dict
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        seconds_per_occurrence = self._first_float(
            row,
            ["segundos_por_ocorrencia", "segudos_por_ocorrecia"],
        )
        occurrences_per_day = self._first_float(
            row,
            ["ocorrencias_por_dia", "ocorrecias_por_dia"],
        )
        hourly_cost = self._first_float(row, ["custo_hora"])
        return seconds_per_occurrence, occurrences_per_day, hourly_cost

    def _calculate_daily_savings(self, row: dict) -> Optional[float]:
        """
        Ganho diário derivado da planilha:
        horas_poupadas_dia = (segundos_por_ocorrencia × ocorrencias_por_dia) / 3600
        ganho_diario = horas_poupadas_dia × custo_hora
        """
        seconds_per_occurrence, occurrences_per_day, hourly_cost = self._savings_inputs(
            row
        )

        if (
            seconds_per_occurrence is None
            or occurrences_per_day is None
            or hourly_cost is None
        ):
            return None

        hours_saved_per_day = (seconds_per_occurrence * occurrences_per_day) / 3600
        return round(hours_saved_per_day * hourly_cost, 2)

    def _annual_savings(self, daily_savings: Optional[float]) -> Optional[float]:
        if daily_savings is None:
            return None
        return round(daily_savings * 365, 2)

    def _hours_saved_per_day(self, row: dict) -> Optional[float]:
        seconds_per_occurrence, occurrences_per_day, _ = self._savings_inputs(row)
        if seconds_per_occurrence is None or occurrences_per_day is None:
            return None
        return round((seconds_per_occurrence * occurrences_per_day) / 3600, 4)

    def _iter_active_rows(self):
        rows = self.client.read_csv_rows(
            sheet_id=self.sheet_id,
            gid=self.gid,
        )
        for row in rows:
            if self._is_deleted(row.get("deleted")):
                continue
            yield row

    def _row_to_kaizen(self, row: dict) -> Kaizen:
        implemented = row["date_implemented"]
        return Kaizen(
            id=row["id"],
            title=row["title"],
            date_implemented=implemented,
            status=row["status"],
            accountable=row["accountable"],
            sector=row["sector"],
            investment=row["investment"],
            daily_savings=row["daily_savings"],
            annual_savings=row["annual_savings"],
            branch=row.get("branch"),
            quantity_date=row.get("quantity_date") or implemented,
        )

    def _map_row_to_summary_model(self, row: dict) -> Optional[dict]:
        title = self.utils.empty_to_none(row.get("descricao"))
        implemented_date = self.utils.empty_to_none(row.get("data"))

        if not title and not implemented_date:
            return None

        branch = self.utils.empty_to_none(row.get("filial"))
        daily_savings = self._calculate_daily_savings(row)

        return {
            "id": f"{branch or ''}-{implemented_date or ''}-{title or ''}".strip("-"),
            "title": title or "",
            "date_implemented": implemented_date,
            "status": self.utils.empty_to_none(row.get("status")),
            "accountable": self.utils.empty_to_none(row.get("responsavel")),
            "sector": self.utils.empty_to_none(row.get("area_setor")),
            "investment": self.utils.to_float(row.get("custo_investimento")),
            "daily_savings": daily_savings,
            "annual_savings": self._annual_savings(daily_savings),
            "branch": branch,
        }

    def _map_row_to_detail_model(self, row: dict) -> Optional[KaizenDetail]:
        summary = self._map_row_to_summary_model(row)
        if summary is None:
            return None

        seconds_per_occurrence, occurrences_per_day, hourly_cost = self._savings_inputs(
            row
        )

        return KaizenDetail(
            id=summary["id"],
            title=summary["title"],
            date_implemented=summary["date_implemented"],
            status=summary["status"],
            accountable=summary["accountable"],
            sector=summary["sector"],
            investment=summary["investment"],
            daily_savings=summary["daily_savings"],
            annual_savings=summary["annual_savings"],
            branch=summary.get("branch"),
            seconds_per_occurrence=seconds_per_occurrence,
            occurrences_per_day=occurrences_per_day,
            hourly_cost=hourly_cost,
            hours_saved_per_day=self._hours_saved_per_day(row),
        )

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

        # Regra de negócio: economia válida por 1 ano a partir da implantação.
        return kaizen_savings_validity.active_days_in_range(
            implemented=impl_date,
            range_start=start,
            range_end=end,
        )

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

        normalized_rows = []
        for row in self._iter_active_rows():
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

        kaizens = [self._row_to_kaizen(row) for row in count_rows]
        savings_kaizens: list[Kaizen] = []
        total_savings = 0.0
        for row in savings_rows:
            period_savings = self._calculate_kaizen_total_savings(
                row=row,
                range_start=request.date_start,
                range_end=request.date_end,
            )
            total_savings += period_savings
            item = self._row_to_kaizen(row)
            item.period_savings = period_savings
            savings_kaizens.append(item)

        return KaizenSummaryResponse(
            date_start=request.date_start,
            date_end=request.date_end,
            total_kaizens=len(kaizens),
            total_savings=round(total_savings, 2),
            list_kaizen=kaizens,
            list_savings_kaizen=savings_kaizens,
        )

    def get_kaizen_by_id(self, kaizen_id: str) -> Optional[KaizenDetail]:
        normalized_id = (kaizen_id or "").strip()
        if not normalized_id:
            return None

        for row in self._iter_active_rows():
            detail = self._map_row_to_detail_model(row)
            if detail is not None and detail.id == normalized_id:
                return detail

        return None

    def list_active_kaizen_details(self) -> list[KaizenDetail]:
        details: list[KaizenDetail] = []
        for row in self._iter_active_rows():
            detail = self._map_row_to_detail_model(row)
            if detail is not None:
                details.append(detail)
        return details