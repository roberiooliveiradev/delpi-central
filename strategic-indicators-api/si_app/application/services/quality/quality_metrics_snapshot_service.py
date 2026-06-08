from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
    _parse_dashboard_date_parts,
)
from si_app.infrastructure.gateways.delpi_quality_gateway import DelpiQualityGateway


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
        quality_gateway: DelpiQualityGateway,
    ) -> None:
        self._quality_gateway = quality_gateway
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

            kaizen_summary = self._quality_gateway.get_kaizen_summary(
                branch=branch_code,
                date_start=start_date,
                date_end=end_date,
            )

            audit_summary = self._quality_gateway.get_audit_5s_summary(
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
            )

            months = self._resolve_month_count(
                start_date=start_date,
                end_date=end_date,
            )

            total_kaizens = int(kaizen_summary.get("total_kaizens") or 0)
            kaizen_ideas_avg = (
                round(total_kaizens / months, 2)
                if months > 0
                else None
            )

            snapshots.append(
                QualityBranchSnapshot(
                    branch=branch_code,
                    ppm_internal=round(ppm_internal, 2) if ppm_internal is not None else None,
                    ppm_external=round(ppm_external, 2) if ppm_external is not None else None,
                    kaizen_ideas_avg=kaizen_ideas_avg,
                    kaizen_financial_gain=round(
                        float(kaizen_summary.get("total_savings") or 0),
                        2,
                    ),
                    audit_5s_score=round(
                        float(audit_summary.get("average_score") or 0),
                        2,
                    ),
                )
            )

        return QualityMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            branches=snapshots,
            ppm_internal_consolidated=(
                round(ppm_internal_consolidated, 2)
                if ppm_internal_consolidated is not None
                else None
            ),
            ppm_external_consolidated=(
                round(ppm_external_consolidated, 2)
                if ppm_external_consolidated is not None
                else None
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
        if ppm_type not in {"internal", "external"}:
            raise ValueError("ppm_type deve ser internal ou external")

        result = self._quality_gateway.get_ppm_summary(
            ppm_type=ppm_type,
            branch=branch,
            date_start=start_date,
            date_end=end_date,
        )

        value = self._extract_first_number(result)

        return value

    def _resolve_branches(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> list[str]:
        branches: set[str] = set()

        for ppm_type in ("internal", "external"):
            try:
                ppm_branches = self._quality_gateway.list_branches(
                    ppm_type=ppm_type,
                    date_start=start_date,
                    date_end=end_date,
                )
                branches.update(
                    branch.strip()
                    for branch in ppm_branches
                    if branch and branch.strip()
                )
            except Exception:
                pass

        try:
            kaizen_summary = self._quality_gateway.get_kaizen_summary(
                branch=None,
                date_start=start_date,
                date_end=end_date,
            )

            branches.update(
                str(item.get("branch") or "").strip()
                for item in (kaizen_summary.get("list_kaizen") or [])
                if str(item.get("branch") or "").strip()
            )
        except Exception:
            pass

        try:
            audit_summary = self._quality_gateway.get_audit_5s_summary(
                branch=None,
                start_date=start_date,
                end_date=end_date,
            )

            branches.update(
                str(item.get("branch") or "").strip()
                for item in (audit_summary.get("list_audits") or [])
                if str(item.get("branch") or "").strip()
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

    @staticmethod
    def _parse_dashboard_date(value: str | None) -> date | None:
        if not value:
            return None
        parts = _parse_dashboard_date_parts(value.strip())
        if parts is None:
            return None
        day, month, year = parts
        return date(year, month, day)

    def _resolve_month_count(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> int:
        if not start_date or not end_date:
            return 1

        start = self._parse_dashboard_date(start_date)
        end = self._parse_dashboard_date(end_date)

        if not start or not end:
            return 1

        return ((end.year - start.year) * 12) + (end.month - start.month) + 1
