from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.application.use_cases.audit_5s.get_audit_5s_summary_use_case import (
    GetAudit5SSummaryUseCase,
)
from app.application.use_cases.kaizen.get_kaizen_summary_use_case import (
    GetKaizenSummaryUseCase,
)
from app.application.use_cases.ppm.get_ppm_summary_use_case import (
    GetPpmSummaryUseCase,
)


@dataclass(frozen=True)
class QualityBranchSnapshot:
    branch: str
    ppm_internal: float | None
    ppm_external: float | None
    kaizen_ideas_avg: float | None
    kaizen_financial_gain: float | None
    audit_5s_score: float | None


@dataclass(frozen=True)
class QualityMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    branches: list[QualityBranchSnapshot]


class QualityMetricsSnapshotService:
    def __init__(
        self,
        *,
        internal_ppm_use_case: GetPpmSummaryUseCase,
        external_ppm_use_case: GetPpmSummaryUseCase,
        kaizen_summary_use_case: GetKaizenSummaryUseCase,
        audit_5s_summary_use_case: GetAudit5SSummaryUseCase,
    ) -> None:
        self._internal_ppm_use_case = internal_ppm_use_case
        self._external_ppm_use_case = external_ppm_use_case
        self._kaizen_summary_use_case = kaizen_summary_use_case
        self._audit_5s_summary_use_case = audit_5s_summary_use_case
        self._cache: dict[
            tuple[str | None, str | None, str | None],
            QualityMetricsSnapshot,
        ] = {}

    def get_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None = None,
    ) -> QualityMetricsSnapshot:
        key = (start_date, end_date, branch)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        if branch:
            branches = [branch]
        else:
            branches = self._resolve_branches(
                start_date=start_date,
                end_date=end_date,
            )

        snapshots: list[QualityBranchSnapshot] = []

        for branch_code in branches:

            ppm_internal = self._extract_first_number(
                self._internal_ppm_use_case.execute(
                    PpmSummaryRequest(
                        type="internal",
                        branch=branch_code,
                        date_start=start_date,
                        date_end=end_date,
                    )
                )
            )
            if ppm_internal is None:
                ppm_internal = 0.0

            ppm_external = self._extract_first_number(
                self._external_ppm_use_case.execute(
                    PpmSummaryRequest(
                        type="external",
                        branch=branch_code,
                        date_start=start_date,
                        date_end=end_date,
                    )
                )
            )
            if ppm_external is None:
                ppm_external = 0.0

            kaizen_summary = self._kaizen_summary_use_case.execute(
                KaizenSummaryRequest(
                    title=None,
                    status=None,
                    date_start=start_date,
                    date_end=end_date,
                    branch=branch_code,
                )
            )

            audit_summary = self._audit_5s_summary_use_case.execute(
                Audit5SSummaryRequest(
                    start_date=start_date,
                    end_date=end_date,
                    branch=branch_code,
                )
            )

            months = self._resolve_month_count(
                start_date=start_date,
                end_date=end_date,
            )

            kaizen_ideas_avg = (
                round(kaizen_summary.total_kaizens / months, 2)
                if months > 0
                else None
            )

            snapshots.append(
                QualityBranchSnapshot(
                    branch=branch_code,
                    ppm_internal=round(ppm_internal, 2) if ppm_internal is not None else None,
                    ppm_external=round(ppm_external, 2) if ppm_external is not None else None,
                    kaizen_ideas_avg=kaizen_ideas_avg,
                    kaizen_financial_gain=round(kaizen_summary.total_savings, 2),
                    audit_5s_score=round(audit_summary.average_score, 2),
                )
            )

        snapshot = QualityMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            branches=snapshots,
        )
        self._cache[key] = snapshot
        return snapshot

    def _resolve_branches(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> list[str]:
        kaizen_summary = self._kaizen_summary_use_case.execute(
            KaizenSummaryRequest(
                title=None,
                status=None,
                date_start=start_date,
                date_end=end_date,
                branch=None,
            )
        )
        audit_summary = self._audit_5s_summary_use_case.execute(
            Audit5SSummaryRequest(
                start_date=start_date,
                end_date=end_date,
                branch=None,
            )
        )

        branches = {
            (item.branch or "").strip()
            for item in kaizen_summary.list_kaizen
            if (item.branch or "").strip()
        }

        branches.update(
            {
                (item.branch or "").strip()
                for item in audit_summary.list_audits
                if (item.branch or "").strip()
            }
        )

        return sorted(branches)

    def _extract_first_number(self, result) -> float | None:
        payload = result.to_dict() if hasattr(result, "to_dict") else result
        data = payload.get("data", payload)

        candidates = [
            "ppm",
            "ppm_value",
            "ppm_internal",
            "ppm_external",
            "internal_ppm",
            "external_ppm",
            "total_ppm",
            "ppm_summary",
        ]

        for key in candidates:
            value = data.get(key)
            if value is None:
                continue
            try:
                return float(value)
            except (TypeError, ValueError):
                continue

        return None

    def _resolve_month_count(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> int:
        if not start_date or not end_date:
            return 1

        from app.shared.utils.spreadsheet_date import parse_spreadsheet_date

        start = parse_spreadsheet_date(start_date)
        end = parse_spreadsheet_date(end_date)

        if not start or not end:
            return 1

        return ((end.year - start.year) * 12) + (end.month - start.month) + 1