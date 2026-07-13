from datetime import date

from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class R(BaseRepository):
    pass


r = R()
today = date.today().isoformat()

with r:
    # OP apontada hoje por Carla + QPR da mesma OP
    rows = r.execute_query(
        """
        SELECT TOP 20
            RTRIM(EF.OP) AS op,
            RTRIM(EF.OPERACAO) AS oper_apont,
            RTRIM(EF.COD_OPERADOR) AS cod_apont,
            RTRIM(EF.LOGIN_OPERADOR) AS login_apont,
            RTRIM(EF.NOME_OPERADOR) AS nome_apont,
            RTRIM(QPR.QPR_OPERAC) AS oper_qpr,
            RTRIM(QPR.QPR_ENSR) AS ensr,
            RTRIM(QPR.QPR_DTMEDI) AS dt_qpr
        FROM dbo.vw_Apontamentos_Eficiencia EF WITH (NOLOCK)
        LEFT JOIN dbo.QPR010 QPR WITH (NOLOCK)
            ON QPR.D_E_L_E_T_ = ''
           AND QPR.QPR_FILIAL = EF.FILIAL
           AND RTRIM(QPR.QPR_OP) = RTRIM(EF.OP)
        WHERE EF.FILIAL = '02'
          AND EF.DATA_PRODUCAO = ?
          AND EF.STATUS_REGISTRO = 'OK'
          AND RTRIM(EF.NOME_OPERADOR) LIKE 'CARLA%'
        """,
        (today,),
    )
    print("=== Carla apont + QPR same OP ===")
    for row in rows:
        print(row)

    # SYS_USR / map COD to something
    usr = r.execute_query(
        """
        SELECT TOP 5 COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME LIKE 'SYS_USR%'
          AND (
            COLUMN_NAME LIKE '%COD%'
            OR COLUMN_NAME LIKE '%LOGIN%'
            OR COLUMN_NAME LIKE '%MATR%'
            OR COLUMN_NAME LIKE '%NOME%'
            OR COLUMN_NAME LIKE '%ID%'
          )
        """
    )
    print("SYS_USR cols", usr)

    # Try RAJ / SRA employee
    for table in ("RAJ010", "SRA010", "SQB010", "AJ2010"):
        exists = r.execute_one(
            """
            SELECT COUNT(*) AS c
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = ?
            """,
            (table,),
        )
        print("table", table, exists)

    # How EF view gets COD - inspect nearby. Try match ensr padded
    pad = r.execute_query(
        """
        SELECT TOP 10
            RTRIM(EF.COD_OPERADOR) AS cod,
            RTRIM(EF.LOGIN_OPERADOR) AS login,
            RTRIM(EF.NOME_OPERADOR) AS nome,
            RTRIM(QPR.QPR_ENSR) AS ensr
        FROM dbo.vw_Apontamentos_Eficiencia EF WITH (NOLOCK)
        INNER JOIN dbo.QPR010 QPR WITH (NOLOCK)
            ON QPR.D_E_L_E_T_ = ''
           AND QPR.QPR_FILIAL = EF.FILIAL
           AND RTRIM(QPR.QPR_OP) = RTRIM(EF.OP)
           AND RTRIM(QPR.QPR_OPERAC) = RTRIM(EF.OPERACAO)
           AND (
                RIGHT('000000' + RTRIM(QPR.QPR_ENSR), 6) = RIGHT('000000' + RTRIM(EF.COD_OPERADOR), 6)
             OR RTRIM(QPR.QPR_ENSR) = RIGHT(RTRIM(EF.COD_OPERADOR), 5)
           )
        WHERE EF.DATA_PRODUCAO = ?
          AND EF.STATUS_REGISTRO = 'OK'
        """,
        (today,),
    )
    print("=== padded matches today ===", len(pad))
    for row in pad:
        print(row)

    # View definition fragment for Matricula
    try:
        defn = r.execute_one(
            """
            SELECT OBJECT_DEFINITION(OBJECT_ID('dbo.vw_minha_delpi_inspecoes_processo_historico_tela')) AS d
            """
        )
        text = (defn or {}).get("d") or ""
        idx = text.upper().find("MATRICULA")
        print("view snippet", text[max(0, idx - 200) : idx + 400] if idx >= 0 else text[:500])
    except Exception as exc:
        print("defn err", exc)
