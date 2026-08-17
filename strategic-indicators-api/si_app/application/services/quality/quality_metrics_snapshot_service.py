from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
    _parse_dashboard_date_parts,
)
from si_app.infrastructure.gateways.delpi_quality_gateway import DelpiQualityGateway

PLUGS_FINISHED_PRODUCT_PREFIX = "9048"
COMPONENTS_FINISHED_PRODUCT_PREFIX = "9026"


@dataclass(frozen=True)
class QualityBranchSnapshot:
    branch: str
    ppm_internal: float | None
    ppm_external: float | None
    kaizen_ideas_avg: float | None
    kaizen_financial_gain: float | None
    audit_5s_score: float | None
    ppm_internal_plugs: float | None = None
    ppm_external_plugs: float | None = None
    ppm_internal_components: float | None = None
    ppm_external_components: float | None = None
    scrap_cost_pct: float | None = None
    rework_cost_pct: float | None = None


@dataclass(frozen=True)
class QualityMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    branches: list[QualityBranchSnapshot]
    ppm_internal_consolidated: float | None = None
    ppm_external_consolidated: float | None = None
    ppm_internal_plugs_consolidated: float | None = None
    ppm_external_plugs_consolidated: float | None = None
    ppm_internal_components_consolidated: float | None = None
    ppm_external_components_consolidated: float | None = None
    scrap_cost_pct_consolidated: float | None = None
    rework_cost_pct_consolidated: float | None = None


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
        self._ppm_series_lookup: dict[
            tuple[str, str | None, str | None, str],
            float | None,
        ] | None = None
        self._cost_series_lookup: dict[
            tuple[str, str | None, str],
            float | None,
        ] | None = None
        self._kaizen_series_lookup: dict[
            tuple[str | None, str],
            dict[str, float | int | None],
        ] | None = None
        self._audit_series_lookup: dict[
            tuple[str | None, str],
            float | None,
        ] | None = None

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
        if not periods:
            return result

        overall_start = periods[0].start_date
        overall_end = periods[-1].end_date
        if branch:
            branch_codes = [branch]
        else:
            # Só PPM branches — evita 1× kaizen/5s summary só para descobrir filiais
            # (series já cobrem essas métricas na janela).
            branch_codes = self._resolve_branches_from_ppm(
                start_date=overall_start,
                end_date=overall_end,
            ) or ["01", "02"]

        self._ppm_series_lookup = self._prefetch_ppm_series(
            start_date=overall_start,
            end_date=overall_end,
            query_branch=branch,
            branch_codes=branch_codes,
        )
        self._cost_series_lookup = self._prefetch_cost_series(
            start_date=overall_start,
            end_date=overall_end,
            query_branch=branch,
            branch_codes=branch_codes,
        )
        self._kaizen_series_lookup = self._prefetch_kaizen_series(
            start_date=overall_start,
            end_date=overall_end,
            query_branch=branch,
            branch_codes=branch_codes,
        )
        self._audit_series_lookup = self._prefetch_audit_series(
            start_date=overall_start,
            end_date=overall_end,
            query_branch=branch,
            branch_codes=branch_codes,
        )
        try:
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
                    branches_override=branch_codes if branch is None else None,
                )
                self._cache[key] = snapshot
                result[period.competence] = snapshot
        finally:
            self._ppm_series_lookup = None
            self._cost_series_lookup = None
            self._kaizen_series_lookup = None
            self._audit_series_lookup = None

        return result

    def _prefetch_ppm_series(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        query_branch: str | None,
        branch_codes: list[str],
    ) -> dict[tuple[str, str | None, str | None, str], float | None]:
        """Indexa PPM por (type, product_prefix, branch, competence YYYY-MM)."""
        lookup: dict[tuple[str, str | None, str | None, str], float | None] = {}
        prefixes: tuple[str | None, ...] = (
            None,
            PLUGS_FINISHED_PRODUCT_PREFIX,
            COMPONENTS_FINISHED_PRODUCT_PREFIX,
        )
        scopes: list[str | None] = [query_branch]
        if query_branch is None:
            scopes.extend(branch_codes)

        seen_scopes: list[str | None] = []
        for scope in scopes:
            if scope not in seen_scopes:
                seen_scopes.append(scope)

        for ppm_type in ("internal", "external"):
            for product_prefix in prefixes:
                for scope in seen_scopes:
                    payload = self._quality_gateway.get_ppm_series(
                        ppm_type=ppm_type,
                        branch=scope,
                        date_start=start_date,
                        date_end=end_date,
                        product_prefix=product_prefix,
                    )
                    for point in self._iter_ppm_series_points(payload):
                        competence = self._competence_from_ppm_point(point)
                        if not competence:
                            continue
                        lookup[
                            (ppm_type, product_prefix, scope, competence)
                        ] = self._ppm_value_from_point(point)
        return lookup

    def _prefetch_cost_series(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        query_branch: str | None,
        branch_codes: list[str],
    ) -> dict[tuple[str, str | None, str], float | None]:
        lookup: dict[tuple[str, str | None, str], float | None] = {}
        scopes: list[str | None] = [query_branch]
        if query_branch is None:
            scopes.extend(branch_codes)
        seen: list[str | None] = []
        for scope in scopes:
            if scope not in seen:
                seen.append(scope)

        for scope in seen:
            scrap = self._quality_gateway.get_scrap_cost_pct_series(
                branch=scope,
                date_start=start_date,
                date_end=end_date,
            )
            rework = self._quality_gateway.get_rework_cost_pct_series(
                branch=scope,
                date_start=start_date,
                date_end=end_date,
            )
            for point in self._iter_ppm_series_points(scrap):
                competence = self._competence_from_ppm_point(point)
                if not competence:
                    continue
                metrics = point.get("metrics") or {}
                raw = metrics.get("scrap_cost_pct")
                lookup[("scrap", scope, competence)] = (
                    float(raw) if raw is not None else None
                )
            for point in self._iter_ppm_series_points(rework):
                competence = self._competence_from_ppm_point(point)
                if not competence:
                    continue
                metrics = point.get("metrics") or {}
                raw = metrics.get("rework_cost_pct")
                lookup[("rework", scope, competence)] = (
                    float(raw) if raw is not None else None
                )
        return lookup

    def _branch_series_scopes(
        self,
        *,
        query_branch: str | None,
        branch_codes: list[str],
    ) -> list[str | None]:
        if query_branch:
            return [query_branch]
        return list(branch_codes)

    def _prefetch_kaizen_series(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        query_branch: str | None,
        branch_codes: list[str],
    ) -> dict[tuple[str | None, str], dict[str, float | int | None]]:
        lookup: dict[tuple[str | None, str], dict[str, float | int | None]] = {}
        for scope in self._branch_series_scopes(
            query_branch=query_branch,
            branch_codes=branch_codes,
        ):
            payload = self._quality_gateway.get_kaizen_summary_series(
                branch=scope,
                date_start=start_date,
                date_end=end_date,
            )
            for point in self._iter_ppm_series_points(payload):
                competence = self._competence_from_ppm_point(point)
                if not competence:
                    continue
                metrics = point.get("metrics") or {}
                lookup[(scope, competence)] = {
                    "total_kaizens": metrics.get("total_kaizens"),
                    "total_savings": metrics.get("total_savings"),
                }
        return lookup

    def _prefetch_audit_series(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        query_branch: str | None,
        branch_codes: list[str],
    ) -> dict[tuple[str | None, str], float | None]:
        lookup: dict[tuple[str | None, str], float | None] = {}
        for scope in self._branch_series_scopes(
            query_branch=query_branch,
            branch_codes=branch_codes,
        ):
            payload = self._quality_gateway.get_audit_5s_summary_series(
                branch=scope,
                start_date=start_date,
                end_date=end_date,
            )
            for point in self._iter_ppm_series_points(payload):
                competence = self._competence_from_ppm_point(point)
                if not competence:
                    continue
                metrics = point.get("metrics") or {}
                raw = metrics.get("average_score")
                lookup[(scope, competence)] = (
                    float(raw) if raw is not None else None
                )
        return lookup

    def _iter_ppm_series_points(self, payload: object) -> list[dict]:
        data = payload.to_dict() if hasattr(payload, "to_dict") else payload
        if not isinstance(data, dict):
            return []
        body = data.get("data", data)
        if not isinstance(body, dict):
            return []
        points = body.get("points") or []
        return [p for p in points if isinstance(p, dict)]

    def _competence_from_ppm_point(self, point: dict) -> str | None:
        sort_key = str(point.get("sort_key") or "").strip()
        if len(sort_key) >= 7 and sort_key[4] == "-":
            return sort_key[:7]
        start = str(point.get("start_date") or "").strip()
        parts = _parse_dashboard_date_parts(start) if start else None
        if parts:
            _day, month, year = parts
            return f"{year}-{str(month).zfill(2)}"
        return None

    def _ppm_value_from_point(self, point: dict) -> float | None:
        raw = point.get("ppm")
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    def _competence_for_period_dates(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> str | None:
        for value in (end_date, start_date):
            if not value:
                continue
            parts = _parse_dashboard_date_parts(value)
            if parts:
                _day, month, year = parts
                return f"{year}-{str(month).zfill(2)}"
        return None

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

        # Com filial explícita, o bloco "consolidado" com o mesmo branch
        # duplicava PPM/custo — preenche só no loop e espelha no fim.
        fetch_consolidated_block = branch is None

        ppm_internal_consolidated = None
        ppm_external_consolidated = None
        ppm_internal_plugs_consolidated = None
        ppm_external_plugs_consolidated = None
        ppm_internal_components_consolidated = None
        ppm_external_components_consolidated = None
        scrap_cost_pct_consolidated = None
        rework_cost_pct_consolidated = None

        if fetch_consolidated_block:
            ppm_internal_consolidated = self._resolve_ppm(
                ppm_type="internal",
                branch=None,
                start_date=start_date,
                end_date=end_date,
            )
            ppm_external_consolidated = self._resolve_ppm(
                ppm_type="external",
                branch=None,
                start_date=start_date,
                end_date=end_date,
            )
            ppm_internal_plugs_consolidated = self._resolve_ppm(
                ppm_type="internal",
                branch=None,
                start_date=start_date,
                end_date=end_date,
                product_prefix=PLUGS_FINISHED_PRODUCT_PREFIX,
            )
            ppm_external_plugs_consolidated = self._resolve_ppm(
                ppm_type="external",
                branch=None,
                start_date=start_date,
                end_date=end_date,
                product_prefix=PLUGS_FINISHED_PRODUCT_PREFIX,
            )
            ppm_internal_components_consolidated = self._resolve_ppm(
                ppm_type="internal",
                branch=None,
                start_date=start_date,
                end_date=end_date,
                product_prefix=COMPONENTS_FINISHED_PRODUCT_PREFIX,
            )
            ppm_external_components_consolidated = self._resolve_ppm(
                ppm_type="external",
                branch=None,
                start_date=start_date,
                end_date=end_date,
                product_prefix=COMPONENTS_FINISHED_PRODUCT_PREFIX,
            )
            scrap_cost_pct_consolidated = self._resolve_cost_pct(
                kind="scrap",
                branch=None,
                start_date=start_date,
                end_date=end_date,
            )
            rework_cost_pct_consolidated = self._resolve_cost_pct(
                kind="rework",
                branch=None,
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

            ppm_internal_plugs = self._resolve_ppm(
                ppm_type="internal",
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
                product_prefix=PLUGS_FINISHED_PRODUCT_PREFIX,
            )

            ppm_external_plugs = self._resolve_ppm(
                ppm_type="external",
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
                product_prefix=PLUGS_FINISHED_PRODUCT_PREFIX,
            )

            ppm_internal_components = self._resolve_ppm(
                ppm_type="internal",
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
                product_prefix=COMPONENTS_FINISHED_PRODUCT_PREFIX,
            )

            ppm_external_components = self._resolve_ppm(
                ppm_type="external",
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
                product_prefix=COMPONENTS_FINISHED_PRODUCT_PREFIX,
            )

            scrap_cost_pct = self._resolve_cost_pct(
                kind="scrap",
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
            )
            rework_cost_pct = self._resolve_cost_pct(
                kind="rework",
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
            )

            kaizen_summary = self._resolve_kaizen_summary(
                branch=branch_code,
                start_date=start_date,
                end_date=end_date,
            )
            audit_score = self._resolve_audit_score(
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
                        float(audit_score or 0),
                        2,
                    ),
                    ppm_internal_plugs=(
                        round(ppm_internal_plugs, 2)
                        if ppm_internal_plugs is not None
                        else None
                    ),
                    ppm_external_plugs=(
                        round(ppm_external_plugs, 2)
                        if ppm_external_plugs is not None
                        else None
                    ),
                    ppm_internal_components=(
                        round(ppm_internal_components, 2)
                        if ppm_internal_components is not None
                        else None
                    ),
                    ppm_external_components=(
                        round(ppm_external_components, 2)
                        if ppm_external_components is not None
                        else None
                    ),
                    scrap_cost_pct=(
                        round(scrap_cost_pct, 4)
                        if scrap_cost_pct is not None
                        else None
                    ),
                    rework_cost_pct=(
                        round(rework_cost_pct, 4)
                        if rework_cost_pct is not None
                        else None
                    ),
                )
            )

        if not fetch_consolidated_block and snapshots:
            only = snapshots[0]
            ppm_internal_consolidated = only.ppm_internal
            ppm_external_consolidated = only.ppm_external
            ppm_internal_plugs_consolidated = only.ppm_internal_plugs
            ppm_external_plugs_consolidated = only.ppm_external_plugs
            ppm_internal_components_consolidated = only.ppm_internal_components
            ppm_external_components_consolidated = only.ppm_external_components
            scrap_cost_pct_consolidated = only.scrap_cost_pct
            rework_cost_pct_consolidated = only.rework_cost_pct

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
            ppm_internal_plugs_consolidated=(
                round(ppm_internal_plugs_consolidated, 2)
                if ppm_internal_plugs_consolidated is not None
                else None
            ),
            ppm_external_plugs_consolidated=(
                round(ppm_external_plugs_consolidated, 2)
                if ppm_external_plugs_consolidated is not None
                else None
            ),
            ppm_internal_components_consolidated=(
                round(ppm_internal_components_consolidated, 2)
                if ppm_internal_components_consolidated is not None
                else None
            ),
            ppm_external_components_consolidated=(
                round(ppm_external_components_consolidated, 2)
                if ppm_external_components_consolidated is not None
                else None
            ),
            scrap_cost_pct_consolidated=(
                round(scrap_cost_pct_consolidated, 4)
                if scrap_cost_pct_consolidated is not None
                else None
            ),
            rework_cost_pct_consolidated=(
                round(rework_cost_pct_consolidated, 4)
                if rework_cost_pct_consolidated is not None
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
        product_prefix: str | None = None,
    ) -> float | None:
        if ppm_type not in {"internal", "external"}:
            raise ValueError("ppm_type deve ser internal ou external")

        if self._ppm_series_lookup is not None:
            competence = self._competence_for_period_dates(
                start_date=start_date,
                end_date=end_date,
            )
            if competence:
                key = (ppm_type, product_prefix, branch, competence)
                if key in self._ppm_series_lookup:
                    return self._ppm_series_lookup[key]

        result = self._quality_gateway.get_ppm_summary(
            ppm_type=ppm_type,
            branch=branch,
            date_start=start_date,
            date_end=end_date,
            product_prefix=product_prefix,
        )

        value = self._extract_first_number(result)

        return value

    def _resolve_cost_pct(
        self,
        *,
        kind: str,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> float | None:
        if self._cost_series_lookup is not None:
            competence = self._competence_for_period_dates(
                start_date=start_date,
                end_date=end_date,
            )
            if competence:
                key = (kind, branch, competence)
                if key in self._cost_series_lookup:
                    return self._cost_series_lookup[key]

        if kind == "scrap":
            result = self._quality_gateway.get_scrap_cost_pct(
                branch=branch,
                date_start=start_date,
                date_end=end_date,
            )
            field = "scrap_cost_pct"
        elif kind == "rework":
            result = self._quality_gateway.get_rework_cost_pct(
                branch=branch,
                date_start=start_date,
                date_end=end_date,
            )
            field = "rework_cost_pct"
        else:
            raise ValueError("kind deve ser scrap ou rework")

        return self._extract_named_number(result, field)

    def _resolve_kaizen_summary(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> dict[str, float | int | None]:
        if self._kaizen_series_lookup is not None:
            competence = self._competence_for_period_dates(
                start_date=start_date,
                end_date=end_date,
            )
            if competence:
                key = (branch, competence)
                if key in self._kaizen_series_lookup:
                    return dict(self._kaizen_series_lookup[key])

        return self._quality_gateway.get_kaizen_summary(
            branch=branch,
            date_start=start_date,
            date_end=end_date,
        )

    def _resolve_audit_score(
        self,
        *,
        branch: str | None,
        start_date: str | None,
        end_date: str | None,
    ) -> float | None:
        if self._audit_series_lookup is not None:
            competence = self._competence_for_period_dates(
                start_date=start_date,
                end_date=end_date,
            )
            if competence:
                key = (branch, competence)
                if key in self._audit_series_lookup:
                    return self._audit_series_lookup[key]

        audit_summary = self._quality_gateway.get_audit_5s_summary(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        raw = audit_summary.get("average_score")
        return float(raw) if raw is not None else None

    def _resolve_branches_from_ppm(
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
        return sorted(branches)

    def _resolve_branches(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> list[str]:
        branches: set[str] = set(
            self._resolve_branches_from_ppm(
                start_date=start_date,
                end_date=end_date,
            )
        )

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

    def _extract_named_number(self, result, field: str) -> float | None:
        payload = result.to_dict() if hasattr(result, "to_dict") else result
        data = payload.get("data", payload) if isinstance(payload, dict) else {}
        if not isinstance(data, dict):
            return None
        value = data.get(field)
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
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
