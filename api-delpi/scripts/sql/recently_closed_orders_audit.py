#!/usr/bin/env python3
"""Audit recently-closed Kanban SQL vs TOTVS SC5/SC6.

Run: docker exec delpi-api-delpi python /app/scripts/sql/recently_closed_orders_audit.py
"""
from __future__ import annotations

import os
import sys

import pyodbc


def connect():
    host = os.environ["TOTVS_DB_HOST"]
    port = os.environ.get("TOTVS_DB_PORT", "1433")
    db = os.environ["TOTVS_DB_DATABASE"]
    user = os.environ["TOTVS_DB_USER"]
    pwd = os.environ["TOTVS_DB_PASSWORD"]
    last_err = None
    for driver in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "FreeTDS"):
        if driver == "FreeTDS":
            conn_str = (
                f"DRIVER={{FreeTDS}};SERVER={host};PORT={port};DATABASE={db};"
                f"UID={user};PWD={pwd};TDS_Version=7.4;"
            )
        else:
            conn_str = (
                f"DRIVER={{{driver}}};SERVER={host},{port};DATABASE={db};UID={user};PWD={pwd};"
                "TrustServerCertificate=yes;Encrypt=no;"
            )
        try:
            return pyodbc.connect(conn_str, timeout=60)
        except Exception as exc:  # noqa: BLE001
            last_err = exc
    raise SystemExit(f"connect failed: {last_err}")


def cols(cur, table: str, q: str | None = None) -> list[str]:
    sql = """
        SELECT c.name
        FROM sys.columns c
        INNER JOIN sys.tables t ON t.object_id = c.object_id
        WHERE t.name = ?
    """
    params: list = [table]
    if q:
        sql += " AND UPPER(c.name) LIKE ?"
        params.append(f"%{q.upper()}%")
    sql += " ORDER BY c.column_id"
    cur.execute(sql, params)
    return [str(r[0]).strip() for r in cur.fetchall()]


def scalar(cur, sql: str, params=()):
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else None


def main() -> int:
    conn = connect()
    cur = conn.cursor()
    print("=== SC6010 columns (QTD/ENTREG/DAT) ===")
    for name in cols(cur, "SC6010", "QTD") + cols(cur, "SC6010", "ENTREG") + cols(cur, "SC6010", "DAT"):
        print(f"  {name}")
    print("=== SC5010 date-ish ===")
    for name in cols(cur, "SC5010", "EMIS") + cols(cur, "SC5010", "DAT") + cols(cur, "SC5010", "FATA"):
        print(f"  {name}")

    print("\n=== Counts (filial 01/02, not deleted) ===")
    probes = [
        (
            "fully_delivered_any_emission",
            """
            SELECT COUNT(*) FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
              ON C5.C5_FILIAL = C6.C6_FILIAL
             AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
             AND C5.D_E_L_E_T_ = ' '
            WHERE C6.D_E_L_E_T_ = ' '
              AND C5.C5_FILIAL IN ('01','02')
              AND C6.C6_QTDENT > 0
              AND (C6.C6_QTDVEN - C6.C6_QTDENT) <= 0
            """,
            (),
        ),
        (
            "current_api_filter_emissao_30d",
            """
            SELECT COUNT(*) FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
              ON C5.C5_FILIAL = C6.C6_FILIAL
             AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
             AND C5.D_E_L_E_T_ = ' '
            WHERE C6.D_E_L_E_T_ = ' '
              AND C5.C5_FILIAL IN ('01','02')
              AND C6.C6_QTDENT > 0
              AND (C6.C6_QTDVEN - C6.C6_QTDENT) <= 0
              AND C5.C5_EMISSAO >= CONVERT(VARCHAR(8), DATEADD(DAY, -30, GETDATE()), 112)
            """,
            (),
        ),
        (
            "current_api_filter_emissao_90d",
            """
            SELECT COUNT(*) FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
              ON C5.C5_FILIAL = C6.C6_FILIAL
             AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
             AND C5.D_E_L_E_T_ = ' '
            WHERE C6.D_E_L_E_T_ = ' '
              AND C5.C5_FILIAL IN ('01','02')
              AND C6.C6_QTDENT > 0
              AND (C6.C6_QTDVEN - C6.C6_QTDENT) <= 0
              AND C5.C5_EMISSAO >= CONVERT(VARCHAR(8), DATEADD(DAY, -90, GETDATE()), 112)
            """,
            (),
        ),
        (
            "fully_delivered_entreg_30d",
            """
            SELECT COUNT(*) FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
              ON C5.C5_FILIAL = C6.C6_FILIAL
             AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
             AND C5.D_E_L_E_T_ = ' '
            WHERE C6.D_E_L_E_T_ = ' '
              AND C5.C5_FILIAL IN ('01','02')
              AND C6.C6_QTDENT > 0
              AND (C6.C6_QTDVEN - C6.C6_QTDENT) <= 0
              AND NULLIF(RTRIM(C6.C6_ENTREG), '') IS NOT NULL
              AND TRY_CONVERT(DATE, NULLIF(RTRIM(C6.C6_ENTREG), ''), 112)
                    >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
            """,
            (),
        ),
        (
            "fully_delivered_entreg_90d",
            """
            SELECT COUNT(*) FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
              ON C5.C5_FILIAL = C6.C6_FILIAL
             AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
             AND C5.D_E_L_E_T_ = ' '
            WHERE C6.D_E_L_E_T_ = ' '
              AND C5.C5_FILIAL IN ('01','02')
              AND C6.C6_QTDENT > 0
              AND (C6.C6_QTDVEN - C6.C6_QTDENT) <= 0
              AND NULLIF(RTRIM(C6.C6_ENTREG), '') IS NOT NULL
              AND TRY_CONVERT(DATE, NULLIF(RTRIM(C6.C6_ENTREG), ''), 112)
                    >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE))
            """,
            (),
        ),
        (
            "fully_delivered_datfat_30d",
            """
            SELECT COUNT(*) FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
              ON C5.C5_FILIAL = C6.C6_FILIAL
             AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
             AND C5.D_E_L_E_T_ = ' '
            WHERE C6.D_E_L_E_T_ = ' '
              AND C5.C5_FILIAL IN ('01','02')
              AND C6.C6_QTDENT > 0
              AND (C6.C6_QTDVEN - C6.C6_QTDENT) <= 0
              AND NULLIF(RTRIM(C6.C6_DATFAT), '') IS NOT NULL
              AND TRY_CONVERT(DATE, NULLIF(RTRIM(C6.C6_DATFAT), ''), 112)
                    >= DATEADD(DAY, -30, CAST(GETDATE() AS DATE))
            """,
            (),
        ),
        (
            "fully_delivered_datfat_90d",
            """
            SELECT COUNT(*) FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
              ON C5.C5_FILIAL = C6.C6_FILIAL
             AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
             AND C5.D_E_L_E_T_ = ' '
            WHERE C6.D_E_L_E_T_ = ' '
              AND C5.C5_FILIAL IN ('01','02')
              AND C6.C6_QTDENT > 0
              AND (C6.C6_QTDVEN - C6.C6_QTDENT) <= 0
              AND NULLIF(RTRIM(C6.C6_DATFAT), '') IS NOT NULL
              AND TRY_CONVERT(DATE, NULLIF(RTRIM(C6.C6_DATFAT), ''), 112)
                    >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE))
            """,
            (),
        ),
        (
            "open_lines_saldo_gt_0",
            """
            SELECT COUNT(*) FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
              ON C5.C5_FILIAL = C6.C6_FILIAL
             AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
             AND C5.D_E_L_E_T_ = ' '
            WHERE C6.D_E_L_E_T_ = ' '
              AND C5.C5_FILIAL IN ('01','02')
              AND (C6.C6_QTDVEN - C6.C6_QTDENT) > 0
            """,
            (),
        ),
    ]
    for label, sql, params in probes:
        n = scalar(cur, sql, params)
        print(f"  {label}: {n}")

    print("\n=== Sample TOP 5 by C6_ENTREG (fully delivered, 90d) ===")
    cur.execute(
        """
        SELECT TOP 5
            RTRIM(C5.C5_FILIAL) AS filial,
            RTRIM(C5.C5_NUM) AS pedido,
            RTRIM(C6.C6_ITEM) AS linha,
            RTRIM(C5.C5_EMISSAO) AS emissao,
            RTRIM(C6.C6_ENTREG) AS entreg,
            CAST(C6.C6_QTDVEN AS FLOAT) AS qtdven,
            CAST(C6.C6_QTDENT AS FLOAT) AS qtdent
        FROM SC6010 C6 WITH (NOLOCK)
        INNER JOIN SC5010 C5 WITH (NOLOCK)
          ON C5.C5_FILIAL = C6.C6_FILIAL
         AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
         AND C5.D_E_L_E_T_ = ' '
        WHERE C6.D_E_L_E_T_ = ' '
          AND C5.C5_FILIAL IN ('01','02')
          AND C6.C6_QTDENT > 0
          AND (C6.C6_QTDVEN - C6.C6_QTDENT) <= 0
          AND NULLIF(RTRIM(C6.C6_ENTREG), '') IS NOT NULL
          AND TRY_CONVERT(DATE, NULLIF(RTRIM(C6.C6_ENTREG), ''), 112)
                >= DATEADD(DAY, -90, CAST(GETDATE() AS DATE))
        ORDER BY C6.C6_ENTREG DESC
        """
    )
    rows = cur.fetchall()
    if not rows:
        print("  (empty)")
    for r in rows:
        print(f"  {tuple(r)}")

    print("\n=== Sample TOP 5 current API filter (emissao 30d) ===")
    cur.execute(
        """
        SELECT TOP 5
            RTRIM(C5.C5_FILIAL), RTRIM(C5.C5_NUM), RTRIM(C6.C6_ITEM),
            RTRIM(C5.C5_EMISSAO), RTRIM(C6.C6_ENTREG),
            CAST(C6.C6_QTDVEN AS FLOAT), CAST(C6.C6_QTDENT AS FLOAT)
        FROM SC6010 C6 WITH (NOLOCK)
        INNER JOIN SC5010 C5 WITH (NOLOCK)
          ON C5.C5_FILIAL = C6.C6_FILIAL
         AND LTRIM(RTRIM(C5.C5_NUM)) = LTRIM(RTRIM(C6.C6_NUM))
         AND C5.D_E_L_E_T_ = ' '
        WHERE C6.D_E_L_E_T_ = ' '
          AND C5.C5_FILIAL IN ('01','02')
          AND C6.C6_QTDENT > 0
          AND (C6.C6_QTDVEN - C6.C6_QTDENT) <= 0
          AND C5.C5_EMISSAO >= CONVERT(VARCHAR(8), DATEADD(DAY, -30, GETDATE()), 112)
        ORDER BY C5.C5_EMISSAO DESC
        """
    )
    rows = cur.fetchall()
    if not rows:
        print("  (empty) ← matches empty Concluídos column if this is the only filter")
    for r in rows:
        print(f"  {tuple(r)}")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
