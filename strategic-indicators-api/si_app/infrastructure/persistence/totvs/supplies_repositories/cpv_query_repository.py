from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.domain.ports.supplies.cpv_query_repository_port import CpvQueryRepositoryPort
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from si_app.shared.branch_filter import effective_query_branch
from si_app.application.dto.supplies.get_cpv_request import GetCPVRequest


class CpvQueryRepository(BaseRepository, CpvQueryRepositoryPort):

    DEFAULT_CFOPS = ("5101", "5102", "5124", "6101", "6102", "6124", "7101", "6109")

    def _build_filters(self, request: GetCPVRequest):
        qb = QueryBuilder()

        qb.raw("SD3.D_E_L_E_T_ = ''")
        qb.raw("SF4.D_E_L_E_T_ = ''")

        branch = effective_query_branch(request.branch)
        if branch:
            qb.eq("SD3.D3_FILIAL", branch)

        qb.date_range("SD3.D3_EMISSAO", request.start_date, request.end_date)

        cfops = request.cfops or self.DEFAULT_CFOPS
        qb.in_list("SF4.F4_CF", cfops)

        return qb.build()

    def get_cpv_summary(self, request: GetCPVRequest) -> dict:
        where_clause, params = self._build_filters(request)

        sql = f"""
            SELECT
                ISNULL(SUM(SD3.D3_CUSTO1), 0) AS cpv_total,
                COUNT(*) AS total_movements,
                ISNULL(SUM(SD3.D3_QUANT), 0) AS total_quantity,
                ISNULL(MIN(SD3.D3_EMISSAO), '') AS start_date,
                ISNULL(MAX(SD3.D3_EMISSAO), '') AS end_date
            FROM SD3010 SD3
            INNER JOIN SF4010 SF4
                ON SF4.F4_CODIGO = SD3.D3_TM
            WHERE {where_clause}
        """

        with self as repo:
            result = repo.execute_one(sql, params)

        return result or {
            "cpv_total": 0,
            "total_movements": 0,
            "total_quantity": 0,
            "start_date": request.start_date or "",
            "end_date": request.end_date or "",
        }

    def get_cpv_by_cfop(self, request: GetCPVRequest) -> list[dict]:
        where_clause, params = self._build_filters(request)

        sql = f"""
            SELECT
                SF4.F4_CF AS cfop,
                MAX(SF4.F4_TEXTO) AS tes_description,
                COUNT(*) AS total_movements,
                ISNULL(SUM(SD3.D3_QUANT), 0) AS total_quantity,
                ISNULL(SUM(SD3.D3_CUSTO1), 0) AS cpv_total
            FROM SD3010 SD3
            INNER JOIN SF4010 SF4
                ON SF4.F4_CODIGO = SD3.D3_TM
            WHERE {where_clause}
            GROUP BY SF4.F4_CF
            ORDER BY cpv_total DESC, cfop
        """

        with self as repo:
            return repo.execute_query(sql, params) or []

    def get_cpv_by_tm(self, request: GetCPVRequest) -> list[dict]:
        where_clause, params = self._build_filters(request)

        sql = f"""
            SELECT
                SD3.D3_TM AS tm,
                SF4.F4_CF AS cfop,
                MAX(SF4.F4_TEXTO) AS tes_description,
                COUNT(*) AS total_movements,
                ISNULL(SUM(SD3.D3_QUANT), 0) AS total_quantity,
                ISNULL(SUM(SD3.D3_CUSTO1), 0) AS cpv_total
            FROM SD3010 SD3
            INNER JOIN SF4010 SF4
                ON SF4.F4_CODIGO = SD3.D3_TM
            WHERE {where_clause}
            GROUP BY SD3.D3_TM, SF4.F4_CF
            ORDER BY cpv_total DESC, tm
        """

        with self as repo:
            return repo.execute_query(sql, params) or []

    def get_cpv_top_products(self, request: GetCPVRequest) -> list[dict]:
        where_clause, params = self._build_filters(request)
        limit = max(1, int(getattr(request, "top_limit", 5) or 5))

        sql = f"""
            SELECT TOP {limit}
                SD3.D3_COD AS product_code,
                MAX(SB1.B1_DESC) AS product_description,
                COUNT(*) AS total_movements,
                ISNULL(SUM(SD3.D3_QUANT), 0) AS total_quantity,
                ISNULL(SUM(SD3.D3_CUSTO1), 0) AS cpv_total
            FROM SD3010 SD3
            INNER JOIN SF4010 SF4
                ON SF4.F4_CODIGO = SD3.D3_TM
            LEFT JOIN SB1010 SB1
                ON SB1.D_E_L_E_T_ = ''
            AND SB1.B1_COD = SD3.D3_COD
            WHERE {where_clause}
            GROUP BY SD3.D3_COD
            ORDER BY cpv_total DESC, product_code
        """

        with self as repo:
            return repo.execute_query(sql, params) or []

    def get_cpv_top_documents(self, request: GetCPVRequest) -> list[dict]:
        where_clause, params = self._build_filters(request)
        limit = max(1, int(getattr(request, "top_limit", 5) or 5))

        sql = f"""
            SELECT TOP {limit}
                SD3.D3_DOC AS document,
                COUNT(*) AS total_movements,
                ISNULL(SUM(SD3.D3_QUANT), 0) AS total_quantity,
                ISNULL(SUM(SD3.D3_CUSTO1), 0) AS cpv_total
            FROM SD3010 SD3
            INNER JOIN SF4010 SF4
                ON SF4.F4_CODIGO = SD3.D3_TM
            WHERE {where_clause}
            GROUP BY SD3.D3_DOC
            ORDER BY cpv_total DESC, document
        """

        with self as repo:
            return repo.execute_query(sql, params) or []