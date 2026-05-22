from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from si_app.shared.branch_filter import effective_query_branch
from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.entities.production.overall_equipment_effectiveness import OverallEquipmentEffectiveness
from si_app.domain.ports.production.overall_equipment_effectiveness_repository_port import OverallEquipmentEffectivenessRepositoryPort


class OverallEquipmentEffectivenessRepository(BaseRepository, OverallEquipmentEffectivenessRepositoryPort):

    def get_overall_equipment_effectiveness(
        self,
        request: ProductionRequest
    ) -> OverallEquipmentEffectiveness:
        qb = QueryBuilder()
        qb.raw("D_E_L_E_T_ = ''")

        branch = effective_query_branch(request.branch)
        if branch:
            qb.eq("H6_FILIAL", branch)

        qb.date_range("H6_DTPROD", request.start_date, request.end_date)

        where_clause, where_params = qb.build()

        sql = f"""
            SELECT
                AVG(
                    CASE
                        WHEN TRY_CAST(REPLACE(LTRIM(RTRIM(H6_ZEFICI)), ',', '.') AS DECIMAL(18, 4)) BETWEEN 0 AND 199
                        THEN TRY_CAST(REPLACE(LTRIM(RTRIM(H6_ZEFICI)), ',', '.') AS DECIMAL(18, 4))
                        ELSE NULL
                    END
                ) AS oee_pct
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
        request: ProductionRequest
    ) -> list[dict]:
        qb = QueryBuilder()
        qb.raw("D_E_L_E_T_ = ''")

        branch = effective_query_branch(request.branch)
        if branch:
            qb.eq("H6_FILIAL", branch)

        qb.date_range("H6_DTPROD", request.start_date, request.end_date)

        where_clause, where_params = qb.build()

        sql = f"""
            SELECT
                H6_FILIAL AS branch,
                AVG(
                    CASE
                        WHEN TRY_CAST(REPLACE(LTRIM(RTRIM(H6_ZEFICI)), ',', '.') AS DECIMAL(18, 4)) BETWEEN 0 AND 199
                        THEN TRY_CAST(REPLACE(LTRIM(RTRIM(H6_ZEFICI)), ',', '.') AS DECIMAL(18, 4))
                        ELSE NULL
                    END
                ) AS oee_pct
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