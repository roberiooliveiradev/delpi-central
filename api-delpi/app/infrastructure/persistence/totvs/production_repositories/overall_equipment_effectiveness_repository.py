from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.application.dto.production.production_request import ProductionRequest
from app.domain.entities.production.overall_equipment_effectiveness import OverallEquipmentEffectiveness
from app.domain.ports.production.overall_equipment_effectiveness_repository_port import OverallEquipmentEffectivenessRepositoryPort


class OverallEquipmentEffectivenessRepository(BaseRepository, OverallEquipmentEffectivenessRepositoryPort):

    def get_overall_equipment_effectiveness(
        self,
        request: ProductionRequest
    ) -> OverallEquipmentEffectiveness:
        qb = QueryBuilder()
        qb.raw("D_E_L_E_T_ = ''")
        qb.eq("H6_FILIAL", request.branch)
        qb.date_range("H6_DTPROD", request.start_date, request.end_date)

        where_clause, where_params = qb.build()

        sql = f"""
            SELECT
                AVG(
                    CASE
                        WHEN TRY_CAST(REPLACE(LTRIM(RTRIM(H6_ZEFICI)), ',', '.') AS DECIMAL(18, 4)) BETWEEN 0 AND 299
                        THEN TRY_CAST(REPLACE(LTRIM(RTRIM(H6_ZEFICI)), ',', '.') AS DECIMAL(18, 4))
                        ELSE NULL
                    END
                ) AS oee_pct
            FROM
                SH6010
            WHERE
                {where_clause}
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

        return OverallEquipmentEffectiveness()