"""Consulta agregada de NCs por operador e defeito (GLPI #1538).

A agregação ocorre no SQL Server sobre o recorte completo, nunca sobre a
página atual da tabela de não conformidades.
"""

from app.application.dto.nonconformity.list_nonconformity_request import (
    ListNonconformityRequest,
)
from app.domain.services.quality.nonconformity_query_filter_service import (
    qi2_tipo_codes_for_filter,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.nonconformity_repositories.nonconformity_query_filters import (
    apply_nonconformity_text_filters,
)
from app.infrastructure.persistence.totvs.quality.qi2_record_sql import (
    QI2_CURRENT_REVISION_SQL,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


class NonconformityOperatorRankingRepository(BaseRepository):
    """Conta FNCs vigentes por matrícula e descrição resumida (QI2_DESCR)."""

    def count_by_operator_and_defect(
        self, request: ListNonconformityRequest
    ) -> list[dict]:
        qb = QueryBuilder()
        qb.raw("D_E_L_E_T_ = ''")
        qb.raw(QI2_CURRENT_REVISION_SQL)
        qb.raw("QI2_OPERAD IS NOT NULL AND LTRIM(RTRIM(QI2_OPERAD)) <> ''")
        qb.eq("QI2_FILIAL", request.branch)
        qb.date_range("QI2_OCORRE", request.date_start, request.date_end)
        apply_nonconformity_text_filters(
            qb,
            status=request.status,
            item_code=request.item_code,
            description=request.description,
        )
        type_codes = qi2_tipo_codes_for_filter(request.type)
        if type_codes:
            qb.in_list("QI2_TIPO", type_codes)

        where_clause, params = qb.build()
        code_sql = "LTRIM(RTRIM(QI2_OPERAD))"
        defect_sql = (
            "COALESCE(NULLIF(LTRIM(RTRIM(QI2_DESCR)), ''), 'Não informado')"
        )
        sql = f"""
            SELECT
                {code_sql} AS operator_code,
                {defect_sql} AS defect,
                COUNT(1) AS nc_count,
                -- Mesma conversão do numerador PPM/Quantidade devolvida da Qualidade.
                -- QI2_QTDDEV: quantidade devolvida/rejeitada informada na NC.
                SUM(
                    COALESCE(
                        TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'pt-BR'),
                        TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'en-US'),
                        0
                    )
                ) AS rejected_quantity
            FROM QI2010 WITH (NOLOCK)
            WHERE {where_clause}
            GROUP BY {code_sql}, {defect_sql}
        """
        with self as repo:
            return repo.execute_query(sql, params)
