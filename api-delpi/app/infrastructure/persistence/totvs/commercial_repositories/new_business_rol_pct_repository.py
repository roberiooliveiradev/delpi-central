from app.application.dto.commercial.new_business_rol_pct_request import NewBusinessRolPctRequest
from app.domain.entities.commercial.new_business_rol_pct import NewBusinessRolPct
from app.domain.ports.commercial.new_business_rol_pct_repository_port import (
    NewBusinessRolPctRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

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
        vendas_qb = QueryBuilder()
        vendas_qb.raw("D2.D_E_L_E_T_ = ''")
        if request.branch:
            vendas_qb.eq("D2.D2_FILIAL", request.branch)
        vendas_qb.date_range("D2.D2_EMISSAO", request.start_date, request.end_date)
        vendas_where, vendas_params = vendas_qb.build()

        exists_qb = QueryBuilder()
        exists_qb.date_range("D1X.D1_DTDIGIT", request.start_date, request.end_date)
        exists_where, exists_params = exists_qb.build()

        dev_qb = QueryBuilder()
        dev_qb.raw("D1.D_E_L_E_T_ = ''")
        if request.branch:
            dev_qb.eq("D1.D1_FILIAL", request.branch)
        dev_qb.date_range("D1.D1_DTDIGIT", request.start_date, request.end_date)
        dev_where, dev_params = dev_qb.build()

        is_weg_client = self._sql_is_weg_client()

        sql = f"""
            WITH VENDAS AS (
                SELECT
                    D2.D2_FILIAL,
                    D2.D2_CLIENTE,
                    D2.D2_LOJA,
                    SUM(CONVERT(FLOAT,
                        ISNULL(D2.D2_TOTAL, 0)
                        - ISNULL(D2.D2_VALICM, 0)
                        - ISNULL(D2.D2_VALIMP5, 0)
                        - ISNULL(D2.D2_VALIMP6, 0)
                    )) AS VLR_VENDA

                FROM SD2010 D2

                LEFT JOIN SA1010 A1
                    ON  A1.D_E_L_E_T_ = ''
                    AND A1.A1_COD  = D2.D2_CLIENTE
                    AND A1.A1_LOJA = D2.D2_LOJA

                LEFT JOIN SF4010 F4
                    ON  F4.D_E_L_E_T_ = ''
                    AND F4.F4_CODIGO = D2.D2_TES
                    AND (
                            F4.F4_FILIAL = D2.D2_FILIAL
                         OR F4.F4_FILIAL = ''
                         OR F4.F4_FILIAL IS NULL
                    )

                WHERE {vendas_where}
                    AND ISNULL(A1.A1_NOME, '') <> ''
                    AND ISNULL(D2.D2_TIPO, '') <> 'D'

                    AND (
                        D2.D2_CF NOT IN ('5911', '6151')
                        OR (
                            D2.D2_FILIAL = '01'
                            AND D2.D2_CF IN ('5911', '6911')
                            AND D2.D2_COD LIKE '90%'
                            AND ISNULL(F4.F4_DUPLIC, '')  = 'N'
                            AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                            AND D2.D2_UM = 'MI'
                        )
                    )

                    AND (
                        ISNULL(F4.F4_DUPLIC, '') = 'S'

                        OR (
                            ISNULL(F4.F4_DUPLIC, '')  = 'N'
                            AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                            AND ISNULL(F4.F4_FINALID, '') = 'BAIXA ESTOQUE'
                            AND D2.D2_CF  = '5927'
                            AND D2.D2_UM  = 'MI'
                            AND EXISTS (
                                SELECT 1
                                FROM SD1010 D1X
                                WHERE
                                    D1X.D_E_L_E_T_ = ''
                                    AND D1X.D1_FILIAL  = D2.D2_FILIAL
                                    AND D1X.D1_FORNECE = D2.D2_CLIENTE
                                    AND D1X.D1_LOJA    = D2.D2_LOJA
                                    AND {exists_where}
                                    AND (
                                        D1X.D1_CF IN ('1201', '2201')
                                        OR D1X.D1_TIPO = 'D'
                                    )
                            )
                        )

                        OR (
                            D2.D2_FILIAL = '01'
                            AND D2.D2_CF IN ('5911', '6911')
                            AND D2.D2_COD LIKE '90%'
                            AND ISNULL(F4.F4_DUPLIC, '')  = 'N'
                            AND ISNULL(F4.F4_ESTOQUE, '') = 'S'
                            AND D2.D2_UM = 'MI'
                        )
                    )

                GROUP BY D2.D2_FILIAL, D2.D2_CLIENTE, D2.D2_LOJA
            ),

            DEVOLUCOES AS (
                SELECT
                    D1.D1_FILIAL,
                    D1.D1_FORNECE,
                    D1.D1_LOJA,
                    SUM(CONVERT(FLOAT,
                        ISNULL(D1.D1_TOTAL, 0)
                        - ISNULL(D1.D1_VALICM, 0)
                        - ISNULL(D1.D1_VALIMP5, 0)
                        - ISNULL(D1.D1_VALIMP6, 0)
                    )) AS VLR_DEVOLUCAO

                FROM SD1010 D1

                WHERE {dev_where}
                    AND (
                        D1.D1_CF IN ('1201', '2201')
                        OR D1.D1_TIPO = 'D'
                    )

                GROUP BY D1.D1_FILIAL, D1.D1_FORNECE, D1.D1_LOJA
            ),

            ROL_POR_CLIENTE AS (
                SELECT
                    ISNULL(V.D2_CLIENTE, D.D1_FORNECE) AS COD_CLIENTE,
                    ISNULL(V.D2_LOJA, D.D1_LOJA)       AS LOJA,
                    ISNULL(V.VLR_VENDA, 0)
                    - ISNULL(D.VLR_DEVOLUCAO, 0)        AS ROL_CLIENTE
                FROM VENDAS V
                FULL OUTER JOIN DEVOLUCOES D
                    ON  D.D1_FILIAL  = V.D2_FILIAL
                    AND D.D1_FORNECE = V.D2_CLIENTE
                    AND D.D1_LOJA    = V.D2_LOJA
            ),

            ROL_CLASSIFICADO AS (
                SELECT
                    RC.ROL_CLIENTE,
                    {is_weg_client} AS is_weg_client
                FROM ROL_POR_CLIENTE RC
                LEFT JOIN SA1010 SA1
                    ON  SA1.D_E_L_E_T_ = ''
                    AND SA1.A1_COD  = RC.COD_CLIENTE
                    AND SA1.A1_LOJA = RC.LOJA
            )

            SELECT
                ? AS branch,
                ? AS start_date,
                ? AS end_date,
                ISNULL(SUM(ROL_CLIENTE), 0) AS total_rol,
                ISNULL(SUM(CASE WHEN is_weg_client = 0
                                THEN ROL_CLIENTE ELSE 0 END), 0) AS new_business_rol,
                ISNULL(SUM(CASE WHEN is_weg_client = 1
                                THEN ROL_CLIENTE ELSE 0 END), 0) AS weg_rol,
                CAST(
                    CASE
                        WHEN ISNULL(SUM(ROL_CLIENTE), 0) = 0 THEN NULL
                        ELSE SUM(CASE WHEN is_weg_client = 0
                                      THEN ROL_CLIENTE ELSE 0 END)
                             * 100.0 / SUM(ROL_CLIENTE)
                    END
                AS DECIMAL(10, 2)) AS new_business_rol_pct
            FROM ROL_CLASSIFICADO
        """

        params = vendas_params + exists_params + dev_params + (
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
