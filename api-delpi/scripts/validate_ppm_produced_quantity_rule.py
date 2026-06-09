"""Validação integrada: denominador PPM por CT de inspeção final (jan–mai/2026)."""
from types import SimpleNamespace

from app.infrastructure.persistence.totvs.ppm_repositories.ppm_inspection_sql_builder import (
    SQL_LIST_INSPECTION_CTS,
    append_apont_date_params,
    sql_produced_totals_by_tipo,
)
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_protheus_dates import (
    exclusive_end_date,
)
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)

MONTHS = [
    ("2026-01-01", "2026-01-31", "Jan/2026"),
    ("2026-02-01", "2026-02-28", "Feb/2026"),
    ("2026-03-01", "2026-03-31", "Mar/2026"),
    ("2026-04-01", "2026-04-30", "Abr/2026"),
    ("2026-05-01", "2026-05-31", "Mai/2026"),
]


def main() -> None:
    print("CTs de inspeção final (SHB010):")
    with PpmQueryRepository() as repo:
        for row in repo.execute_query(SQL_LIST_INSPECTION_CTS, ()) or []:
            print(f"  filial {row.get('HB_FILIAL')} | {row.get('HB_COD')} | {row.get('HB_NOME')}")

    print("\nFilial 01 — PPM get_summary (PA + PI, CT inspeção)")
    print("=" * 58)
    print(f"{'Mês':<12} {'Total (un)':>14} {'PA':>12} {'PI':>12}")
    print("-" * 58)

    acum = 0.0
    sql_by_tipo, base_params = sql_produced_totals_by_tipo(branch="01")

    for start, end, label in MONTHS:
        ini = start.replace("-", "")
        fim_ex = exclusive_end_date(end)
        req = SimpleNamespace(
            type="internal",
            branch="01",
            date_start=start,
            date_end=end,
        )
        tipo_params = tuple(
            append_apont_date_params(
                list(base_params),
                date_start=ini,
                date_end_exclusive=fim_ex,
            )
        )
        with PpmQueryRepository() as repo:
            tipos = {
                str(r.get("B1_TIPO") or "").strip(): float(r.get("total_un") or 0)
                for r in repo.execute_query(sql_by_tipo, tipo_params) or []
            }
        with PpmQueryRepository() as repo:
            summary = repo.get_summary(req)
        total = summary.total_produzido_un
        acum += total
        print(
            f"{label:<12} {total:>14,.0f} {tipos.get('PA', 0):>12,.0f} "
            f"{tipos.get('PI', 0):>12,.0f}"
        )

    print("-" * 58)
    print(f"{'Acumulado':<12} {acum:>14,.0f}")


if __name__ == "__main__":
    main()
