#!/usr/bin/env python3
"""Compara taxa de conversão antiga (ganha só por AD1_DATA) vs nova (AD1_DTFIM no período).

Uso (container com acesso ao TOTVS):
  docker exec delpi-api-delpi python scripts/validate_commercial_closing_rate_dtfim.py \\
    --start 2026-01-01 --end 2026-06-23

Saída: totais do denominador (abertas), numerador legado, numerador novo e amostra de OVs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domain.services.commercial_proposal_status import WON_STATUS_CODE
from app.infrastructure.persistence.totvs.commercial_repositories.sales_conversion_rate_repository import (
    SalesConversionRateRepository,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


def _new_won_sql(branch: str | None, start: str, end: str) -> tuple[str, tuple]:
    qb = QueryBuilder()
    qb.raw("AD1.D_E_L_E_T_ = ''")
    if branch:
        qb.eq("AD1.AD1_FILIAL", branch)
    qb.date_range("AD1.AD1_DATA", start, end)
    where_clause, where_params = qb.build()

    won_qb = QueryBuilder()
    won_qb.raw(f"AD1_STATUS = '{WON_STATUS_CODE}'")
    won_qb.raw("AD1_DTFIM IS NOT NULL")
    won_qb.raw("RTRIM(CAST(AD1_DTFIM AS VARCHAR(20))) <> ''")
    won_qb.date_range("AD1_DTFIM", start, end)
    won_clause, won_params = won_qb.build()

    sql = f"""
        WITH ovs_opened AS (
            SELECT DISTINCT
                AD1.AD1_FILIAL,
                AD1.AD1_NROPOR,
                AD1.AD1_REVISA,
                AD1.AD1_DATA,
                AD1.AD1_DTFIM,
                AD1.AD1_STATUS
            FROM AD1010 AD1
            WHERE {where_clause}
        )
        SELECT
            COUNT(*) AS qtd_proposals,
            SUM(CASE WHEN {won_clause} THEN 1 ELSE 0 END) AS qtd_won_new,
            CAST(
                CASE
                    WHEN COUNT(*) = 0 THEN 0
                    ELSE SUM(CASE WHEN {won_clause} THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                END
            AS DECIMAL(10, 2)) AS sales_conversion_rate_pct
        FROM ovs_opened
    """
    params = tuple(where_params) + tuple(won_params) + tuple(won_params)
    return sql, params


def _legacy_won_sql(branch: str | None, start: str, end: str) -> tuple[str, tuple]:
    qb = QueryBuilder()
    qb.raw("AD1.D_E_L_E_T_ = ''")
    if branch:
        qb.eq("AD1.AD1_FILIAL", branch)
    qb.date_range("AD1.AD1_DATA", start, end)
    where_clause, where_params = qb.build()
    sql = f"""
        WITH ovs_opened AS (
            SELECT DISTINCT
                AD1.AD1_FILIAL,
                AD1.AD1_NROPOR,
                AD1.AD1_REVISA,
                AD1.AD1_DATA,
                AD1.AD1_DTFIM,
                AD1.AD1_STATUS
            FROM AD1010 AD1
            WHERE {where_clause}
        )
        SELECT
            COUNT(*) AS qtd_proposals,
            SUM(CASE WHEN AD1_STATUS = '{WON_STATUS_CODE}' THEN 1 ELSE 0 END) AS qtd_won_legacy
        FROM ovs_opened
    """
    return sql, tuple(where_params)


def _sample_won_closed_sql(branch: str | None, start: str, end: str) -> tuple[str, tuple]:
    qb = QueryBuilder()
    qb.raw("AD1.D_E_L_E_T_ = ''")
    if branch:
        qb.eq("AD1.AD1_FILIAL", branch)
    qb.date_range("AD1.AD1_DATA", start, end)
    open_where, open_params = qb.build()

    won_qb = QueryBuilder()
    won_qb.raw(f"AD1_STATUS = '{WON_STATUS_CODE}'")
    won_qb.raw("AD1_DTFIM IS NOT NULL")
    won_qb.raw("RTRIM(CAST(AD1_DTFIM AS VARCHAR(20))) <> ''")
    won_qb.date_range("AD1_DTFIM", start, end)
    won_clause, won_params = won_qb.build()

    sql = f"""
        WITH ovs_opened AS (
            SELECT DISTINCT
                AD1.AD1_FILIAL,
                AD1.AD1_NROPOR,
                AD1.AD1_REVISA,
                AD1.AD1_DATA,
                AD1.AD1_DTFIM,
                AD1.AD1_STATUS
            FROM AD1010 AD1
            WHERE {open_where}
        )
        SELECT TOP 15
            RTRIM(AD1_FILIAL) AS branch,
            RTRIM(AD1_NROPOR) AS proposal_number,
            RTRIM(AD1_REVISA) AS revision,
            AD1_DATA AS open_date,
            AD1_DTFIM AS close_date,
            RTRIM(AD1_STATUS) AS status_code,
            CASE WHEN {won_clause} THEN 1 ELSE 0 END AS counts_as_won_new
        FROM ovs_opened
        WHERE AD1_STATUS = '{WON_STATUS_CODE}'
           OR (AD1_DTFIM IS NOT NULL AND RTRIM(CAST(AD1_DTFIM AS VARCHAR(20))) <> '')
        ORDER BY AD1_DTFIM DESC, AD1_NROPOR DESC
    """
    return sql, tuple(open_params) + tuple(won_params)


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida closing-rate com AD1_DTFIM")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--branch", default=None, help="Filial 01/02 ou omitir consolidado")
    args = parser.parse_args()

    repo = SalesConversionRateRepository()

    with repo:
        new_sql, new_params = _new_won_sql(args.branch, args.start, args.end)
        new = repo.execute_one(new_sql, new_params) or {}
        legacy_sql, legacy_params = _legacy_won_sql(args.branch, args.start, args.end)
        legacy = repo.execute_one(legacy_sql, legacy_params) or {}
        sample_sql, sample_params = _sample_won_closed_sql(args.branch, args.start, args.end)
        sample = repo.execute_query(sample_sql, sample_params)

        report = {
            "period": {"start": args.start, "end": args.end, "branch": args.branch or "consolidated"},
            "qtd_proposals_opened": int(new.get("qtd_proposals") or 0),
            "qtd_won_legacy_by_open_date_only": int(legacy.get("qtd_won_legacy") or 0),
            "qtd_won_new_by_close_date": int(new.get("qtd_won_new") or 0),
            "sales_conversion_rate_pct": float(new.get("sales_conversion_rate_pct") or 0),
            "sample_rows": sample,
        }

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
