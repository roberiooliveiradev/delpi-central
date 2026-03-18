from datetime import datetime, date, timedelta
from typing import List, Optional

from app.application.dto.transforma_mais.process_request import ProcessRequest
from app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from app.application.dto.transforma_mais.process_summary_response import (
    MonthlySummaryItem,
    ProcessSummaryResponse,
    RangeSummary,
)
from app.domain.entities.transforma_mais.process import Process
from app.domain.ports.transforma_mais.process_query_port import ProcessQueryRepositoryPort
from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient


class ProcessRepository(ProcessQueryRepositoryPort):
    def __init__(
        self,
        client: GoogleSheetsClient,
        sheet_id: str,
        gid: str,
    ):
        self.client = client
        self.sheet_id = sheet_id
        self.gid = gid

    def list_process(self, request: ProcessRequest) -> List[Process]:
        self._validate_date_range(request.start_date, request.end_date)

        rows = self.client.read_csv_rows(
            sheet_id=self.sheet_id,
            gid=self.gid,
        )

        items = []

        for row in rows:
            entity = self._map_row_to_entity(row)
            if entity and self._matches(entity, request):
                items.append(entity)

        return items

    def get_process_summary(
        self,
        request: ProcessSummaryRequest
    ) -> ProcessSummaryResponse:
        self._validate_date_range(request.start_date, request.end_date)

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
            if self._is_concluded(row["status"])
        ]

        implemented_solutions = len(concluded_rows)

        total_savings_until_now = sum(row["economy_until_now"] for row in concluded_rows)
        total_investment_until_now = sum(row["investment_total"] for row in concluded_rows)

        roi_values = [
            row["roi_annual_percent"]
            for row in concluded_rows
            if row["roi_annual_percent"] is not None
        ]
        average_roi_percent = round(sum(roi_values) / len(roi_values), 2) if roi_values else 0.0

        total_hours_saved_until_now = sum(
            self._calculate_hours_saved_until_now(row)
            for row in concluded_rows
        )

        monthly_description = self._build_monthly_series(concluded_rows)

        range_rows = self._filter_by_date_range(
            concluded_rows,
            request.start_date,
            request.end_date,
        )

        range_summary = RangeSummary(
            start_date=request.start_date,
            end_date=request.end_date,
            accumulated_savings=round(
                sum(row["economy_until_now"] for row in range_rows),
                2
            ),
        )

        return ProcessSummaryResponse(
            implemented_solutions=implemented_solutions,
            total_savings_until_now=round(total_savings_until_now, 2),
            total_hours_saved_until_now=round(total_hours_saved_until_now, 2),
            total_investment_until_now=round(total_investment_until_now, 2),
            average_roi_percent=average_roi_percent,
            monthly_description=monthly_description,
            range=range_summary,
        )

    def _build_monthly_series(self, rows: list[dict]) -> list[MonthlySummaryItem]:
        valid_rows = [
            row for row in rows
            if row["implementation_date_obj"] is not None
        ]

        if not valid_rows:
            return []

        first_month = self._month_start(
            min(row["implementation_date_obj"] for row in valid_rows)
        )
        current_month = self._month_start(date.today())

        result = []
        cursor = first_month

        while cursor <= current_month:
            total_savings_month = 0.0

            for row in valid_rows:
                implementation_date = row["implementation_date_obj"]
                if implementation_date is None:
                    continue

                active_days = self._get_active_days_in_month(
                    implementation_date=implementation_date,
                    month_start=cursor,
                )

                if active_days <= 0:
                    continue

                total_savings_month += active_days * row["economy_daily"]

            result.append(
                MonthlySummaryItem(
                    month=cursor.strftime("%Y-%m"),
                    total_savings_month=round(total_savings_month, 2),
                )
            )

            cursor = self._next_month(cursor)

        return result

    def _map_row_to_summary_model(self, row: dict) -> Optional[dict]:
        process_id = row.get("id")
        name_process = row.get("nome_do_processo")

        if not process_id and not name_process:
            return None

        implementation_date_raw = self._first_non_empty(
            row,
            ["data_da_implementacao"]
        )

        return {
            "id": str(process_id or "").strip(),
            "name_process": str(name_process or "").strip(),
            "status": self._empty_to_none(row.get("status")),
            "investment_total": self._to_float(row.get("investimento_total_r")) or 0.0,
            "economy_until_now": self._to_float(row.get("economia_ate_agora")) or 0.0,
            "economy_monthly": self._to_float(row.get("economia_mensal_r")) or self._to_float(row.get("economia_mensal")) or 0.0,
            "economy_daily": self._to_float(row.get("economia_por_dia_r")) or self._to_float(row.get("economia_por_dia")) or 0.0,
            "roi_annual_percent": self._to_float(row.get("roi_anual_percent")),
            "implementation_date": implementation_date_raw,
            "implementation_date_obj": self._parse_date(implementation_date_raw),
            "tempo_atual_por_execucao_min": self._to_float(row.get("tempo_atual_por_execucao_min")) or 0.0,
            "tempo_apos_melhoria_min": self._to_float(row.get("tempo_apos_melhoria_min")) or 0.0,
            "execucoes_por_mes": self._to_float(row.get("execucoes_por_mes")) or 0.0,
            "dias_implantados": self._to_float(row.get("dias_implantados")) or 0.0,
        }

    def _filter_by_date_range(
        self,
        rows: list[dict],
        start_date_str: Optional[str],
        end_date_str: Optional[str],
    ) -> list[dict]:
        if not start_date_str and not end_date_str:
            return rows

        start_date = self._parse_date(start_date_str) if start_date_str else None
        end_date = self._parse_date(end_date_str) if end_date_str else None

        filtered = []

        for row in rows:
            implementation_date = row["implementation_date_obj"]

            if implementation_date is None:
                continue

            if start_date and implementation_date < start_date:
                continue

            if end_date and implementation_date > end_date:
                continue

            filtered.append(row)

        return filtered

    def _calculate_hours_saved_until_now(self, row: dict) -> float:
        time_before = row["tempo_atual_por_execucao_min"]
        time_after = row["tempo_apos_melhoria_min"]
        executions_per_month = row["execucoes_por_mes"]
        days_implanted = row["dias_implantados"]

        if days_implanted <= 0:
            return 0.0

        minutes_saved_per_execution = max(time_before - time_after, 0.0)
        monthly_minutes_saved = minutes_saved_per_execution * executions_per_month
        proportional_minutes_saved = monthly_minutes_saved * (days_implanted / 30.0)

        return proportional_minutes_saved / 60.0

    def _get_active_days_in_month(
        self,
        implementation_date: date,
        month_start: date,
    ) -> int:
        month_end = self._month_end(month_start)

        if implementation_date > month_end:
            return 0

        active_start = max(implementation_date, month_start)
        return (month_end - active_start).days + 1

    def _month_start(self, value: date) -> date:
        return value.replace(day=1)

    def _month_end(self, value: date) -> date:
        return self._next_month(value) - timedelta(days=1)

    def _next_month(self, value: date) -> date:
        if value.month == 12:
            return date(value.year + 1, 1, 1)
        return date(value.year, value.month + 1, 1)

    def _is_concluded(self, status: Optional[str]) -> bool:
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

        return normalized == "concluido"

    def _map_row_to_entity(self, row: dict) -> Optional[Process]:
        process_id = row.get("id")
        name_process = row.get("nome_do_processo")

        if not process_id and not name_process:
            return None

        return Process(
            id=str(process_id or "").strip(),
            name_process=str(name_process or "").strip(),
            sector_name=self._empty_to_none(row.get("setor")),
            daily_savings=self._to_float(row.get("economia_por_dia_r")) or self._to_float(row.get("economia_por_dia")),
            payback_months=self._to_float(row.get("payback_meses")),
            status=self._empty_to_none(row.get("status")),
            implementetion_date=self._empty_to_none(row.get("data_da_implementacao")),
        )

    def _matches(self, process: Process, request: ProcessRequest) -> bool:
        if request.id and request.id.lower() not in process.id.lower():
            return False

        if request.name_process and request.name_process.lower() not in process.name_process.lower():
            return False

        if request.sector_name and request.sector_name.lower() not in (process.sector_name or "").lower():
            return False

        if request.status and request.status.lower() not in (process.status or "").lower():
            return False

        if not self._matches_date_range(process.implementetion_date, request.start_date, request.end_date):
            return False

        return True

    def _matches_date_range(
        self,
        process_date_value: Optional[str],
        start_date_str: Optional[str],
        end_date_str: Optional[str],
    ) -> bool:
        if not start_date_str and not end_date_str:
            return True

        process_date = self._parse_date(process_date_value)
        if process_date is None:
            return False

        start_date = self._parse_date(start_date_str) if start_date_str else None
        end_date = self._parse_date(end_date_str) if end_date_str else None

        if start_date and process_date < start_date:
            return False

        if end_date and process_date > end_date:
            return False

        return True

    def _validate_date_range(
        self,
        start_date_str: Optional[str],
        end_date_str: Optional[str],
    ) -> None:
        start_date = self._parse_date(start_date_str) if start_date_str else None
        end_date = self._parse_date(end_date_str) if end_date_str else None

        if start_date_str and start_date is None:
            raise ValueError("start_date inválida. Use formatos como YYYY-MM-DD ou DD/MM/YYYY.")

        if end_date_str and end_date is None:
            raise ValueError("end_date inválida. Use formatos como YYYY-MM-DD ou DD/MM/YYYY.")

        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date não pode ser maior que end_date.")

    def _parse_date(self, value: Optional[str]) -> Optional[date]:
        if value is None:
            return None

        raw = str(value).strip()
        if not raw:
            return None

        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                continue

        return None

    def _first_non_empty(self, row: dict, aliases: list[str]) -> Optional[str]:
        for alias in aliases:
            value = row.get(alias)
            if value is not None and str(value).strip() != "":
                return str(value).strip()
        return None

    def _to_float(self, value) -> Optional[float]:
        if value is None or str(value).strip() == "":
            return None

        raw = str(value).strip()
        raw = raw.replace("R$", "").replace("%", "").replace(" ", "")

        if raw in {"-", "—"}:
            return None

        if "," in raw and "." in raw:
            raw = raw.replace(".", "").replace(",", ".")
        elif "," in raw:
            raw = raw.replace(",", ".")

        try:
            return float(raw)
        except ValueError:
            return None

    def _empty_to_none(self, value):
        if value is None:
            return None

        value = str(value).strip()
        return value or None