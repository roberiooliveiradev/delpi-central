from app.application.dto.production.get_production_oee_request import (
    GetProductionOeeRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.models.page import Page
from app.application.services.production.production_kpi_cache import (
    get_cached_production_oee,
    get_cached_production_oee_by_branch,
    production_oee_by_branch_cache_key,
    production_oee_cache_key,
    set_cached_production_oee,
    set_cached_production_oee_by_branch,
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
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pagination import paginate
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_appointment_filters import (
    build_fabril_view_filters,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_oee_kpi_sql import (
    OEE_FABRIL_KPI_AVG_SELECT,
    OEE_FABRIL_KPI_BY_BRANCH_SELECT,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_oee_sql import (
    OEE_FABRIL_APPOINTMENTS_SELECT,
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

        where_clause, where_params = build_fabril_view_filters(
            date_start=request.start_date,
            date_end=request.end_date,
            branch=request.branch,
            status_ok_only=True,
            efficiency_cap_pct=PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
            column_prefix="EF",
        )

        sql = f"""
            {OEE_FABRIL_KPI_BY_BRANCH_SELECT}
            WHERE {where_clause}
              AND RTRIM(LTRIM(EF.FILIAL)) <> ''
            GROUP BY RTRIM(LTRIM(EF.FILIAL))
            ORDER BY branch
        """

        with self:
            rows = self.execute_query(sql, where_params)

        return rows or []

    def get_oee_appointment_summary(
        self,
        request: GetProductionOeeRequest,
    ) -> dict:
        where_clause, where_params = self._build_appointment_filters(request)
        status_clause = self._list_filter_clause(request)

        sql = f"""
            WITH APONTAMENTOS_OEE AS (
                {OEE_FABRIL_APPOINTMENTS_SELECT}
                WHERE {where_clause}
            )
            SELECT
                COUNT(*) AS total_appointments,
                SUM(CASE WHEN status = 'valid' THEN 1 ELSE 0 END) AS valid_appointments,
                SUM(CASE WHEN status = 'outlier' THEN 1 ELSE 0 END) AS outlier_appointments,
                ROUND(AVG(CASE WHEN status = 'valid' THEN oee_pct END), 2) AS avg_oee_pct
            FROM APONTAMENTOS_OEE
            {status_clause}
        """

        with self:
            row = self.execute_one(sql, where_params)

        return row or {
            "total_appointments": 0,
            "valid_appointments": 0,
            "outlier_appointments": 0,
        }

    def list_oee_appointments(
        self,
        request: GetProductionOeeRequest,
    ) -> Page[dict]:
        paging = paginate(request.page, request.page_size)
        where_clause, where_params = self._build_appointment_filters(request)
        status_clause = self._list_filter_clause(request)
        order_clause = self._list_order_clause(request)

        count_sql = f"""
            WITH APONTAMENTOS_OEE AS (
                {OEE_FABRIL_APPOINTMENTS_SELECT}
                WHERE {where_clause}
            )
            SELECT COUNT(*) AS total
            FROM APONTAMENTOS_OEE
            {status_clause}
        """

        list_sql = f"""
            WITH APONTAMENTOS_OEE AS (
                {OEE_FABRIL_APPOINTMENTS_SELECT}
                WHERE {where_clause}
            )
            SELECT *
            FROM APONTAMENTOS_OEE
            {status_clause}
            {order_clause}
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        list_params = where_params + [paging["offset"], paging["page_size"]]

        with self:
            total_row = self.execute_one(count_sql, where_params)
            total = int(total_row.get("total") or 0) if total_row else 0
            rows = self.execute_query(list_sql, list_params) or []

        return Page(
            items=rows,
            total=total,
            page=paging["page"],
            page_size=paging["page_size"],
        )

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
