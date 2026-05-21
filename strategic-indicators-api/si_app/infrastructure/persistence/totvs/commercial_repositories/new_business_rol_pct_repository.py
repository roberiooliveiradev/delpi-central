from si_app.application.dto.commercial.new_business_rol_pct_request import NewBusinessRolPctRequest
from si_app.domain.entities.commercial.new_business_rol_pct import NewBusinessRolPct
from si_app.domain.ports.commercial.new_business_rol_pct_repository_port import (
    NewBusinessRolPctRepositoryPort,
)
from si_app.infrastructure.persistence.totvs.base_repository import BaseRepository
from si_app.infrastructure.persistence.totvs.query_builder import QueryBuilder

# Grupo WEG no cadastro: código 000001 com várias lojas; fallback por nome.
WEG_CLIENT_CODE = "000001"


class NewBusinessRolPctRepository(BaseRepository, NewBusinessRolPctRepositoryPort):
    @staticmethod
    def _sql_is_weg_client() -> str:
        return f"""
            CASE
                WHEN SA1.A1_COD IS NOT NULL
                 AND (
                        RTRIM(SA1.A1_COD) = '{WEG_CLIENT_CODE}'
                     OR UPPER(RTRIM(SA1.A1_NOME)) LIKE '%WEG%'
                     OR UPPER(RTRIM(SA1.A1_NREDUZ)) LIKE '%WEG%'
                 )
                THEN 1
                ELSE 0
            END
        """

    def get_new_business_rol_pct(self, request: NewBusinessRolPctRequest) -> NewBusinessRolPct:
        faturamento_qb = QueryBuilder()
        faturamento_qb.raw("D2.D_E_L_E_T_ = ''")

        if request.branch:
            faturamento_qb.eq("D2.D2_FILIAL", request.branch)

        faturamento_qb.date_range("D2.D2_EMISSAO", request.start_date, request.end_date)
        faturamento_where_clause, faturamento_where_params = faturamento_qb.build()

        is_weg_client = self._sql_is_weg_client()

        sql = f"""
            WITH base_faturamento AS (
                SELECT
                    D2.D2_FILIAL,
                    D2.D2_CLIENTE,
                    D2.D2_LOJA,
                    ISNULL(D2.D2_TOTAL, 0) AS VALOR_ITEM,
                    ISNULL(D2.D2_VALDEV, 0) AS VALOR_DEVOLUCAO,
                    ISNULL(D2.D2_VALICM, 0) AS VALOR_ICMS,
                    ISNULL(D2.D2_VALISS, 0) AS VALOR_ISS,
                    ISNULL(D2.D2_VALPIS, 0) AS VALOR_PIS,
                    ISNULL(D2.D2_VALCOF, 0) AS VALOR_COFINS,
                    ISNULL(D2.D2_VALIPI, 0) AS VALOR_IPI,
                    ISNULL(D2.D2_DESCON, 0) + ISNULL(D2.D2_DESC, 0) AS VALOR_DESCONTO,
                    CASE
                        WHEN ISNULL(F4.F4_DUPLIC, '') = 'S'
                        THEN ISNULL(D2.D2_TOTAL, 0)
                        ELSE 0
                    END AS VALOR_FATURAMENTO,
                    {is_weg_client} AS is_weg_client
                FROM SD2010 D2
                LEFT JOIN SF4010 F4
                    ON  F4.D_E_L_E_T_ = ''
                    AND F4.F4_CODIGO  = D2.D2_TES
                    AND (
                            F4.F4_FILIAL = D2.D2_FILIAL
                         OR F4.F4_FILIAL = ''
                         OR F4.F4_FILIAL IS NULL
                    )
                LEFT JOIN SA1010 SA1
                    ON  SA1.D_E_L_E_T_ = ''
                    AND SA1.A1_COD = D2.D2_CLIENTE
                    AND SA1.A1_LOJA = D2.D2_LOJA
                WHERE {faturamento_where_clause}
            ),
            rol_por_linha AS (
                SELECT
                    BF.is_weg_client,
                    BF.VALOR_FATURAMENTO
                        - BF.VALOR_DEVOLUCAO
                        - BF.VALOR_DESCONTO
                        - (
                            BF.VALOR_ICMS + BF.VALOR_ISS + BF.VALOR_PIS
                            + BF.VALOR_COFINS + BF.VALOR_IPI
                        ) AS rol_linha
                FROM base_faturamento BF
            ),
            rol_agregado AS (
                SELECT
                    ISNULL(SUM(rol_linha), 0) AS total_rol,
                    ISNULL(SUM(CASE WHEN is_weg_client = 0 THEN rol_linha ELSE 0 END), 0) AS new_business_rol,
                    ISNULL(SUM(CASE WHEN is_weg_client = 1 THEN rol_linha ELSE 0 END), 0) AS weg_rol
                FROM rol_por_linha
            )
            SELECT
                ? AS branch,
                ? AS start_date,
                ? AS end_date,
                RA.total_rol,
                RA.new_business_rol,
                RA.weg_rol,
                CAST(
                    CASE
                        WHEN RA.total_rol = 0 THEN NULL
                        ELSE RA.new_business_rol * 100.0 / RA.total_rol
                    END
                AS DECIMAL(10, 2)) AS new_business_rol_pct
            FROM rol_agregado RA
        """

        params = faturamento_where_params + (
            request.branch or "consolidated",
            request.start_date or "",
            request.end_date or "",
        )

        with self:
            row = self.execute_one(sql, params)

        total_rol = float((row or {}).get("total_rol") or 0)
        new_business_rol = float((row or {}).get("new_business_rol") or 0)
        weg_rol = float((row or {}).get("weg_rol") or 0)
        pct_raw = (row or {}).get("new_business_rol_pct")
        new_business_rol_pct = float(pct_raw) if pct_raw is not None else None

        return NewBusinessRolPct(
            branch=(row or {}).get("branch") or request.branch,
            start_date=(row or {}).get("start_date") or request.start_date,
            end_date=(row or {}).get("end_date") or request.end_date,
            total_rol=total_rol,
            new_business_rol=new_business_rol,
            weg_rol=weg_rol,
            new_business_rol_pct=new_business_rol_pct,
        )
