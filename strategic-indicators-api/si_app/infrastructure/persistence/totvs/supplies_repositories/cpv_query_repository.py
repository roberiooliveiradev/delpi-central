from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.domain.ports.supplies.cpv_query_repository_port import CpvQueryRepositoryPort
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder
from si_app.shared.branch_filter import effective_query_branch
from si_app.application.dto.supplies.get_cpv_request import GetCPVRequest


class CpvQueryRepository(BaseRepository, CpvQueryRepositoryPort):
    """CPV alinhado ao relatório Kardex: SD2010, D2_CUSTO1 e filtro por D2_CF."""

    KARDEX_DEFAULT_CFOPS = ("5101", "5124", "6101", "6124")

    def _resolve_cfops(self, request: GetCPVRequest) -> tuple[str, ...]:
        cfops = tuple(request.cfops) if request.cfops else self.KARDEX_DEFAULT_CFOPS
        return cfops or self.KARDEX_DEFAULT_CFOPS

    def _build_filters(self, request: GetCPVRequest):
        qb = QueryBuilder()

        qb.raw("D2.D_E_L_E_T_ = ''")

        branch = effective_query_branch(request.branch)
        if branch:
            qb.eq("D2.D2_FILIAL", branch)

        qb.date_range("D2.D2_EMISSAO", request.start_date, request.end_date)

        cfops = self._resolve_cfops(request)
        qb.in_list("D2.D2_CF", cfops)

        return qb.build()

    def get_cpv_summary(self, request: GetCPVRequest) -> dict:
        where_clause, params = self._build_filters(request)

        sql = f"""
            SELECT
                ISNULL(SUM(D2.D2_CUSTO1), 0) AS cpv_total,
                COUNT(*) AS total_movements,
                ISNULL(SUM(D2.D2_QUANT), 0) AS total_quantity,
                ISNULL(MIN(D2.D2_EMISSAO), '') AS start_date,
                ISNULL(MAX(D2.D2_EMISSAO), '') AS end_date
            FROM SD2010 D2
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
                D2.D2_CF AS cfop,
                COUNT(*) AS total_movements,
                ISNULL(SUM(D2.D2_QUANT), 0) AS total_quantity,
                ISNULL(SUM(D2.D2_CUSTO1), 0) AS cpv_total
            FROM SD2010 D2
            WHERE {where_clause}
            GROUP BY D2.D2_CF
            ORDER BY cpv_total DESC, cfop
        """

        with self as repo:
            return repo.execute_query(sql, params) or []

    def get_cpv_by_tm(self, request: GetCPVRequest) -> list[dict]:
        where_clause, params = self._build_filters(request)

        sql = f"""
            SELECT
                D2.D2_TES AS tm,
                D2.D2_CF AS cfop,
                MAX(SF4.F4_TEXTO) AS tes_description,
                COUNT(*) AS total_movements,
                ISNULL(SUM(D2.D2_QUANT), 0) AS total_quantity,
                ISNULL(SUM(D2.D2_CUSTO1), 0) AS cpv_total
            FROM SD2010 D2
            INNER JOIN SF4010 SF4
                ON SF4.F4_CODIGO = D2.D2_TES
               AND SF4.D_E_L_E_T_ = ''
            WHERE {where_clause}
            GROUP BY D2.D2_TES, D2.D2_CF
            ORDER BY cpv_total DESC, tm
        """

        with self as repo:
            return repo.execute_query(sql, params) or []

    def get_cpv_top_products(self, request: GetCPVRequest) -> list[dict]:
        where_clause, params = self._build_filters(request)
        limit = max(1, int(getattr(request, "top_limit", 5) or 5))

        sql = f"""
            SELECT TOP {limit}
                D2.D2_COD AS product_code,
                MAX(SB1.B1_DESC) AS product_description,
                COUNT(*) AS total_movements,
                ISNULL(SUM(D2.D2_QUANT), 0) AS total_quantity,
                ISNULL(SUM(D2.D2_CUSTO1), 0) AS cpv_total
            FROM SD2010 D2
            LEFT JOIN SB1010 SB1
                ON SB1.D_E_L_E_T_ = ''
               AND SB1.B1_COD = D2.D2_COD
            WHERE {where_clause}
            GROUP BY D2.D2_COD
            ORDER BY cpv_total DESC, product_code
        """

        with self as repo:
            return repo.execute_query(sql, params) or []

    def get_cpv_top_documents(self, request: GetCPVRequest) -> list[dict]:
        where_clause, params = self._build_filters(request)
        limit = max(1, int(getattr(request, "top_limit", 5) or 5))

        sql = f"""
            SELECT TOP {limit}
                D2.D2_DOC AS document,
                COUNT(*) AS total_movements,
                ISNULL(SUM(D2.D2_QUANT), 0) AS total_quantity,
                ISNULL(SUM(D2.D2_CUSTO1), 0) AS cpv_total
            FROM SD2010 D2
            WHERE {where_clause}
            GROUP BY D2.D2_DOC
            ORDER BY cpv_total DESC, document
        """

        with self as repo:
            return repo.execute_query(sql, params) or []
