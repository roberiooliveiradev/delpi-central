"""Filtro de OPs por periodo — playbook situacao de producao / factory-status."""

PRODUCT_PLAYBOOK_PRODUCTION_ORDER_PERIOD_FILTER_SQL = """
              AND (
                  EXISTS (
                      SELECT 1
                      FROM SH6010 H6P WITH (NOLOCK)
                      WHERE H6P.D_E_L_E_T_ = ''
                        AND H6P.H6_DTAPONT >= @DATA_INI
                        AND H6P.H6_DTAPONT < @DATA_FIM
                        AND H6P.H6_FILIAL = SC2.C2_FILIAL
                        AND H6P.H6_PRODUTO = SC2.C2_PRODUTO
                        AND (
                            H6P.H6_OP = SC2.C2_OP
                            OR H6P.H6_OP = SC2.C2_NUM + SC2.C2_ITEM + SC2.C2_SEQUEN
                        )
                  )
                  OR (
                      ISNULL(CAST(SC2.C2_QUJE AS FLOAT), 0)
                          < ISNULL(CAST(SC2.C2_QUANT AS FLOAT), 0)
                      AND (
                          SC2.C2_DATRF = ''
                          OR SC2.C2_DATRF IS NULL
                          OR SC2.C2_DATRF >= @DATA_INI
                      )
                  )
                  OR (
                      SC2.C2_DATPRI <> ''
                      AND SC2.C2_DATPRF <> ''
                      AND SC2.C2_DATPRI < @DATA_FIM
                      AND SC2.C2_DATPRF >= @DATA_INI
                  )
              )
"""
