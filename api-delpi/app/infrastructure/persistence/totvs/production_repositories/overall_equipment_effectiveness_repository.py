from app.application.dto.production.get_production_oee_request import (
    GetProductionOeeRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.models.page import Page
from app.application.services.production.production_kpi_cache import (
    get_cached_production_oee,
    get_cached_production_oee_appointments_bundle,
    get_cached_production_oee_by_branch,
    get_cached_production_oee_appointments_materialized,
    get_cached_production_oee_series_daily,
    production_oee_appointments_bundle_cache_key,
    production_oee_appointments_materialized_cache_key,
    production_oee_by_branch_cache_key,
    production_oee_cache_key,
    production_oee_series_daily_cache_key,
    set_cached_production_oee,
    set_cached_production_oee_appointments_bundle,
    set_cached_production_oee_appointments_materialized,
    set_cached_production_oee_by_branch,
    set_cached_production_oee_series_daily,
)
from app.domain.entities.production.overall_equipment_effectiveness import (
    OverallEquipmentEffectiveness,
)
from app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
    OverallEquipmentEffectivenessRepositoryPort,
)
from app.domain.production.production_efficiency_valid_range import (
    EFFICIENCY_BAND_VERIFY,
    PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
    parse_efficiency_bands,
    resolve_production_list_status_filter_clause,
)
from app.domain.services.production.production_oee_series_aggregation_service import (
    resolve_period_oee_by_branch,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pagination import paginate
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_appointment_filters import (
    build_fabril_view_filters,
)
from app.domain.production.production_oee_listing_service import (
    filter_production_appointment_rows,
    paginate_production_appointment_rows,
    sort_production_appointment_rows,
    summarize_production_appointment_rows,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_oee_appointments_batch_sql import (
    format_oee_appointments_materialize_sql,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_oee_sql import (
    build_oee_fabril_appointments_select,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_sh6010_apply import (
    build_fabril_sh6010_scoped_left_join,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_oee_kpi_sql import (
    OEE_FABRIL_KPI_AVG_SELECT,
    OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT,
)
from app.infrastructure.persistence.totvs.production_repositories.production_oee_sql import (
    OEE_APPOINTMENT_DETAIL_SELECT,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class OverallEquipmentEffectivenessRepository(
    BaseRepository, OverallEquipmentEffectivenessRepositoryPort
):
    @staticmethod
    def _build_appointment_filters(request: GetProductionOeeRequest) -> tuple[str, list]:
        if not request.start_date or not request.end_date:
            return "1=0", []

        where_clause, where_params = build_fabril_view_filters(
            date_start=request.start_date,
            date_end=request.end_date,
            branch=request.branch,
            op=request.production_order,
            work_center=request.work_center,
            operator_code=request.operator_code,
            status_ok_only=True,
            efficiency_cap_pct=None,
            column_prefix="EF",
        )

        extra_clauses: list[str] = []
        extra_params: list = []

        if request.product_type:
            normalized_type = str(request.product_type).strip().upper()
            if normalized_type in {"PA", "PI"}:
                extra_clauses.append("SB1.B1_TIPO = ?")
                extra_params.append(normalized_type)

        if extra_clauses:
            where_clause = f"{where_clause} AND {' AND '.join(extra_clauses)}"
            where_params = tuple(list(where_params) + extra_params)

        return where_clause, list(where_params)

    @staticmethod
    def _build_kpi_filters(request: ProductionRequest) -> tuple[str, list]:
        if not request.start_date or not request.end_date:
            return "1=0", []

        where_clause, where_params = build_fabril_view_filters(
            date_start=request.start_date,
            date_end=request.end_date,
            branch=request.branch,
            status_ok_only=True,
            efficiency_cap_pct=PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
            column_prefix="EF",
        )
        return where_clause, list(where_params)

    def _resolve_oee_pct_for_branch(
        self,
        request: ProductionRequest,
        rows: list[dict],
    ) -> float | None:
        target_branch = (request.branch or "").strip()
        if not target_branch:
            return None

        for row in rows:
            if str(row.get("branch") or "").strip() == target_branch:
                value = row.get("oee_pct")
                return float(value) if value is not None else None

        return None

    @staticmethod
    def _list_filter_clause(request: GetProductionOeeRequest) -> str:
        return resolve_production_list_status_filter_clause(
            request.status,
            request.efficiency_bands,
        )

    @staticmethod
    def _list_order_clause(request: GetProductionOeeRequest) -> str:
        sort_columns = {
            "appointment_id": "appointment_id",
            "status": "status",
            "branch": "branch",
            "production_order": "production_order",
            "product_code": "product_code",
            "product_description": "product_description",
            "product_type": "product_type",
            "operator_code": "operator_code",
            "work_center": "work_center",
            "operation": "operation",
            "resource_code": "resource_code",
            "production_date": "production_date",
            "start_time": "start_time",
            "end_time": "end_time",
            "oee_pct": "oee_pct",
            "produced_qty": "produced_qty",
        }
        sort_key = (request.sort_by or "").strip().lower()
        sort_column = sort_columns.get(sort_key)
        if sort_column:
            direction = (
                "DESC" if str(request.sort_dir or "asc").lower() == "desc" else "ASC"
            )
            return f"""
                ORDER BY {sort_column} {direction},
                         production_date DESC,
                         production_order ASC,
                         operation ASC
            """

        normalized = (request.status or "").strip().lower()
        bands = parse_efficiency_bands(request.efficiency_bands)
        if normalized == "outlier" or bands == [EFFICIENCY_BAND_VERIFY]:
            return """
                ORDER BY oee_pct DESC,
                         production_date DESC,
                         production_order ASC,
                         operation ASC
            """

        return """
            ORDER BY production_date DESC,
                     production_order ASC,
                     operation ASC
        """

    def get_overall_equipment_effectiveness(
        self,
        request: ProductionRequest,
    ) -> OverallEquipmentEffectiveness:
        cache_key = production_oee_cache_key(request)
        cached = get_cached_production_oee(cache_key)
        if cached is not None:
            return cached

        result = self._load_overall_equipment_effectiveness(request)
        set_cached_production_oee(cache_key, result)
        return result

    def _load_overall_equipment_effectiveness(
        self,
        request: ProductionRequest,
    ) -> OverallEquipmentEffectiveness:
        if request.branch:
            consolidated_request = ProductionRequest(
                branch=None,
                start_date=request.start_date,
                end_date=request.end_date,
            )
            rows = self._load_overall_equipment_effectiveness_by_branch(
                consolidated_request
            )
            oee_pct = self._resolve_oee_pct_for_branch(request, rows)
            return OverallEquipmentEffectiveness(
                branch=request.branch,
                start_date=request.start_date,
                end_date=request.end_date,
                oee_pct=oee_pct,
            )

        where_clause, where_params = self._build_kpi_filters(request)

        sql = f"""
            {OEE_FABRIL_KPI_AVG_SELECT}
            WHERE {where_clause}
        """

        with self:
            result = self.execute_query(sql, where_params)

        if result:
            row = result[0]
            return OverallEquipmentEffectiveness(
                branch=request.branch,
                start_date=request.start_date,
                end_date=request.end_date,
                oee_pct=row.get("oee_pct"),
            )

        return OverallEquipmentEffectiveness(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            oee_pct=None,
        )

    def list_overall_equipment_effectiveness_by_branch(
        self,
        request: ProductionRequest,
    ) -> list[dict]:
        cache_key = production_oee_by_branch_cache_key(request)
        cached = get_cached_production_oee_by_branch(cache_key)
        if cached is not None:
            return cached

        rows = self._load_overall_equipment_effectiveness_by_branch(request)
        set_cached_production_oee_by_branch(cache_key, rows)
        return rows

    def _load_overall_equipment_effectiveness_by_branch(
        self,
        request: ProductionRequest,
    ) -> list[dict]:
        if not request.start_date or not request.end_date:
            return []

        # Deriva o OEE do período por filial da agregação diária (mesma view,
        # mesmos filtros), evitando um segundo scan pesado da view fabril.
        # A série diária já é cacheada em `production-oee-series-daily`.
        daily_rows = self.list_oee_kpi_by_day_and_branch(request)
        return resolve_period_oee_by_branch(daily_rows)

    def list_oee_kpi_by_day_and_branch(
        self,
        request: ProductionRequest,
    ) -> list[dict]:
        cache_key = production_oee_series_daily_cache_key(request)
        cached = get_cached_production_oee_series_daily(cache_key)
        if cached is not None:
            return cached

        rows = self._load_oee_kpi_by_day_and_branch(request)
        set_cached_production_oee_series_daily(cache_key, rows)
        return rows

    def _load_oee_kpi_by_day_and_branch(
        self,
        request: ProductionRequest,
    ) -> list[dict]:
        if not request.start_date or not request.end_date:
            return []

        where_clause, where_params = self._build_kpi_filters(request)

        sql = f"""
            {OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT}
            WHERE {where_clause}
            GROUP BY EF.DATA_PRODUCAO, EF.FILIAL
            ORDER BY production_date, branch
        """

        with self:
            rows = self.execute_query(sql, where_params)

        return rows or []

    @staticmethod
    def _protheus_period_params(
        request: GetProductionOeeRequest,
    ) -> tuple[str, str]:
        qb = QueryBuilder()
        start = qb.convert_date_to_protheus(request.start_date or "")
        end = qb.convert_date_to_protheus(request.end_date or "")
        if not start or not end:
            raise ValueError("Período OEE inválido para materialização.")
        return start, end

    def _load_oee_appointments_materialized_rows(
        self,
        request: GetProductionOeeRequest,
    ) -> list[dict]:
        materialized_key = production_oee_appointments_materialized_cache_key(request)
        cached_rows = get_cached_production_oee_appointments_materialized(materialized_key)
        if cached_rows is not None:
            return cached_rows

        where_clause, where_params = self._build_appointment_filters(request)
        date_start, date_end = self._protheus_period_params(request)
        sh6010_join, sh6010_params = build_fabril_sh6010_scoped_left_join(
            date_start_protheus=date_start,
            date_end_protheus=date_end,
            branch=request.branch,
        )
        appointments_select = build_oee_fabril_appointments_select(
            sh6010_join_sql=sh6010_join,
        )
        sql = format_oee_appointments_materialize_sql(
            appointments_select=appointments_select,
            where_clause=where_clause,
        )
        query_params = tuple(list(sh6010_params) + list(where_params))

        with self:
            resultsets = self.execute_query_multiple(sql, query_params)

        rows = resultsets[0].get("data") or [] if resultsets else []
        set_cached_production_oee_appointments_materialized(materialized_key, rows)
        return rows

    def _build_oee_appointments_listing(
        self,
        request: GetProductionOeeRequest,
        rows: list[dict],
    ) -> tuple[dict, Page[dict]]:
        paging = paginate(request.page, request.page_size)
        filtered_rows = filter_production_appointment_rows(
            rows,
            status=request.status,
            efficiency_bands=request.efficiency_bands,
        )
        summary = summarize_production_appointment_rows(filtered_rows)
        sorted_rows = sort_production_appointment_rows(
            filtered_rows,
            sort_by=request.sort_by,
            sort_dir=request.sort_dir,
            status=request.status,
            efficiency_bands=request.efficiency_bands,
        )
        page_rows, total = paginate_production_appointment_rows(
            sorted_rows,
            page=paging["page"],
            page_size=paging["page_size"],
        )
        return summary, Page(
            items=page_rows,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"],
        )

    def get_oee_appointments_bundle(
        self,
        request: GetProductionOeeRequest,
    ) -> tuple[dict, Page[dict]]:
        cache_key = production_oee_appointments_bundle_cache_key(request)
        cached = get_cached_production_oee_appointments_bundle(cache_key)
        if cached is not None:
            summary = cached.get("summary") or {}
            page_payload = cached.get("page") or {}
            return summary, Page(
                items=page_payload.get("items") or [],
                total=int(page_payload.get("total") or 0),
                page=int(page_payload.get("page") or 1),
                page_size=int(page_payload.get("page_size") or 20),
            )

        summary, page = self._load_oee_appointments_bundle(request)
        set_cached_production_oee_appointments_bundle(
            cache_key,
            {
                "summary": summary,
                "page": page.to_dict(),
            },
        )
        return summary, page

    def _load_oee_appointments_bundle(
        self,
        request: GetProductionOeeRequest,
    ) -> tuple[dict, Page[dict]]:
        rows = self._load_oee_appointments_materialized_rows(request)
        return self._build_oee_appointments_listing(request, rows)

    def get_oee_appointment_summary(
        self,
        request: GetProductionOeeRequest,
    ) -> dict:
        summary, _page = self.get_oee_appointments_bundle(request)
        return summary

    def list_oee_appointments(
        self,
        request: GetProductionOeeRequest,
    ) -> Page[dict]:
        _summary, page = self.get_oee_appointments_bundle(request)
        return page

    def get_oee_appointment_by_id(
        self,
        appointment_id: int,
        *,
        branch: str | None = None,
    ) -> dict | None:
        qb = QueryBuilder()
        qb.raw("H6.D_E_L_E_T_ = ''")
        qb.eq("H6.R_E_C_N_O_", appointment_id)

        if branch:
            qb.eq("H6.H6_FILIAL", branch)

        where_clause, where_params = qb.build()

        sql = f"""
            {OEE_APPOINTMENT_DETAIL_SELECT}
            WHERE {where_clause}
        """

        with self:
            row = self.execute_one(sql, where_params)

        return row
