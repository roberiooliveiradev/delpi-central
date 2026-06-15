from app.application.dto.production.get_production_oee_request import (
    GetProductionOeeRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.models.page import Page
from app.domain.entities.production.overall_equipment_effectiveness import (
    OverallEquipmentEffectiveness,
)
from app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
    OverallEquipmentEffectivenessRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pagination import paginate
from app.infrastructure.persistence.totvs.production_repositories.production_oee_sql import (
    OEE_APPOINTMENT_DETAIL_SELECT,
    OEE_APPOINTMENTS_SELECT,
    OEE_VALID_PCT_EXPR_PLAIN,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class OverallEquipmentEffectivenessRepository(
    BaseRepository, OverallEquipmentEffectivenessRepositoryPort
):
    @staticmethod
    def _build_appointment_filters(request: GetProductionOeeRequest) -> tuple[str, list]:
        qb = QueryBuilder()
        qb.raw("H6.D_E_L_E_T_ = ''")
        qb.raw("H6.H6_OP <> ''")

        if request.branch:
            qb.eq("H6.H6_FILIAL", request.branch)

        qb.date_range("H6.H6_DTPROD", request.start_date, request.end_date)

        if request.work_center:
            qb.eq("SH1.H1_CTRAB", request.work_center)

        if request.production_order:
            qb.eq("H6.H6_OP", request.production_order)

        if request.product_type:
            normalized_type = str(request.product_type).strip().upper()
            if normalized_type in {"PA", "PI"}:
                qb.eq("SB1.B1_TIPO", normalized_type)

        return qb.build()

    @staticmethod
    def _status_filter_clause(status: str | None) -> str:
        normalized = (status or "").strip().lower()
        if normalized == "valid":
            return "WHERE status = 'valid'"
        if normalized == "outlier":
            return "WHERE status = 'outlier'"
        return ""

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
            "resource_name": "resource_name",
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
        if normalized == "outlier":
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
        qb = QueryBuilder()
        qb.raw("D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("H6_FILIAL", request.branch)

        qb.date_range("H6_DTPROD", request.start_date, request.end_date)

        where_clause, where_params = qb.build()

        sql = f"""
            SELECT
                AVG({OEE_VALID_PCT_EXPR_PLAIN}) AS oee_pct
            FROM SH6010
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
        qb = QueryBuilder()
        qb.raw("D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("H6_FILIAL", request.branch)

        qb.date_range("H6_DTPROD", request.start_date, request.end_date)

        where_clause, where_params = qb.build()

        sql = f"""
            SELECT
                H6_FILIAL AS branch,
                AVG({OEE_VALID_PCT_EXPR_PLAIN}) AS oee_pct
            FROM SH6010
            WHERE {where_clause}
              AND H6_FILIAL IS NOT NULL
              AND LTRIM(RTRIM(H6_FILIAL)) <> ''
            GROUP BY H6_FILIAL
            ORDER BY H6_FILIAL
        """

        with self:
            rows = self.execute_query(sql, where_params)

        return rows or []

    def get_oee_appointment_summary(
        self,
        request: GetProductionOeeRequest,
    ) -> dict:
        where_clause, where_params = self._build_appointment_filters(request)
        status_clause = self._status_filter_clause(request.status)

        sql = f"""
            WITH APONTAMENTOS_OEE AS (
                {OEE_APPOINTMENTS_SELECT}
                WHERE {where_clause}
            )
            SELECT
                COUNT(*) AS total_appointments,
                SUM(CASE WHEN status = 'valid' THEN 1 ELSE 0 END) AS valid_appointments,
                SUM(CASE WHEN status = 'outlier' THEN 1 ELSE 0 END) AS outlier_appointments
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
        status_clause = self._status_filter_clause(request.status)
        order_clause = self._list_order_clause(request)

        count_sql = f"""
            WITH APONTAMENTOS_OEE AS (
                {OEE_APPOINTMENTS_SELECT}
                WHERE {where_clause}
            )
            SELECT COUNT(*) AS total
            FROM APONTAMENTOS_OEE
            {status_clause}
        """

        list_sql = f"""
            WITH APONTAMENTOS_OEE AS (
                {OEE_APPOINTMENTS_SELECT}
                WHERE {where_clause}
            )
            SELECT *
            FROM APONTAMENTOS_OEE
            {status_clause}
            {order_clause}
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        list_params = where_params + (paging["offset"], paging["page_size"])

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
