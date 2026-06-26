"""Fragmentos SQL compartilhados para enriquecimento de registros QI2010."""


def qi2_from_with_customer(*, table_alias: str = "nc") -> str:
    return f"""
        FROM QI2010 {table_alias} WITH (NOLOCK)
        LEFT JOIN SA1010 SA1 WITH (NOLOCK)
            ON SA1.D_E_L_E_T_ = ''
           AND SA1.A1_COD = {table_alias}.QI2_CODCLI
           AND SA1.A1_LOJA = {table_alias}.QI2_LOJCLI
    """


def qi2_prefix_where_clause(where_clause: str, *, table_alias: str = "nc") -> str:
    prefixed = where_clause.replace("QI2_", f"{table_alias}.QI2_")
    if f"{table_alias}.D_E_L_E_T_" not in prefixed:
        prefixed = prefixed.replace("D_E_L_E_T_", f"{table_alias}.D_E_L_E_T_")
    return prefixed


def qi2_detailed_description_sql(*, table_alias: str = "nc") -> str:
    ddeta_ref = f"{table_alias}.QI2_DDETA"
    return f"""
        NULLIF(
            LTRIM(RTRIM(
                ISNULL((
                    SELECT RTRIM(YP_TEXTO)
                    FROM SYP010 SYP WITH (NOLOCK)
                    WHERE SYP.YP_CHAVE = {ddeta_ref}
                      AND SYP.YP_CAMPO = 'QI2_DDETA'
                      AND SYP.D_E_L_E_T_ = ' '
                    ORDER BY YP_SEQ
                    FOR XML PATH (''), TYPE
                ).value('.', 'VARCHAR(MAX)'), '')
            )),
            ''
        ) AS detailed_description
    """
