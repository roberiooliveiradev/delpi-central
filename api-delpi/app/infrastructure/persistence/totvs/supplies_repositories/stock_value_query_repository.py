from datetime import datetime, timedelta

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.services.supplies.stock_value_cache import (
    get_cached_stock_value_bundle,
    set_cached_stock_value_bundle,
    stock_value_cache_key,
)
from app.application.services.supplies.stock_value_method_service import (
    STOCK_METHOD_ESTIMATED,
    STOCK_METHOD_RESOLVED_ESTIMATED,
    STOCK_METHOD_RESOLVED_MIXED,
    STOCK_METHOD_RESOLVED_OFFICIAL,
    STOCK_METHOD_RESOLVED_REGISTER_SNAPSHOT,
    normalize_stock_method,
    resolve_stock_method_plan,
)
from app.application.services.supplies.stock_value_hybrid_content_service import (
    process_warehouse_locations,
)
from app.application.services.supplies.stock_value_register_snapshot_service import (
    build_register_snapshot_estimation_meta,
)
from app.domain.ports.supplies.stock_value_query_repository_port import (
    StockValueQueryRepositoryPort,
)
from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_historical_sql import (
    HistoricalStockFilterClauses,
    build_historical_method_breakdown_params,
    build_historical_stock_params,
    format_historical_breakdown_sql,
    format_historical_method_breakdown_sql,
    format_historical_stock_sql,
)
from app.infrastructure.persistence.totvs.supplies_repositories.stock_value_official_closure_sql import (
    OfficialClosureFilterClauses,
    build_official_closure_params,
    format_official_closure_sql,
)

_DEFAULT_STOCK_BRANCHES = ("01", "02")


class StockValueQueryRepository(BaseRepository, StockValueQueryRepositoryPort):

    def _uses_historical_estimation(self, request: GetStockValueRequest) -> bool:
        return request.uses_historical_estimation

    def _resolve_historical_period(
        self,
        request: GetStockValueRequest,
    ) -> tuple[str, str, str]:
        qb = QueryBuilder()
        period_start = qb.convert_date_to_protheus(request.start_date)
        period_end = qb.convert_date_to_protheus(request.end_date)

        if not period_start or not period_end:
            raise ValueError(
                "Para consultar estoque em uma data passada, informe start_date e end_date válidos."
            )

        end_date = datetime.strptime(period_end, "%Y%m%d").date()
        period_end_exclusive = (end_date + timedelta(days=1)).strftime("%Y%m%d")
        return period_start, period_end, period_end_exclusive

    def _branch_filter_clause(self, column: str, branch: str | None) -> tuple[str, tuple]:
        if branch:
            return f" AND {column} = ?", (branch,)
        return "", ()

    def _location_filter_clause(self, column: str, location: str | None) -> tuple[str, tuple]:
        normalized = (location or "").strip()
        if normalized:
            return f" AND RTRIM({column}) = ?", (normalized,)
        return "", ()

    def _historical_filter_clauses(
        self,
        request: GetStockValueRequest,
    ) -> tuple[HistoricalStockFilterClauses, tuple, tuple, tuple, tuple, tuple, tuple]:
        branch = request.branch
        location = (request.location or "").strip() or None

        sb9_filter, sb9_params = self._branch_filter_clause("B9_FILIAL", branch)
        sb9_b9_filter, sb9_b9_params = self._branch_filter_clause("B9.B9_FILIAL", branch)
        sb9_official_filter, sb9_official_params = self._branch_filter_clause(
            "B9.B9_FILIAL",
            branch,
        )
        sb9_loc_filter, sb9_loc_params = self._location_filter_clause("B9.B9_LOCAL", location)
        d3_filter, d3_params = self._branch_filter_clause("D3.D3_FILIAL", branch)
        d3_loc_filter, d3_loc_params = self._location_filter_clause("D3.D3_LOCAL", location)

        filters = HistoricalStockFilterClauses(
            sb9_branch_filter=sb9_filter,
            sb9_branch_filter_b9=sb9_b9_filter,
            sb9_branch_filter_official=sb9_official_filter,
            sb9_location_filter=sb9_loc_filter,
            d3_branch_filter=d3_filter,
            d3_location_filter=d3_loc_filter,
        )
        return (
            filters,
            sb9_params,
            sb9_b9_params,
            sb9_official_params,
            sb9_loc_params,
            d3_params,
            d3_loc_params,
        )

    def _format_historical_bundle_sql(
        self,
        request: GetStockValueRequest,
    ) -> tuple[str, tuple]:
        period_start, period_end, period_end_exclusive = self._resolve_historical_period(request)
        (
            filters,
            sb9_params,
            sb9_b9_params,
            sb9_official_params,
            sb9_loc_params,
            d3_params,
            d3_loc_params,
        ) = self._historical_filter_clauses(request)

        sql = format_historical_stock_sql(
            summary_only=request.summary_only,
            filters=filters,
            top_limit=max(1, int(getattr(request, "top_limit", 10) or 10)),
        )
        params = build_historical_stock_params(
            period_start=period_start,
            period_end=period_end,
            period_end_exclusive=period_end_exclusive,
            sb9_params=sb9_params,
            sb9_b9_params=sb9_b9_params,
            sb9_official_params=sb9_official_params,
            sb9_loc_params=sb9_loc_params,
            d3_params=d3_params,
            d3_loc_params=d3_loc_params,
            include_breakdown_select=False,
        )
        return sql, params

    def _format_historical_breakdown_sql(
        self,
        request: GetStockValueRequest,
    ) -> tuple[str, tuple]:
        period_start, period_end, period_end_exclusive = self._resolve_historical_period(request)
        (
            filters,
            sb9_params,
            sb9_b9_params,
            sb9_official_params,
            sb9_loc_params,
            d3_params,
            d3_loc_params,
        ) = self._historical_filter_clauses(request)

        sql = format_historical_breakdown_sql(filters=filters)
        params = build_historical_stock_params(
            period_start=period_start,
            period_end=period_end,
            period_end_exclusive=period_end_exclusive,
            sb9_params=sb9_params,
            sb9_b9_params=sb9_b9_params,
            sb9_official_params=sb9_official_params,
            sb9_loc_params=sb9_loc_params,
            d3_params=d3_params,
            d3_loc_params=d3_loc_params,
            include_breakdown_select=True,
        )
        return sql, params

    def _format_historical_method_breakdown_sql(
        self,
        request: GetStockValueRequest,
    ) -> tuple[str, tuple]:
        period_start, period_end, _period_end_exclusive = self._resolve_historical_period(
            request
        )
        (
            filters,
            sb9_params,
            sb9_b9_params,
            _sb9_official_params,
            sb9_loc_params,
            _d3_params,
            _d3_loc_params,
        ) = self._historical_filter_clauses(request)

        sql = format_historical_method_breakdown_sql(filters=filters)
        params = build_historical_method_breakdown_params(
            period_start=period_start,
            period_end=period_end,
            sb9_params=sb9_params,
            sb9_b9_params=sb9_b9_params,
            sb9_loc_params=sb9_loc_params,
        )
        return sql, params

    def _should_fan_out_consolidated(self, request: GetStockValueRequest) -> bool:
        if (request.branch or "").strip():
            return False
        if (request.location or "").strip():
            return False
        if self._uses_historical_estimation(request):
            return True
        return request.summary_only

    def _branch_stock_request(
        self,
        request: GetStockValueRequest,
        branch: str,
    ) -> GetStockValueRequest:
        return GetStockValueRequest(
            branch=branch,
            location=request.location,
            start_date=request.start_date,
            end_date=request.end_date,
            top_limit=request.top_limit,
            summary_only=request.summary_only,
            stock_method=request.stock_method,
        )

    def _merge_consolidated_summary_bundle(
        self,
        branch_bundles: list[dict],
        *,
        branch_label: str,
        location_label: str,
    ) -> dict:
        summaries = [bundle.get("summary") or {} for bundle in branch_bundles]
        breakdown_rows = [
            row
            for bundle in branch_bundles
            for row in (bundle.get("estimation_meta") or {}).get("by_branch_breakdown") or []
        ]
        stock_method_resolved = self._resolve_consolidated_stock_method(branch_bundles)
        if stock_method_resolved == STOCK_METHOD_RESOLVED_REGISTER_SNAPSHOT:
            estimation_meta = self._merge_register_snapshot_estimation_meta(
                branch_bundles,
                breakdown_rows,
            )
        else:
            estimation_meta = self._build_estimation_meta(breakdown_rows)

        by_branch: list[dict] = []
        for bundle in branch_bundles:
            by_branch.extend(bundle.get("by_branch") or [])
        if not by_branch:
            by_branch = self._merge_branch_with_breakdown(
                [
                    {
                        "branch": summary.get("branch"),
                        "total_stock_value": float(summary.get("total_stock_value") or 0),
                        "total_stock_quantity": float(
                            summary.get("total_stock_quantity") or 0
                        ),
                        "total_records": int(summary.get("total_records") or 0),
                        "total_products": int(summary.get("total_products") or 0),
                        "total_locations": int(summary.get("total_locations") or 0),
                    }
                    for summary in summaries
                    if summary.get("branch")
                ],
                breakdown_rows,
            )

        return {
            "summary": {
                "branch": branch_label,
                "location": location_label,
                "total_stock_value": sum(
                    float(summary.get("total_stock_value") or 0) for summary in summaries
                ),
                "total_stock_quantity": sum(
                    float(summary.get("total_stock_quantity") or 0) for summary in summaries
                ),
                "total_records": sum(
                    int(summary.get("total_records") or 0) for summary in summaries
                ),
                "total_products": sum(
                    int(summary.get("total_products") or 0) for summary in summaries
                ),
                "total_locations": sum(
                    int(summary.get("total_locations") or 0) for summary in summaries
                ),
            },
            "by_branch": by_branch,
            "by_location": [],
            "top_products": [],
            "estimation_meta": estimation_meta,
            "stock_method_resolved": stock_method_resolved,
        }

    def _merge_register_snapshot_estimation_meta(
        self,
        branch_bundles: list[dict],
        breakdown_rows: list[dict],
    ) -> dict:
        snapshots = [
            (bundle.get("estimation_meta") or {}).get("register_snapshot") or {}
            for bundle in branch_bundles
        ]
        period_end = str(snapshots[0].get("period_end_requested") or "") if snapshots else ""
        em_estoque_value = sum(float(s.get("em_estoque_value") or 0) for s in snapshots)
        em_processo_proxy_value = sum(
            float(s.get("em_processo_proxy_value") or 0) for s in snapshots
        )
        by_branch_wip = [
            row
            for snapshot in snapshots
            for row in (snapshot.get("by_branch") or [])
        ]
        return build_register_snapshot_estimation_meta(
            period_end=period_end,
            breakdown_rows=breakdown_rows,
            em_estoque_value=em_estoque_value,
            em_processo_proxy_value=em_processo_proxy_value,
            by_branch_wip=by_branch_wip,
        )

    def _resolve_consolidated_stock_method(self, branch_bundles: list[dict]) -> str:
        resolved_methods = {
            bundle.get("stock_method_resolved")
            for bundle in branch_bundles
            if bundle.get("stock_method_resolved")
        }
        if len(resolved_methods) > 1:
            return STOCK_METHOD_RESOLVED_MIXED
        if resolved_methods == {STOCK_METHOD_RESOLVED_OFFICIAL}:
            return STOCK_METHOD_RESOLVED_OFFICIAL
        if resolved_methods == {STOCK_METHOD_RESOLVED_REGISTER_SNAPSHOT}:
            return STOCK_METHOD_RESOLVED_REGISTER_SNAPSHOT
        return STOCK_METHOD_RESOLVED_ESTIMATED

    def _merge_consolidated_full_bundle(
        self,
        branch_bundles: list[dict],
        *,
        branch_label: str,
        location_label: str,
        top_limit: int,
    ) -> dict:
        summary_bundle = self._merge_consolidated_summary_bundle(
            branch_bundles,
            branch_label=branch_label,
            location_label=location_label,
        )
        by_location: list[dict] = []
        top_products: list[dict] = []
        for bundle in branch_bundles:
            by_location.extend(bundle.get("by_location") or [])
            top_products.extend(bundle.get("top_products") or [])

        top_products = sorted(
            top_products,
            key=lambda row: (
                -float(row.get("total_stock_value") or 0),
                str(row.get("product_code") or ""),
            ),
        )[: max(1, top_limit)]

        resolved_methods = {
            bundle.get("stock_method_resolved")
            for bundle in branch_bundles
            if bundle.get("stock_method_resolved")
        }
        if len(resolved_methods) > 1:
            stock_method_resolved = STOCK_METHOD_RESOLVED_MIXED
        elif resolved_methods == {STOCK_METHOD_RESOLVED_OFFICIAL}:
            stock_method_resolved = STOCK_METHOD_RESOLVED_OFFICIAL
        elif resolved_methods == {STOCK_METHOD_RESOLVED_REGISTER_SNAPSHOT}:
            stock_method_resolved = STOCK_METHOD_RESOLVED_REGISTER_SNAPSHOT
        else:
            stock_method_resolved = STOCK_METHOD_RESOLVED_ESTIMATED

        return {
            **summary_bundle,
            "by_location": by_location,
            "top_products": top_products,
            "stock_method_resolved": stock_method_resolved,
        }

    def _fetch_consolidated_bundle(self, request: GetStockValueRequest) -> dict:
        branch_bundles = [
            self._fetch_branch_bundle(self._branch_stock_request(request, branch))
            for branch in _DEFAULT_STOCK_BRANCHES
        ]
        branch_label, location_label = self._labels(request)
        if request.summary_only:
            return self._merge_consolidated_summary_bundle(
                branch_bundles,
                branch_label=branch_label,
                location_label=location_label,
            )
        return self._merge_consolidated_full_bundle(
            branch_bundles,
            branch_label=branch_label,
            location_label=location_label,
            top_limit=max(1, int(getattr(request, "top_limit", 10) or 10)),
        )

    def _fetch_branch_bundle(self, request: GetStockValueRequest) -> dict:
        cache_key = stock_value_cache_key(request)
        cached = get_cached_stock_value_bundle(cache_key)
        if cached is not None:
            return cached

        if self._uses_historical_estimation(request):
            bundle = self._fetch_historical_bundle(request)
        else:
            bundle = self._fetch_current_bundle(request)

        set_cached_stock_value_bundle(cache_key, bundle)
        return bundle

    def _official_filter_clauses(
        self,
        request: GetStockValueRequest,
    ) -> tuple[OfficialClosureFilterClauses, tuple, tuple]:
        branch = request.branch
        location = (request.location or "").strip() or None
        sb9_b9_filter, sb9_b9_params = self._branch_filter_clause("B9.B9_FILIAL", branch)
        sb9_loc_filter, sb9_loc_params = self._location_filter_clause("B9.B9_LOCAL", location)
        return (
            OfficialClosureFilterClauses(
                sb9_branch_filter_b9=sb9_b9_filter,
                sb9_location_filter=sb9_loc_filter,
            ),
            sb9_b9_params,
            sb9_loc_params,
        )

    def _format_official_closure_bundle_sql(
        self,
        request: GetStockValueRequest,
    ) -> tuple[str, tuple]:
        _period_start, period_end, _period_end_exclusive = self._resolve_historical_period(
            request
        )
        filters, sb9_b9_params, sb9_loc_params = self._official_filter_clauses(request)
        sql = format_official_closure_sql(
            summary_only=request.summary_only,
            filters=filters,
            top_limit=max(1, int(getattr(request, "top_limit", 10) or 10)),
        )
        params = build_official_closure_params(
            period_end=period_end,
            sb9_b9_params=sb9_b9_params,
            sb9_loc_params=sb9_loc_params,
        )
        return sql, params

    def _build_official_estimation_meta(
        self,
        *,
        period_end: str,
        summary: dict,
    ) -> dict:
        total_value = float(summary.get("total_stock_value") or 0)
        return {
            "closing_base_date": None,
            "closing_base_value": None,
            "bridge_value": None,
            "period_net_value": None,
            "official_closure_available": True,
            "official_closure_date": period_end,
            "official_closure_value": total_value,
            "official_closure_on_period_end": True,
            "by_branch_breakdown": [],
        }

    def _fetch_official_closure_bundle(
        self,
        request: GetStockValueRequest,
        *,
        period_end: str,
        method_plan: dict,
    ) -> dict:
        sql, params = self._format_official_closure_bundle_sql(request)
        branch_label, location_label = self._labels(request)

        with self as repo:
            resultsets = repo.execute_query_multiple(sql, params)

        bundle = self._bundle_from_resultsets(
            resultsets,
            branch_label=branch_label,
            location_label=location_label,
        )
        bundle["stock_method_resolved"] = STOCK_METHOD_RESOLVED_OFFICIAL
        bundle["stock_method_plan"] = method_plan
        bundle["estimation_meta"] = self._build_official_estimation_meta(
            period_end=period_end,
            summary=bundle.get("summary") or {},
        )
        return bundle

    def _fetch_estimated_historical_bundle(
        self,
        request: GetStockValueRequest,
        *,
        method_plan: dict,
        breakdown_rows: list[dict] | None = None,
    ) -> dict:
        sql, params = self._format_historical_bundle_sql(request)
        branch_label, location_label = self._labels(request)
        if breakdown_rows is None:
            breakdown_rows = self._fetch_historical_breakdown_rows(request)

        with self as repo:
            resultsets = repo.execute_query_multiple(sql, params)

        datasets = [item.get("data") or [] for item in resultsets]
        summary_row = datasets[0][0] if datasets and datasets[0] else {}

        if request.summary_only:
            by_branch_seed: list[dict] = []
            if breakdown_rows and request.branch:
                by_branch_seed = [
                    {
                        "branch": request.branch,
                        "total_stock_value": float(summary_row.get("total_stock_value") or 0),
                        "total_stock_quantity": float(
                            summary_row.get("total_stock_quantity") or 0
                        ),
                        "total_records": int(summary_row.get("total_records") or 0),
                        "total_products": int(summary_row.get("total_products") or 0),
                        "total_locations": int(summary_row.get("total_locations") or 0),
                    }
                ]
            bundle = self._bundle_from_resultsets(
                [{"data": [summary_row]}, {"data": by_branch_seed}],
                branch_label=branch_label,
                location_label=location_label,
                breakdown_rows=breakdown_rows,
            )
        else:
            bundle = self._bundle_from_resultsets(
                resultsets,
                branch_label=branch_label,
                location_label=location_label,
                breakdown_rows=breakdown_rows,
            )

        bundle["stock_method_resolved"] = STOCK_METHOD_RESOLVED_ESTIMATED
        bundle["stock_method_plan"] = method_plan
        return bundle

    def _fetch_wip_proxy_rows(self, request: GetStockValueRequest) -> list[dict]:
        locations = process_warehouse_locations()
        if not locations:
            return []

        location_literals = ", ".join(f"'{loc}'" for loc in locations)
        where_clause, params = self._build_filters(request)
        sql = f"""
            SELECT
                SB2.B2_FILIAL AS branch,
                ISNULL(SUM(SB2.B2_VATU1), 0) AS em_estoque_value,
                ISNULL(
                    SUM(
                        CASE
                            WHEN RTRIM(SB2.B2_LOCAL) IN ({location_literals})
                            THEN SB2.B2_VATU1
                            ELSE 0
                        END
                    ),
                    0
                ) AS em_processo_proxy_value
            FROM SB2010 SB2 WITH (NOLOCK)
            WHERE {where_clause}
            GROUP BY SB2.B2_FILIAL
            ORDER BY SB2.B2_FILIAL
        """
        with self as repo:
            rows = repo.execute_query(sql, params)
        return [
            {
                "branch": str(row.get("branch") or "").strip(),
                "em_estoque_value": float(row.get("em_estoque_value") or 0),
                "em_processo_proxy_value": float(row.get("em_processo_proxy_value") or 0),
            }
            for row in rows
        ]

    def _fetch_register_snapshot_bundle(
        self,
        request: GetStockValueRequest,
        *,
        period_end: str,
        method_plan: dict,
        breakdown_rows: list[dict] | None = None,
    ) -> dict:
        breakdown_rows = breakdown_rows or self._fetch_historical_breakdown_rows(request)
        bundle = self._fetch_current_bundle(request)
        wip_rows = self._fetch_wip_proxy_rows(request)
        wip_by_branch = {row["branch"]: row for row in wip_rows}

        summary = bundle.get("summary") or {}
        em_estoque_value = float(summary.get("total_stock_value") or 0)
        em_processo_proxy_value = sum(
            row.get("em_processo_proxy_value") or 0 for row in wip_rows
        )

        by_branch_wip = []
        for row in bundle.get("by_branch") or []:
            branch = str(row.get("branch") or "").strip()
            wip = wip_by_branch.get(branch) or {}
            by_branch_wip.append(
                {
                    "branch": branch,
                    "em_estoque_value": float(
                        wip.get("em_estoque_value") or row.get("total_stock_value") or 0
                    ),
                    "em_processo_proxy_value": float(
                        wip.get("em_processo_proxy_value") or 0
                    ),
                }
            )

        bundle["stock_method_resolved"] = STOCK_METHOD_RESOLVED_REGISTER_SNAPSHOT
        bundle["stock_method_plan"] = method_plan
        bundle["estimation_meta"] = build_register_snapshot_estimation_meta(
            period_end=period_end,
            breakdown_rows=breakdown_rows,
            em_estoque_value=em_estoque_value,
            em_processo_proxy_value=em_processo_proxy_value,
            by_branch_wip=by_branch_wip,
        )
        return bundle

    def _build_filters(self, request: GetStockValueRequest):
        qb = QueryBuilder()
        qb.raw("SB2.D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("SB2.B2_FILIAL", request.branch)

        if request.location:
            qb.eq("SB2.B2_LOCAL", request.location)

        return qb.build()

    def _labels(self, request: GetStockValueRequest) -> tuple[str, str]:
        return request.branch or "consolidated", request.location or "all"

    def _normalize_summary_row(
        self,
        row: dict | None,
        *,
        branch_label: str,
        location_label: str,
    ) -> dict:
        row = row or {}
        return {
            "branch": branch_label,
            "location": location_label,
            "total_stock_value": float(row.get("total_stock_value") or 0),
            "total_stock_quantity": float(row.get("total_stock_quantity") or 0),
            "total_records": int(row.get("total_records") or 0),
            "total_products": int(row.get("total_products") or 0),
            "total_locations": int(row.get("total_locations") or 0),
        }

    def _normalize_branch_breakdown_row(self, row: dict) -> dict:
        return {
            "branch": row.get("branch"),
            "closing_base_date": row.get("closing_base_date") or None,
            "closing_base_value": float(row.get("closing_base_value") or 0),
            "bridge_value": float(row.get("bridge_value") or 0),
            "period_net_value": float(row.get("period_net_value") or 0),
            "official_closure_date": row.get("official_closure_date") or None,
            "official_closure_value": float(row.get("official_closure_value") or 0)
            if row.get("official_closure_value") not in (None, "")
            else None,
            "official_closure_available": bool(int(row.get("official_closure_available") or 0)),
            "official_closure_on_period_end": bool(
                int(row.get("official_closure_on_period_end") or 0)
            ),
        }

    def _merge_branch_with_breakdown(
        self,
        branch_rows: list[dict],
        breakdown_rows: list[dict],
    ) -> list[dict]:
        breakdown_by_branch = {
            str(row.get("branch") or "").strip(): row for row in breakdown_rows
        }
        merged: list[dict] = []
        seen: set[str] = set()

        for row in branch_rows:
            branch = str(row.get("branch") or "").strip()
            seen.add(branch)
            breakdown = breakdown_by_branch.get(branch) or {}
            merged.append({**row, **{k: v for k, v in breakdown.items() if k != "branch"}})

        for branch, breakdown in breakdown_by_branch.items():
            if branch in seen:
                continue
            merged.append(
                {
                    "branch": branch,
                    "total_stock_value": 0.0,
                    "total_stock_quantity": 0.0,
                    "total_records": 0,
                    "total_products": 0,
                    "total_locations": 0,
                    **{k: v for k, v in breakdown.items() if k != "branch"},
                }
            )

        return sorted(merged, key=lambda item: str(item.get("branch") or ""))

    def _build_estimation_meta(self, breakdown_rows: list[dict]) -> dict:
        if not breakdown_rows:
            return {}

        normalized = [self._normalize_branch_breakdown_row(row) for row in breakdown_rows]
        official_rows = [row for row in normalized if row.get("official_closure_available")]

        return {
            "closing_base_date": normalized[0].get("closing_base_date")
            if len(normalized) == 1
            else None,
            "closing_base_value": sum(row.get("closing_base_value") or 0 for row in normalized),
            "bridge_value": sum(row.get("bridge_value") or 0 for row in normalized),
            "period_net_value": sum(row.get("period_net_value") or 0 for row in normalized),
            "official_closure_available": bool(official_rows),
            "official_closure_date": official_rows[0].get("official_closure_date")
            if len(official_rows) == 1
            else None,
            "official_closure_value": sum(
                row.get("official_closure_value") or 0 for row in official_rows
            )
            if official_rows
            else None,
            "official_closure_on_period_end": any(
                row.get("official_closure_on_period_end") for row in normalized
            ),
            "by_branch_breakdown": normalized,
        }

    def _normalize_branch_rows(self, rows: list[dict]) -> list[dict]:
        return [
            {
                "branch": row.get("branch"),
                "total_stock_value": float(row.get("total_stock_value") or 0),
                "total_stock_quantity": float(row.get("total_stock_quantity") or 0),
                "total_records": int(row.get("total_records") or 0),
                "total_products": int(row.get("total_products") or 0),
                "total_locations": int(row.get("total_locations") or 0),
                **{
                    key: row.get(key)
                    for key in (
                        "closing_base_date",
                        "closing_base_value",
                        "bridge_value",
                        "period_net_value",
                        "official_closure_date",
                        "official_closure_value",
                        "official_closure_available",
                        "official_closure_on_period_end",
                    )
                    if key in row
                },
            }
            for row in rows
        ]

    def _normalize_location_rows(self, rows: list[dict]) -> list[dict]:
        return [
            {
                "branch": row.get("branch"),
                "location": row.get("location"),
                "total_stock_value": float(row.get("total_stock_value") or 0),
                "total_stock_quantity": float(row.get("total_stock_quantity") or 0),
                "total_records": int(row.get("total_records") or 0),
                "total_products": int(row.get("total_products") or 0),
            }
            for row in rows
            if float(row.get("total_stock_value") or 0) != 0
            or float(row.get("total_stock_quantity") or 0) != 0
        ]

    def _normalize_top_product_rows(self, rows: list[dict]) -> list[dict]:
        return [
            {
                "product_code": row.get("product_code"),
                "product_description": row.get("product_description"),
                "total_stock_value": float(row.get("total_stock_value") or 0),
                "total_stock_quantity": float(row.get("total_stock_quantity") or 0),
                "average_unit_cost": float(row.get("average_unit_cost") or 0),
                "total_locations": int(row.get("total_locations") or 0),
            }
            for row in rows
        ]

    def _bundle_from_resultsets(
        self,
        resultsets: list[dict],
        *,
        branch_label: str,
        location_label: str,
        breakdown_rows: list[dict] | None = None,
    ) -> dict:
        datasets = [item.get("data") or [] for item in resultsets]
        summary_row = datasets[0][0] if datasets and datasets[0] else {}
        by_branch_rows = datasets[1] if len(datasets) > 1 else []
        by_location_rows = datasets[2] if len(datasets) > 2 else []
        top_product_rows = datasets[3] if len(datasets) > 3 else []

        normalized_breakdown = [
            self._normalize_branch_breakdown_row(row) for row in (breakdown_rows or [])
        ]
        merged_by_branch = self._merge_branch_with_breakdown(
            self._normalize_branch_rows(by_branch_rows),
            normalized_breakdown,
        )

        bundle = {
            "summary": self._normalize_summary_row(
                summary_row,
                branch_label=branch_label,
                location_label=location_label,
            ),
            "by_branch": merged_by_branch
            if merged_by_branch
            else self._normalize_branch_rows(by_branch_rows),
            "by_location": self._normalize_location_rows(by_location_rows),
            "top_products": self._normalize_top_product_rows(top_product_rows),
        }
        if normalized_breakdown:
            bundle["estimation_meta"] = self._build_estimation_meta(normalized_breakdown)
        return bundle

    def _fetch_historical_breakdown_rows(
        self,
        request: GetStockValueRequest,
        *,
        full_kardex: bool = True,
    ) -> list[dict]:
        if full_kardex:
            sql, params = self._format_historical_breakdown_sql(request)
        else:
            sql, params = self._format_historical_method_breakdown_sql(request)
        with self as repo:
            rows = repo.execute_query(sql, params)
        return [self._normalize_branch_breakdown_row(row) for row in rows]

    def _fetch_historical_bundle(self, request: GetStockValueRequest) -> dict:
        _period_start, period_end, _period_end_exclusive = self._resolve_historical_period(
            request
        )
        use_full_breakdown = (
            normalize_stock_method(request.stock_method) == STOCK_METHOD_ESTIMATED
        )
        breakdown_rows = self._fetch_historical_breakdown_rows(
            request,
            full_kardex=use_full_breakdown,
        )
        method_plan = resolve_stock_method_plan(
            request,
            breakdown_rows,
            period_end=period_end,
        )

        if method_plan["resolved"] == STOCK_METHOD_RESOLVED_OFFICIAL:
            return self._fetch_official_closure_bundle(
                request,
                period_end=period_end,
                method_plan=method_plan,
            )

        if method_plan["resolved"] == STOCK_METHOD_RESOLVED_REGISTER_SNAPSHOT:
            return self._fetch_register_snapshot_bundle(
                request,
                period_end=period_end,
                method_plan=method_plan,
                breakdown_rows=breakdown_rows,
            )

        return self._fetch_estimated_historical_bundle(
            request,
            method_plan=method_plan,
            breakdown_rows=breakdown_rows if use_full_breakdown else None,
        )

    @staticmethod
    def _current_bundle_query_params(
        request: GetStockValueRequest,
        *,
        branch_label: str,
        location_label: str,
        filter_params: tuple,
    ) -> tuple:
        summary_params = (branch_label, location_label) + filter_params
        if request.summary_only:
            return summary_params
        # Cada SELECT subsequente reutiliza apenas os filtros SB2.
        return summary_params + filter_params + filter_params + filter_params

    def _fetch_current_bundle(self, request: GetStockValueRequest) -> dict:
        where_clause, params = self._build_filters(request)
        branch_label, location_label = self._labels(request)
        limit = max(1, int(getattr(request, "top_limit", 10) or 10))

        summary_sql = f"""
            SELECT
                ? AS branch,
                ? AS location,
                ISNULL(SUM(SB2.B2_VATU1), 0) AS total_stock_value,
                ISNULL(SUM(SB2.B2_QATU), 0) AS total_stock_quantity,
                COUNT(*) AS total_records,
                COUNT(DISTINCT SB2.B2_COD) AS total_products,
                COUNT(DISTINCT SB2.B2_LOCAL) AS total_locations
            FROM SB2010 SB2 WITH (NOLOCK)
            WHERE {where_clause}
        """

        if request.summary_only:
            sql = summary_sql
        else:
            sql = f"""
                {summary_sql};

                SELECT
                    SB2.B2_FILIAL AS branch,
                    ISNULL(SUM(SB2.B2_VATU1), 0) AS total_stock_value,
                    ISNULL(SUM(SB2.B2_QATU), 0) AS total_stock_quantity,
                    COUNT(*) AS total_records,
                    COUNT(DISTINCT SB2.B2_COD) AS total_products,
                    COUNT(DISTINCT SB2.B2_LOCAL) AS total_locations
                FROM SB2010 SB2 WITH (NOLOCK)
                WHERE {where_clause}
                GROUP BY SB2.B2_FILIAL
                ORDER BY SB2.B2_FILIAL;

                SELECT
                    SB2.B2_FILIAL AS branch,
                    SB2.B2_LOCAL AS location,
                    ISNULL(SUM(SB2.B2_VATU1), 0) AS total_stock_value,
                    ISNULL(SUM(SB2.B2_QATU), 0) AS total_stock_quantity,
                    COUNT(*) AS total_records,
                    COUNT(DISTINCT SB2.B2_COD) AS total_products
                FROM SB2010 SB2 WITH (NOLOCK)
                WHERE {where_clause}
                GROUP BY SB2.B2_FILIAL, SB2.B2_LOCAL
                ORDER BY SB2.B2_FILIAL, SB2.B2_LOCAL;

                SELECT TOP {limit}
                    SB2.B2_COD AS product_code,
                    MAX(SB1.B1_DESC) AS product_description,
                    ISNULL(SUM(SB2.B2_VATU1), 0) AS total_stock_value,
                    ISNULL(SUM(SB2.B2_QATU), 0) AS total_stock_quantity,
                    ROUND(AVG(CAST(SB2.B2_CM1 AS DECIMAL(18, 6))), 6) AS average_unit_cost,
                    COUNT(DISTINCT SB2.B2_LOCAL) AS total_locations
                FROM SB2010 SB2 WITH (NOLOCK)
                LEFT JOIN SB1010 SB1 WITH (NOLOCK)
                    ON SB1.D_E_L_E_T_ = ''
                   AND SB1.B1_COD = SB2.B2_COD
                WHERE {where_clause}
                GROUP BY SB2.B2_COD
                ORDER BY total_stock_value DESC, product_code;
            """

        final_params = self._current_bundle_query_params(
            request,
            branch_label=branch_label,
            location_label=location_label,
            filter_params=params,
        )

        with self as repo:
            resultsets = repo.execute_query_multiple(sql, final_params)

        return self._bundle_from_resultsets(
            resultsets,
            branch_label=branch_label,
            location_label=location_label,
        )

    def get_stock_value_bundle(self, request: GetStockValueRequest) -> dict:
        cache_key = stock_value_cache_key(request)
        cached = get_cached_stock_value_bundle(cache_key)
        if cached is not None:
            return cached

        if self._should_fan_out_consolidated(request):
            bundle = self._fetch_consolidated_bundle(request)
        elif self._uses_historical_estimation(request):
            bundle = self._fetch_historical_bundle(request)
        else:
            bundle = self._fetch_current_bundle(request)

        set_cached_stock_value_bundle(cache_key, bundle)
        return bundle

    def get_stock_value_summary(self, request: GetStockValueRequest) -> dict:
        return self.get_stock_value_bundle(request)["summary"]

    def get_stock_value_by_branch(self, request: GetStockValueRequest) -> list[dict]:
        return self.get_stock_value_bundle(request)["by_branch"]

    def get_stock_value_by_location(self, request: GetStockValueRequest) -> list[dict]:
        return self.get_stock_value_bundle(request)["by_location"]

    def get_top_products_by_stock_value(self, request: GetStockValueRequest) -> list[dict]:
        return self.get_stock_value_bundle(request)["top_products"]
