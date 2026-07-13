from datetime import date

from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class R(BaseRepository):
    pass


r = R()
today = date.today().isoformat()

with r:
    # EF view definition
    ef = r.execute_one(
        """
        SELECT OBJECT_DEFINITION(OBJECT_ID('dbo.vw_Apontamentos_Eficiencia')) AS d
        """
    )
    text = (ef or {}).get("d") or ""
    for key in ("OPERADO", "SYS_USR", "COD_OPERADOR", "LOGIN", "USR_"):
        idx = text.upper().find(key)
        if idx >= 0:
            print(f"--- EF {key} ---")
            print(text[max(0, idx - 120) : idx + 280])
            print()

    # historico view
    hv = r.execute_one(
        """
        SELECT OBJECT_DEFINITION(OBJECT_ID('dbo.vw_minha_delpi_inspecoes_processo_historico_tela')) AS d
        """
    )
    htext = (hv or {}).get("d") or ""
    print("historico def len", len(htext))
    for key in ("ENSR", "MATRICULA", "NOME_ENSAIADOR", "QPR_"):
        idx = htext.upper().find(key)
        if idx >= 0:
            print(f"--- HIST {key} ---")
            print(htext[max(0, idx - 80) : idx + 250])
            print()

    # SRA columns
    sra_cols = r.execute_query(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'SRA010'
          AND (
            COLUMN_NAME LIKE 'RA_MAT%'
            OR COLUMN_NAME LIKE 'RA_NOME%'
            OR COLUMN_NAME LIKE 'RA_LOGI%'
            OR COLUMN_NAME LIKE 'RA_COD%'
            OR COLUMN_NAME LIKE 'RA_CIP%'
            OR COLUMN_NAME LIKE 'RA_%USR%'
          )
        ORDER BY ORDINAL_POSITION
        """
    )
    print("SRA cols", sra_cols)

    # Look up Carla in SRA
    carla = r.execute_query(
        """
        SELECT TOP 5
            RTRIM(RA_MAT) AS mat,
            RTRIM(RA_NOME) AS nome
        FROM dbo.SRA010 WITH (NOLOCK)
        WHERE D_E_L_E_T_ = ''
          AND RA_NOME LIKE '%CARLA SOARES%'
        """
    )
    print("Carla SRA", carla)

    # Look up 20115 and 000177 / 177
    for mat in ("20115", "000177", "177", "20145"):
        row = r.execute_query(
            """
            SELECT TOP 3 RTRIM(RA_MAT) AS mat, RTRIM(RA_NOME) AS nome
            FROM dbo.SRA010 WITH (NOLOCK)
            WHERE D_E_L_E_T_ = '' AND RTRIM(RA_MAT) = ?
            """,
            (mat,),
        )
        print("SRA mat", mat, row)

    # SYS_USR for CARLA.JESUS
    usr = r.execute_query(
        """
        SELECT TOP 5
            RTRIM(USR_ID) AS id,
            RTRIM(USR_CODIGO) AS codigo,
            RTRIM(USR_NOME) AS nome
        FROM dbo.SYS_USR WITH (NOLOCK)
        WHERE USR_CODIGO LIKE '%CARLA%' OR USR_NOME LIKE '%CARLA SOARES%'
        """
    )
    print("SYS_USR carla", usr)

    # H6_OPERADO sample for Carla's appointment
    h6 = r.execute_query(
        """
        SELECT TOP 5
            RTRIM(H6_FILIAL) AS fil,
            RTRIM(H6_OP) AS op,
            RTRIM(H6_OPERAC) AS oper,
            RTRIM(H6_OPERADO) AS operado,
            RTRIM(H6_DTPROD) AS dt
        FROM dbo.SH6010 WITH (NOLOCK)
        WHERE D_E_L_E_T_ = ''
          AND H6_FILIAL = '02'
          AND H6_DTPROD = ?
          AND RTRIM(H6_OPERADO) IN ('000177', '177', '20145', '20115')
        """,
        (today.replace("-", ""),),
    )
    print("H6 operado filter", h6)

    h6b = r.execute_query(
        """
        SELECT TOP 5
            RTRIM(H6_OPERADO) AS operado,
            COUNT(*) AS c
        FROM dbo.SH6010 WITH (NOLOCK)
        WHERE D_E_L_E_T_ = ''
          AND H6_FILIAL = '02'
          AND H6_DTPROD = ?
        GROUP BY RTRIM(H6_OPERADO)
        ORDER BY COUNT(*) DESC
        """,
        (today.replace("-", ""),),
    )
    print("H6 operado top today", h6b)
