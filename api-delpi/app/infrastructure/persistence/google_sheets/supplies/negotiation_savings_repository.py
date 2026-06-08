from __future__ import annotations

from collections import defaultdict
from typing import Optional

from app.application.dto.supplies.negotiation_savings_summary_request import (
    NegotiationSavingsSummaryRequest,
)
from app.application.dto.supplies.negotiation_savings_summary_response import (
    NegotiationSavingsBranchSummary,
    NegotiationSavingsEntry,
    NegotiationSavingsSummaryResponse,
)
from app.application.services.strategic_indicators.dashboard_goal_dates import (
    normalize_si_branch,
)
from app.domain.ports.supplies.negotiation_savings_query_repository_port import (
    NegotiationSavingsQueryRepositoryPort,
)
from app.infrastructure.persistence.google_sheets.utils import Utils
from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)
from delpi_domain.spreadsheet_date import parse_spreadsheet_date


class NegotiationSavingsRepository(NegotiationSavingsQueryRepositoryPort):
    def __init__(
        self,
        client: GoogleSheetsClient,
        sheet_id: str,
        gid: str,
        utils: Utils,
    ) -> None:
        self.client = client
        self.sheet_id = sheet_id
        self.gid = gid
        self.utils = utils

    def _is_deleted(self, value: object) -> bool:
        if value is None:
            return False
        normalized = str(value).strip().lower()
        return normalized in {"true", "1", "sim", "yes", "x"}

    def _normalize_branch(self, value: object) -> str | None:
        if value is None:
            return None
        raw = str(value).strip()
        if not raw:
            return None
        return normalize_si_branch(raw)

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

    def _map_row(self, row: dict) -> NegotiationSavingsEntry | None:
        branch = self._normalize_branch(row.get("filial"))
        entry_date = self.utils.empty_to_none(row.get("data"))
        savings_amount = self.utils.to_float(row.get("economia_reais"))

        if not branch or not entry_date or savings_amount is None:
            return None

        return NegotiationSavingsEntry(
            branch=branch,
            date=entry_date,
            savings_amount=round(savings_amount, 2),
        )

    def get_summary(
        self,
        request: NegotiationSavingsSummaryRequest,
    ) -> NegotiationSavingsSummaryResponse:
        self.utils.validate_date_range(
            start_date_str=request.start_date,
            end_date_str=request.end_date,
        )

        rows = self.client.read_csv_rows(
            sheet_id=self.sheet_id,
            gid=self.gid,
        )

        entries: list[NegotiationSavingsEntry] = []
        for row in rows:
            if self._is_deleted(row.get("deleted")):
                continue

            entry = self._map_row(row)
            if entry is None:
                continue

            if not self._is_in_date_range(
                entry.date,
                request.start_date,
                request.end_date,
            ):
                continue

            if request.branch and entry.branch != request.branch:
                continue

            entries.append(entry)

        totals_by_branch: dict[str, float] = defaultdict(float)
        for entry in entries:
            totals_by_branch[entry.branch] += entry.savings_amount

        branch_summaries = [
            NegotiationSavingsBranchSummary(
                branch=branch_code,
                total_savings=round(total, 2),
            )
            for branch_code, total in sorted(totals_by_branch.items())
        ]

        if request.branch:
            branch_total = totals_by_branch.get(request.branch)
            total_savings = round(branch_total, 2) if branch_total is not None else None
        else:
            if not totals_by_branch:
                total_savings = None
            else:
                total_savings = round(sum(totals_by_branch.values()), 2)

        return NegotiationSavingsSummaryResponse(
            start_date=request.start_date,
            end_date=request.end_date,
            branch=request.branch,
            total_savings=total_savings,
            branches=branch_summaries,
            entries=entries,
        )
