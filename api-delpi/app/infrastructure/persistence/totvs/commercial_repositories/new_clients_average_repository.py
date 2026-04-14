from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from app.application.dto.commercial.new_clients_average_request import NewClientsAverageRequest
from app.domain.entities.commercial.new_clients_average import NewClientsAverage
from app.domain.ports.commercial.new_clients_average_repository_port import NewClientsAverageRepositoryPort


class NewClientsAverageRepository(BaseRepository, NewClientsAverageRepositoryPort):

    def get_new_clients_total(
        self,
        request: NewClientsAverageRequest
    ) -> NewClientsAverage:
        qb = QueryBuilder()
        qb.raw("AD1.D_E_L_E_T_ = ''")

        if request.branch:
            qb.eq("AD1.AD1_FILIAL", request.branch)

        qb.raw("AD1.AD1_CODCLI <> ''")
        qb.raw("AD1.AD1_LOJCLI <> ''")

        where_clause, where_params = qb.build()

        period_qb = QueryBuilder()
        period_qb.date_range("PRIMEIRA_DATA", request.start_date, request.end_date)

        period_where_clause, period_where_params = period_qb.build()

        sql = f"""
            WITH primeira_ov_cliente AS (
                SELECT
                    AD1.AD1_FILIAL,
                    AD1.AD1_CODCLI,
                    AD1.AD1_LOJCLI,
                    MIN(AD1.AD1_DATA) AS PRIMEIRA_DATA
                FROM AD1010 AD1
                WHERE {where_clause}
                GROUP BY
                    AD1.AD1_FILIAL,
                    AD1.AD1_CODCLI,
                    AD1.AD1_LOJCLI
            )
            SELECT
                COUNT(*) AS total_new_clients,
                MIN(PRIMEIRA_DATA) AS first_date,
                MAX(PRIMEIRA_DATA) AS last_date
            FROM primeira_ov_cliente
            WHERE {period_where_clause}
        """

        params = where_params + period_where_params

        with self:
            row = self.execute_one(sql, params)

        return NewClientsAverage(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            first_date=(row or {}).get("first_date") or None,
            last_date=(row or {}).get("last_date") or None,
            total_new_clients=int((row or {}).get("total_new_clients") or 0),
        )