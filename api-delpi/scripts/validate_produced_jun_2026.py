"""Validação pontual: total produzido filial 01, 2026-06-01 → 2026-06-09."""

from __future__ import annotations

from types import SimpleNamespace

from app.infrastructure.persistence.totvs.ppm_repositories.ppm_inspection_sql_builder import (
    SQL_LIST_INSPECTION_CTS,
    append_apont_date_params,
    build_inspection_apont_ctes,
    sql_produced_totals_by_tipo,
)
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_protheus_dates import (
    exclusive_end_date,
)
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_production_sql import (
    CT_INSPECAO_JOIN,
    SH1_RECURSO_JOIN,
)
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)

BRANCH = "01"
DATE_START = "2026-06-01"
DATE_END = "2026-06-09"


def main() -> None:
    ini = DATE_START.replace("-", "")
    fim_ex = exclusive_end_date(DATE_END)

    print("=== Parâmetros ===")
    print(f"Filial: {BRANCH}")
    print(f"Período API: {DATE_START} → {DATE_END}")
    print(f"Protheus: H6_DTAPONT >= {ini} AND H6_DTAPONT < {fim_ex}")

    print("\n=== CT inspeção final (filial 01) ===")
    with PpmQueryRepository() as repo:
        rows = repo.execute_query(SQL_LIST_INSPECTION_CTS, ()) or []
    for row in rows:
        if str(row.get("HB_FILIAL")).strip() == BRANCH:
            print(f"  {row.get('HB_COD')} | {row.get('HB_NOME')}")

    req = SimpleNamespace(
        type="internal",
        branch=BRANCH,
        date_start=DATE_START,
        date_end=DATE_END,
    )
    with PpmQueryRepository() as repo:
        summary = repo.get_summary(req)

    print("\n=== get_summary (rota PPM / dashboard) ===")
    print(f"  total_produzido_un: {summary.total_produzido_un:,.2f}")
    print(f"  total_produzido_milheiro: {summary.total_produzido_milheiro:,.4f}")
    print(f"  total_devolvido_un: {summary.total_devolvido_un:,.2f}")
    print(f"  ppm: {summary.ppm:,.2f}")
    ppm_manual = (
        summary.total_devolvido_un / summary.total_produzido_un * 1_000_000
        if summary.total_produzido_un
        else 0
    )
    print(f"  ppm manual (253/29124×10⁶): {ppm_manual:,.2f}")

    sql_by_tipo, base_params = sql_produced_totals_by_tipo(branch=BRANCH)
    tipo_params = tuple(
        append_apont_date_params(
            list(base_params),
            date_start=ini,
            date_end_exclusive=fim_ex,
        )
    )
    with PpmQueryRepository() as repo:
        tipos = repo.execute_query(sql_by_tipo, tipo_params) or []

    print("\n=== Por tipo (PA + PI) ===")
    pa = pi = 0.0
    for row in tipos:
        tipo = str(row.get("B1_TIPO") or "").strip()
        value = float(row.get("total_un") or 0)
        print(f"  {tipo}: {value:,.2f} un")
        if tipo == "PA":
            pa = value
        if tipo == "PI":
            pi = value
    print(f"  SOMA: {pa + pi:,.2f} un")

    ctes = build_inspection_apont_ctes(branch=BRANCH)
    params = tuple(
        append_apont_date_params(
            ctes.params,
            date_start=ini,
            date_end_exclusive=fim_ex,
        )
    )
    sql_detail = f"""
        WITH
        {ctes.ct_inspecao_cte.strip()},
        {ctes.apont_inspecao_cte.strip()}
        SELECT
            LTRIM(RTRIM(ai.H6_PRODUTO)) AS produto,
            ai.B1_TIPO AS tipo,
            MAX(LTRIM(RTRIM(SB1.B1_DESC))) AS descricao,
            SUM(ai.qtd_produzida_op) * 1000 AS produzido_un,
            COUNT(DISTINCT ai.H6_OP) AS ops
        FROM apont_inspecao ai
        INNER JOIN SB1010 SB1
            ON SB1.B1_COD = ai.H6_PRODUTO
           AND SB1.D_E_L_E_T_ = ' '
        GROUP BY ai.H6_PRODUTO, ai.B1_TIPO
        ORDER BY produzido_un DESC
    """
    with PpmQueryRepository() as repo:
        products = repo.execute_query(sql_detail, params) or []

    print("\n=== Detalhe por produto (CT inspeção final) ===")
    print(f"{'Produto':<12} {'Tipo':<4} {'Produzido (un)':>16} {'OPs':>6}")
    print("-" * 44)
    total_check = 0.0
    for row in products:
        value = float(row.get("produzido_un") or 0)
        total_check += value
        print(
            f"{row.get('produto'):<12} {row.get('tipo'):<4} "
            f"{value:>16,.2f} {int(row.get('ops') or 0):>6}"
        )
    print("-" * 44)
    print(f"{'TOTAL':<17} {total_check:>16,.2f}")
    print(f"\nΔ vs summary: {total_check - summary.total_produzido_un:+.4f} un")

    sql_daily = f"""
        WITH
        {ctes.ct_inspecao_cte.strip()}
        SELECT
            SH6.H6_DTAPONT AS dia_protheus,
            SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) * 1000 AS produzido_un,
            COUNT(DISTINCT SH6.H6_OP) AS ops
        FROM SH6010 SH6
        INNER JOIN SB1010 SB1
            ON SB1.B1_COD = SH6.H6_PRODUTO
           AND SB1.D_E_L_E_T_ = ' '
           AND SB1.B1_TIPO IN ('PA', 'PI')
        {SH1_RECURSO_JOIN.strip()}
        {CT_INSPECAO_JOIN.strip()}
        WHERE
            SH6.D_E_L_E_T_ = ' '
            AND SH6.H6_FILIAL = ?
            AND SH6.H6_TIPO = 'P'
            AND SH6.H6_OP <> ''
            AND SH6.H6_PRODUTO <> ''
            AND SH6.H6_RECURSO <> ''
            AND SH6.H6_DTAPONT >= ?
            AND SH6.H6_DTAPONT < ?
        GROUP BY SH6.H6_DTAPONT
        ORDER BY SH6.H6_DTAPONT
    """
    daily_params = (BRANCH, BRANCH, ini, fim_ex)
    with PpmQueryRepository() as repo:
        daily = repo.execute_query(sql_daily, daily_params) or []

    print("\n=== Por dia (CT-70, PA+PI) ===")
    for row in daily:
        dia = str(row.get("dia_protheus") or "")
        formatted = f"{dia[6:8]}/{dia[4:6]}/{dia[0:4]}" if len(dia) == 8 else dia
        print(
            f"  {formatted}: {float(row.get('produzido_un') or 0):,.2f} un "
            f"({int(row.get('ops') or 0)} OPs)"
        )


if __name__ == "__main__":
    main()
