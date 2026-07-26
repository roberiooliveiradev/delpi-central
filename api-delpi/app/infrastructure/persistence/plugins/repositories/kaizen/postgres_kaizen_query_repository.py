from __future__ import annotations

from datetime import date
from typing import Any, Optional

from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.application.dto.kaizen.kaizen_summary_response import KaizenSummaryResponse
from app.domain.entities.kaizen.kaizen import Kaizen, KaizenDetail
from app.domain.ports.kaizen.kaizen_query_port import KaizenQueryRepositoryPort
from app.domain.services.kaizen import kaizen_savings_validity
from app.domain.services.kaizen.kaizen_indicator_eligibility import (
    counts_for_quantity,
    date_in_range,
    is_implemented_status,
    quantity_anchor_from_row,
)
from app.domain.services.kaizen.kaizen_query_mapper import (
    _as_date,
    _as_float,
    row_legacy_sheet_id,
    row_to_kaizen,
    row_to_kaizen_detail,
)
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository

_KAIZEN_QUERY_SELECT = """
    SELECT k.id,
           k.branch_code,
           k.title,
           k.accountable,
           k.sector,
           k.investment,
           k.seconds_per_occurrence,
           k.occurrences_per_day,
           k.hourly_cost,
           k.daily_savings,
           k.annual_savings,
           k.status,
           k.date_committee_approved,
           k.date_implemented
      FROM quality.kaizens k
     WHERE k.deleted_at IS NULL
"""


class PostgresKaizenQueryRepository(PluginBaseRepository, KaizenQueryRepositoryPort):
    """Leitura analítica de kaizens a partir do PostgreSQL (substitui Google Sheets)."""

    def __init__(self, utils: Utils | None = None, connection=None) -> None:
        super().__init__(connection=connection)
        self._utils = utils or Utils()

    def _load_rows(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"{_KAIZEN_QUERY_SELECT} ORDER BY k.date_implemented DESC NULLS LAST, k.created_at DESC"
        )

    def _parse_request_dates(
        self, request: KaizenSummaryRequest
    ) -> tuple[date | None, date | None]:
        self._utils.validate_date_range(request.date_start, request.date_end)
        start = self._utils.parse_date(request.date_start) if request.date_start else None
        end = self._utils.parse_date(request.date_end) if request.date_end else None
        return start, end

    @staticmethod
    def _matches_filters(row: dict[str, Any], request: KaizenSummaryRequest) -> bool:
        if request.title:
            title = (row.get("title") or "").strip().lower()
            if request.title.strip().lower() not in title:
                return False

        if request.status:
            row_status = (row.get("status") or "").strip().lower()
            if row_status != request.status.strip().lower():
                return False

        if request.branch:
            row_branch = (row.get("branch_code") or "").strip()
            if row_branch != request.branch.strip():
                return False

        return True

    @staticmethod
    def _contributes_savings_in_range(
        implemented_at: date | None,
        range_start: date | None,
        range_end: date | None,
    ) -> bool:
        if implemented_at is None:
            return False
        if range_end is not None and implemented_at > range_end:
            return False
        return (
            kaizen_savings_validity.active_days_in_range(
                implemented_at,
                range_start,
                range_end,
            )
            > 0
        )

    @staticmethod
    def _calculate_row_total_savings(
        row: dict[str, Any],
        range_start: date | None,
        range_end: date | None,
    ) -> float:
        daily = _as_float(row.get("daily_savings")) or 0.0
        implemented = _as_date(row.get("date_implemented"))
        active_days = kaizen_savings_validity.active_days_in_range(
            implemented,
            range_start,
            range_end,
        )
        return round(daily * active_days, 2)

    def get_kaizen_summary(self, request: KaizenSummaryRequest) -> KaizenSummaryResponse:
        range_start, range_end = self._parse_request_dates(request)
        rows = self._load_rows()

        count_rows: list[dict[str, Any]] = []
        savings_rows: list[dict[str, Any]] = []

        for row in rows:
            if not self._matches_filters(row, request):
                continue

            status = row.get("status")
            quantity_day = quantity_anchor_from_row(row)
            implemented = _as_date(row.get("date_implemented"))

            if counts_for_quantity(status) and date_in_range(
                quantity_day, range_start, range_end
            ):
                count_rows.append(row)

            if is_implemented_status(status) and self._contributes_savings_in_range(
                implemented, range_start, range_end
            ):
                savings_rows.append(row)

        kaizens: list[Kaizen] = [row_to_kaizen(row) for row in count_rows]
        savings_kaizens: list[Kaizen] = []
        total_savings = 0.0
        for row in savings_rows:
            period_savings = self._calculate_row_total_savings(
                row, range_start, range_end
            )
            total_savings += period_savings
            item = row_to_kaizen(row)
            item.period_savings = period_savings
            savings_kaizens.append(item)

        return KaizenSummaryResponse(
            start_date=request.date_start,
            end_date=request.date_end,
            total_kaizens=len(kaizens),
            total_savings=round(total_savings, 2),
            list_kaizen=kaizens,
            list_savings_kaizen=savings_kaizens,
        )

    def get_kaizen_by_id(self, kaizen_id: str) -> Optional[KaizenDetail]:
        normalized_id = (kaizen_id or "").strip()
        if not normalized_id:
            return None

        row = self.fetch_one(
            f"""
            {_KAIZEN_QUERY_SELECT}
               AND k.id::text = %s
            """,
            (normalized_id,),
        )
        if row is not None:
            return row_to_kaizen_detail(row)

        for candidate in self._load_rows():
            if row_legacy_sheet_id(candidate) == normalized_id:
                return row_to_kaizen_detail(candidate)

        return None

    def list_active_kaizen_details(self) -> list[KaizenDetail]:
        return [row_to_kaizen_detail(row) for row in self._load_rows()]
