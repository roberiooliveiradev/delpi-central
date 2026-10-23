"""X4.FIELDS.E6 — read-only investigation probe (DELPI_TST01 only).

Reúne evidência antes dos retestes PUT e do contrato de catálogos:

1. SX3 (X3_F3/X3_CBOX/X3_VLDUSER/X3_WHEN/X3_RELACAO) dos campos pendentes
   ``simp_regime_code`` (A2_REGESIM), ``linked_customer_code`` (A2_CLIENTE),
   ``linked_customer_store`` (A2_LOJCLI) e dos campos de referência dos
   catálogos (A2_TRANSP, A2_SATIV1, A2_CODADM, A2_NUMRA, A2_ZTABPRC,
   A2_GRPTRIB, A2_RISCO).
2. SA1010 elegível (clientes ≠ 000001) para prova de vínculo composto.
3. Colunas disponíveis nas tabelas de lookup (SA4/SAE/SRA/AIA/SA1/SX5-T3).
4. Estado atual SA2 dos fornecedores de ensaio.

SOMENTE LEITURA — nenhum INSERT/UPDATE/DELETE; recusa ambientes cujo
banco resolvido não seja DELPI_TST01.

Uso (dentro do container api-delpi):
    docker exec -e PYTHONPATH=/app delpi-api-delpi \
        python scripts/protheus_supplier_e6_investigation.py
"""

from __future__ import annotations

import json
import sys

from app.infrastructure.providers.totvs.connection_pool import (
    create_totvs_connection,
)

TARGET_DATABASE = "DELPI_TST01"

SX3_FIELDS = [
    "A2_REGESIM",
    "A2_CLIENTE",
    "A2_LOJCLI",
    "A2_TRANSP",
    "A2_SATIV1",
    "A2_CODADM",
    "A2_NUMRA",
    "A2_ZTABPRC",
    "A2_GRPTRIB",
    "A2_RISCO",
]

TEST_SUPPLIERS = ["003877", "003879", "003880", "003882"]

LOOKUP_TABLES = ["SA4010", "SAE010", "SRA010", "AIA010", "SA1010"]


def _query(cur, sql: str, params: tuple = ()) -> list[dict]:
    cur.execute(sql, params)
    desc = [d[0] for d in cur.description]
    return [dict(zip(desc, row)) for row in cur.fetchall()]


def main() -> int:
    conn = create_totvs_connection()
    try:
        cur = conn.cursor()

        out: dict = {"target": TARGET_DATABASE}

        # 0) sanity — base corrente
        cur.execute("SELECT DB_NAME() AS db")
        out["connected_db"] = cur.fetchone()[0]

        # 1) SX3 dos campos
        marks = ",".join("?" * len(SX3_FIELDS))
        out["sx3"] = _query(
            cur,
            f"""
            SELECT X3_CAMPO, X3_TIPO, X3_TAMANHO, X3_F3, X3_CBOX,
                   X3_WHEN, X3_VLDUSER, X3_RELACAO, X3_RESERV
            FROM {TARGET_DATABASE}.dbo.SX3010
            WHERE X3_ARQUIVO = 'SA2' AND X3_CAMPO IN ({marks})
              AND D_E_L_E_T_ = ''
            """,
            tuple(SX3_FIELDS),
        )

        # 2) SA1010 elegível — clientes distintos de 000001
        out["sa1_distinct"] = _query(
            cur,
            f"""
            SELECT TOP 10 A1_COD, A1_LOJA, RTRIM(A1_NOME) AS A1_NOME, A1_EST
            FROM {TARGET_DATABASE}.dbo.SA1010
            WHERE D_E_L_E_T_ = '' AND A1_COD <> '000001'
            ORDER BY A1_COD, A1_LOJA
            """,
        )
        out["sa1_count"] = _query(
            cur,
            f"""
            SELECT COUNT(DISTINCT A1_COD) AS customers, COUNT(*) AS rows_cnt
            FROM {TARGET_DATABASE}.dbo.SA1010
            WHERE D_E_L_E_T_ = ''
            """,
        )

        # 3) Domínios SX5 relevantes (regime SIMP pode ser tabela SX5)
        for tbl in ("12", "T3"):
            out[f"sx5_{tbl}"] = _query(
                cur,
                f"""
                SELECT TOP 15 X5_CHAVE, RTRIM(X5_DESCRI) AS X5_DESCRI
                FROM {TARGET_DATABASE}.dbo.SX5010
                WHERE X5_TABELA = ? AND X5_FILIAL = '' AND D_E_L_E_T_ = ''
                ORDER BY X5_CHAVE
                """,
                (tbl,),
            )

        # 4) Colunas das tabelas de lookup (TOP 1 para descobrir schema)
        for tbl in LOOKUP_TABLES:
            try:
                rows = _query(
                    cur,
                    f"SELECT TOP 1 * FROM {TARGET_DATABASE}.dbo.{tbl} "
                    "WHERE D_E_L_E_T_ = ''",
                )
                out[f"{tbl}_cols"] = sorted(rows[0].keys()) if rows else []
                out[f"{tbl}_sample"] = rows[0] if rows else None
            except Exception as exc:  # noqa: BLE001 — probe tolerante
                out[f"{tbl}_cols"] = f"ERROR: {exc}"

        # 5) Estado atual SA2 dos fornecedores de ensaio
        for code in TEST_SUPPLIERS:
            out[f"sa2_{code}"] = _query(
                cur,
                f"""
                SELECT A2_COD, A2_LOJA, A2_REGESIM, A2_CLIENTE, A2_LOJCLI,
                       A2_RISCO, A2_GRPTRIB
                FROM {TARGET_DATABASE}.dbo.SA2010
                WHERE A2_COD = ? AND D_E_L_E_T_ = ''
                """,
                (code,),
            )

        json.dump(out, sys.stdout, ensure_ascii=False, indent=2, default=str)
        sys.stdout.write("\n")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
