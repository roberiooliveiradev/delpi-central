from datetime import date, timedelta

from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class R(BaseRepository):
    pass


r = R()
today = date.today().isoformat()
week_ago = (date.today() - timedelta(days=7)).isoformat()

with r:
    qpr = r.execute_query(
        """
        SELECT TOP 10
            RTRIM(QPR_FILIAL) AS fil,
            RTRIM(QPR_OP) AS op,
            RTRIM(QPR_OPERAC) AS oper,
            RTRIM(QPR_ENSR) AS ensr,
            RTRIM(QPR_DTMEDI) AS dt
        FROM dbo.QPR010 WITH (NOLOCK)
        WHERE D_E_L_E_T_ = ''
          AND QPR_FILIAL IN ('01', '02')
          AND RTRIM(ISNULL(QPR_ENSR, '')) <> ''
        ORDER BY R_E_C_N_O_ DESC
        """
    )
    print("=== QPR sample ===")
    for row in qpr:
        print(row)

    for br in ("01", "02"):
        cnt = r.execute_one(
            """
            SELECT COUNT(*) AS c
            FROM dbo.vw_Apontamentos_Eficiencia WITH (NOLOCK)
            WHERE FILIAL = ?
              AND DATA_PRODUCAO = ?
              AND STATUS_REGISTRO = 'OK'
            """,
            (br, today),
        )
        print(f"apontamentos {br} hoje", cnt)

        samp = r.execute_query(
            """
            SELECT TOP 5
                RTRIM(OP) AS op,
                RTRIM(OPERACAO) AS oper,
                RTRIM(COD_OPERADOR) AS cod,
                RTRIM(LOGIN_OPERADOR) AS login,
                RTRIM(NOME_OPERADOR) AS nome
            FROM dbo.vw_Apontamentos_Eficiencia WITH (NOLOCK)
            WHERE FILIAL = ?
              AND DATA_PRODUCAO = ?
              AND STATUS_REGISTRO = 'OK'
            """,
            (br, today),
        )
        print(f"sample apont {br}", samp)

    cruz = r.execute_query(
        """
        SELECT TOP 10
            RTRIM(EF.OP) AS op,
            RTRIM(EF.OPERACAO) AS oper,
            RTRIM(EF.COD_OPERADOR) AS cod_apont,
            RTRIM(QPR.QPR_ENSR) AS ensr,
            RTRIM(EF.NOME_OPERADOR) AS nome
        FROM dbo.vw_Apontamentos_Eficiencia EF WITH (NOLOCK)
        INNER JOIN dbo.QPR010 QPR WITH (NOLOCK)
            ON QPR.D_E_L_E_T_ = ''
           AND QPR.QPR_FILIAL = EF.FILIAL
           AND RTRIM(QPR.QPR_OP) = RTRIM(EF.OP)
           AND RTRIM(QPR.QPR_OPERAC) = RTRIM(EF.OPERACAO)
           AND RTRIM(QPR.QPR_ENSR) = RTRIM(EF.COD_OPERADOR)
        WHERE EF.DATA_PRODUCAO >= ?
          AND EF.STATUS_REGISTRO = 'OK'
        """,
        (week_ago,),
    )
    print("=== matches COD=ENSR last 7d ===", len(cruz))
    for row in cruz:
        print(row)

    cruz2 = r.execute_one(
        """
        SELECT COUNT(*) AS c
        FROM dbo.vw_Apontamentos_Eficiencia EF WITH (NOLOCK)
        WHERE EF.FILIAL = '02'
          AND EF.DATA_PRODUCAO = ?
          AND EF.STATUS_REGISTRO = 'OK'
          AND EXISTS (
            SELECT 1
            FROM dbo.QPR010 QPR WITH (NOLOCK)
            WHERE QPR.D_E_L_E_T_ = ''
              AND QPR.QPR_FILIAL = EF.FILIAL
              AND RTRIM(QPR.QPR_OP) = RTRIM(EF.OP)
              AND RTRIM(QPR.QPR_OPERAC) = RTRIM(EF.OPERACAO)
          )
        """,
        (today,),
    )
    print("fil02 hoje com algum QPR OP+op", cruz2)

    # Matricula na view historico_tela vs QPR_ENSR
    view_cols = r.execute_query(
        """
        SELECT TOP 5
            RTRIM(Ordem_Producao) AS op,
            RTRIM(Operacao) AS oper,
            RTRIM(Matricula_Ensaiador) AS mat,
            RTRIM(Nome_Ensaiador) AS nome
        FROM dbo.vw_minha_delpi_inspecoes_processo_historico_tela WITH (NOLOCK)
        WHERE Filial = '02'
          AND Data_Medicao_Date >= ?
        """,
        (week_ago,),
    )
    print("=== historico_tela ensaiador ===")
    for row in view_cols:
        print(row)
