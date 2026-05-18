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
from app.application.shared.period_resolution import (
    ResolvedPeriod,
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
    ppm_internal_consolidated: float | None = None
    ppm_external_consolidated: float | None = None


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

        snapshot = self._build_snapshot(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            branches_override=None,
        )
        self._cache[key] = snapshot
        return snapshot

    def get_snapshot_series(
        self,
        *,
        periods: list[ResolvedPeriod],
        branch: str | None = None,
    ) -> dict[str, QualityMetricsSnapshot]:
        result: dict[str, QualityMetricsSnapshot] = {}

        for period in periods:
            key = (period.start_date, period.end_date, branch)
            cached = self._cache.get(key)
            if cached is not None:
                result[period.competence] = cached
                continue

            snapshot = self._build_snapshot(
                start_date=period.start_date,
                end_date=period.end_date,
                branch=branch,
                branches_override=None,
            )
            self._cache[key] = snapshot
            result[period.competence] = snapshot

        return result

    def _build_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
        branches_override: list[str] | None,
    ) -> QualityMetricsSnapshot:
        if branch:
            branches = [branch]
        elif branches_override is not None:
            branches = branches_override
        else:
            branches = self._resolve_branches(
                start_date=start_date,
                end_date=end_date,
            )

        ppm_internal_consolidated = self._resolve_ppm(
            ppm_type="internal",
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        ppm_external_consolidated = self._resolve_ppm(
            ppm_type="external",
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        snapshots: list[QualityBranchSnapshot] = []

        for branch_code in branches:
            ppm_internal = self._resolve_ppm(
                ppm_type="internal",
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
            )

            ppm_external = self._resolve_ppm(
                ppm_type="external",
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
            )

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

        return QualityMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            branches=snapshots,
            ppm_internal_consolidated=(
                round(ppm_internal_consolidated, 2)
                if ppm_internal_consolidated is not None
                else 0.0
            ),
            ppm_external_consolidated=(
                round(ppm_external_consolidated, 2)
                if ppm_external_consolidated is not None
                else 0.0
            ),
        )

    def _resolve_ppm(
        self,
        *,
        ppm_type: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> float | None:
        use_case = (
            self._internal_ppm_use_case
            if ppm_type == "internal"
            else self._external_ppm_use_case
        )

        result = use_case.execute(
            PpmSummaryRequest(
                type=ppm_type,
                branch=branch,
                date_start=start_date,
                date_end=end_date,
            )
        )

        value = self._extract_first_number(result)

        if value is None:
            return 0.0

        return value

    def _resolve_branches(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> list[str]:
        branches: set[str] = set()

        try:
            internal_ppm_branches = self._internal_ppm_use_case.list_branches(
                ppm_type="internal",
                date_start=start_date,
                date_end=end_date,
            )
            branches.update(
                branch.strip()
                for branch in internal_ppm_branches
                if branch and branch.strip()
            )
        except Exception:
            pass

        try:
            external_ppm_branches = self._external_ppm_use_case.list_branches(
                ppm_type="external",
                date_start=start_date,
                date_end=end_date,
            )
            branches.update(
                branch.strip()
                for branch in external_ppm_branches
                if branch and branch.strip()
            )
        except Exception:
            pass

        try:
            kaizen_summary = self._kaizen_summary_use_case.execute(
                KaizenSummaryRequest(
                    title=None,
                    status=None,
                    date_start=start_date,
                    date_end=end_date,
                    branch=None,
                )
            )

            branches.update(
                (item.branch or "").strip()
                for item in kaizen_summary.list_kaizen
                if (item.branch or "").strip()
            )
        except Exception:
            pass

        try:
            audit_summary = self._audit_5s_summary_use_case.execute(
                Audit5SSummaryRequest(
                    start_date=start_date,
                    end_date=end_date,
                    branch=None,
                )
            )

            branches.update(
                (item.branch or "").strip()
                for item in audit_summary.list_audits
                if (item.branch or "").strip()
            )
        except Exception:
            pass

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