"""G3.7 — shadow parity: fixtures sintéticas geradas pelo código LEGADO.

`fixtures/lmp_shadow_fixtures.json` foi gerado executando
`LMPBusinessRules.get_dashboard_status` real da api-delpi (HEAD do G3)
sobre os cenários obrigatórios — as expectativas são outputs reais do
owner anterior, não valores escritos à mão.

Comparação: Engineering API domain (enrich_fact) × expected legado,
tolerância 0 após normalização de tipos (compare_items).

REAL_SHADOW = TEST_NOT_RUN — sem ambiente autorizado com dados TOTVS
reais; paridade de produção permanece gate de runtime da G4.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from engineering_app.application.models.lmp import LmpFact
from engineering_app.application.use_cases.list_lmps_dashboard import (
    enrich_fact,
)
from engineering_app.domain.lmp.parity import (
    compare_items,
    compare_summary,
)
from engineering_app.domain.lmp.dashboard_aggregates import compute_summary

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "lmp_shadow_fixtures.json"

# Campos determinísticos comparados — chaveado por regra (ver parity.py).
COMPARE_FIELDS = (
    "listing_kind",
    "nivel",
    "dias_uteis_sla",
    "sla_minutos",
    "data_limite",
    "lead_time_util",
    "status",
)


def _fact_from_legacy_row(row: dict) -> LmpFact:
    """Mapeia a linha legada (summary dataset) para o fato facts G2.

    Flags derivados declarados consistentes com o row: amostra ⇒
    has_sample_anchor; FINALIZADA ⇒ has_lmp_finalized.
    """
    status = row.get("engineering_status")
    kind = row.get("listing_kind")
    return LmpFact.from_dict(
        {
            "branch": row.get("branch"),
            "sale_number": row.get("sale_number"),
            "sale_description": row.get("sale_description"),
            "listing_kind_source": kind,
            "listing_kind": kind,
            "has_sample_anchor": kind == "AMOSTRA",
            "has_lmp_finalized": status == "FINALIZADA",
            "sample_eng_minutes": (
                row.get("engineering_total_minutes") or 0
            )
            if kind == "AMOSTRA"
            else 0,
            "residence_minutes": row.get("engineering_total_minutes"),
            "start_date": row.get("start_date"),
            "end_date": row.get("end_date"),
            "homolog_revision": row.get("homolog_revision"),
            "measurement_revision": row.get("measurement_revision"),
            "homolog_date": row.get("homolog_date"),
            "cycle_index": row.get("cycle_index") or 1,
            "engineering_status": status,
            "qtd_engineering_entries": 1,
            "qtd_engineering_closed": 1 if status == "FINALIZADA" else 0,
            "qtd_advanced_from_engineering": 0,
            "qtd_returned_from_engineering": 1 if status == "RETORNADA" else 0,
            "qtd_pi": row.get("qtd_pi") or 0,
        }
    )


def test_shadow_parity_tolerancia_zero():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) >= 14  # cenários obrigatórios da G3.7

    expected_items = []
    actual_items = []
    for case in cases:
        expected_items.append(case["expected_item"])
        item = enrich_fact(_fact_from_legacy_row(case["legacy_row"]))
        # asdict (não to_dict): compara valores internos YYYYMMDD,
        # não a serialização ISO da borda HTTP.
        actual_items.append(asdict(item))

    report = compare_items(expected_items, actual_items)
    assert report.compared == len(cases)
    assert report.passed, (
        "Divergências de paridade:\n"
        + "\n".join(
            f"  {d.rule_id} {d.field} key={d.key} "
            f"expected={d.expected} actual={d.actual}"
            for d in report.divergences
        )
    )


def test_shadow_parity_summary_aggregation():
    """R09/R10 — KPIs sobre o universo LMP do corpus (mesmas linhas)."""
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    lmp_cases = [
        c
        for c in data["cases"]
        if c["expected_item"]["listing_kind"] == "LMP"
    ]
    items = [
        enrich_fact(_fact_from_legacy_row(c["legacy_row"])).to_dict()
        for c in lmp_cases
    ]
    actual = compute_summary(
        [
            type("I", (), item)  # duck-type com atributos usados pelo compute
            for item in items
        ],
        total_items=len(items),
    )
    # Expected: mesma fórmula legada aplicada aos outputs do legado.
    pontuais = len(
        [c for c in lmp_cases if c["expected_item"]["status"] != "Atrasado"]
    )
    leads = [
        c["expected_item"]["lead_time_util"]
        for c in lmp_cases
        if c["expected_item"]["lead_time_util"] is not None
    ]
    expected = {
        "total_lmps": len(lmp_cases),
        "total_items": len(items),
        "percent_dentro_prazo": round(pontuais / len(lmp_cases) * 100, 2),
        "avg_lead_time": round(sum(leads) / len(leads), 2) if leads else 0,
    }
    report = compare_summary(expected, actual)
    assert report.passed
