"""Último CT de apontamento por OP — PIs 50232xxx / 50233xxx (filial 01, jan–mar/2026)."""
from collections import defaultdict

from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)

PRODUCTS = ("50232465", "50233615", "50233616")

SQL_APONT = """
SELECT
    LTRIM(RTRIM(SH6.H6_OP)) AS op,
    LTRIM(RTRIM(SH6.H6_PRODUTO)) AS product_code,
    LTRIM(RTRIM(SH1.H1_CTRAB)) AS ct,
    LTRIM(RTRIM(HB.HB_NOME)) AS ct_nome,
    SH6.H6_OPERAC AS operac,
    SH6.H6_DTAPONT AS dt_apont,
    CAST(SH6.H6_QTDPROD AS FLOAT) * 1000 AS qtd_un
FROM SH6010 SH6
LEFT JOIN SH1010 SH1
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
LEFT JOIN SHB010 HB
    ON HB.HB_FILIAL = SH6.H6_FILIAL
   AND HB.HB_COD = SH1.H1_CTRAB
   AND HB.D_E_L_E_T_ = ' '
WHERE SH6.D_E_L_E_T_ = ' '
  AND SH6.H6_FILIAL = '01'
  AND SH6.H6_TIPO = 'P'
  AND SH6.H6_PRODUTO IN (?, ?, ?)
  AND SH6.H6_DTAPONT >= '20260101'
  AND SH6.H6_DTAPONT < '20260401'
ORDER BY SH6.H6_OP, SH6.H6_DTAPONT, SH6.H6_OPERAC, SH1.H1_CTRAB
"""


def _dt_key(raw) -> tuple:
    text = str(raw or "").strip()
    return (text, text, text)


def main() -> None:
    with PpmQueryRepository() as repo:
        rows = repo.execute_query(SQL_APONT, PRODUCTS) or []

    by_op: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_op[str(row.get("op") or "").strip()].append(row)

    last_by_op: list[dict] = []
    for op, aponts in by_op.items():
        # último apontamento cronológico da OP (desempate: operac, ct)
        last = max(
            aponts,
            key=lambda r: (
                str(r.get("dt_apont") or ""),
                str(r.get("operac") or ""),
                str(r.get("ct") or ""),
            ),
        )
        last_by_op.append(
            {
                "op": op,
                "product_code": str(last.get("product_code") or "").strip(),
                "last_ct": str(last.get("ct") or "").strip(),
                "last_ct_nome": str(last.get("ct_nome") or "").strip(),
                "last_dt": str(last.get("dt_apont") or "").strip(),
                "last_operac": str(last.get("operac") or "").strip(),
                "last_qtd_un": float(last.get("qtd_un") or 0),
                "apont_count": len(aponts),
            }
        )

    # Agregado: quantas OPs terminam em cada CT (último apontamento)
    last_ct_agg: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"ops": 0, "qtd_last": 0.0}
    )
    for item in last_by_op:
        key = (item["product_code"], item["last_ct"])
        last_ct_agg[key]["ops"] += 1
        last_ct_agg[key]["qtd_last"] += item["last_qtd_un"]

    print("=" * 78)
    print("ÚLTIMO CT por OP (jan–mar/2026, filial 01) — PIs 50232465/50233615/50233616")
    print("Critério: maior H6_DTAPONT; desempate H6_OPERAC, H1_CTRAB")
    print("=" * 78)
    print(f"Total OPs distintas: {len(last_by_op)}")
    print(f"Total linhas apontamento: {len(rows)}")
    print()

    print("--- Último CT por produto (contagem de OPs) ---")
    print(f"{'Produto':<10} {'Último CT':<8} {'Nome CT':<35} {'OPs':>5} {'Σ qtd último':>14}")
    print("-" * 78)
    for (product, ct), data in sorted(
        last_ct_agg.items(),
        key=lambda x: (-x[1]["ops"], x[0][0], x[0][1]),
    ):
        nome = ""
        for item in last_by_op:
            if item["product_code"] == product and item["last_ct"] == ct:
                nome = item["last_ct_nome"][:35]
                break
        print(
            f"{product:<10} {ct:<8} {nome:<35} {data['ops']:>5} "
            f"{data['qtd_last']:>14,.0f}"
        )

    print()
    print("--- Comparação: soma TOTAL por CT (todas etapas) vs ÚLTIMO CT por OP ---")
    total_by_ct: dict[tuple[str, str], float] = defaultdict(float)
    for row in rows:
        product = str(row.get("product_code") or "").strip()
        ct = str(row.get("ct") or "").strip()
        total_by_ct[(product, ct)] += float(row.get("qtd_un") or 0)

    print(f"{'Produto':<10} {'CT':<8} {'Σ todas etapas':>16} {'Σ último apont.':>16}")
    print("-" * 54)
    all_keys = set(total_by_ct) | set(last_ct_agg)
    for product, ct in sorted(all_keys):
        total = total_by_ct.get((product, ct), 0)
        last_sum = last_ct_agg.get((product, ct), {}).get("qtd_last", 0)
        if total > 0 or last_sum > 0:
            print(f"{product:<10} {ct:<8} {total:>16,.0f} {last_sum:>16,.0f}")

    print()
    print("--- Amostra: trilha completa de 5 OPs da planilha ---")
    sample_ops = [
        "24184701001",
        "24184601001",
        "24250401001",
        "24250601001",
        "24322401001",
    ]
    for op in sample_ops:
        aponts = by_op.get(op, [])
        if not aponts:
            print(f"\nOP {op}: sem apontamento")
            continue
        print(f"\nOP {op} ({len(aponts)} apontamentos):")
        for ap in sorted(
            aponts,
            key=lambda r: (
                str(r.get("dt_apont") or ""),
                str(r.get("operac") or ""),
                str(r.get("ct") or ""),
            ),
        ):
            dt = str(ap.get("dt_apont") or "")
            if len(dt) == 8:
                dt = f"{dt[0:4]}-{dt[4:6]}-{dt[6:8]}"
            print(
                f"  {dt} | op {ap.get('operac')} | {ap.get('ct')} "
                f"({str(ap.get('ct_nome') or '')[:30]}) | "
                f"{float(ap.get('qtd_un') or 0):,.0f} un"
            )
        last = max(
            aponts,
            key=lambda r: (
                str(r.get("dt_apont") or ""),
                str(r.get("operac") or ""),
                str(r.get("ct") or ""),
            ),
        )
        print(
            f"  → ÚLTIMO: {last.get('ct')} ({last.get('ct_nome')}) "
            f"em {last.get('dt_apont')} op {last.get('operac')}"
        )


if __name__ == "__main__":
    main()
