"""G3 — testes unitários do domínio LMP migrado (regras R01–R17, S03–S12).

Domínio puro: sem I/O, sem FastAPI, sem rede. Paridade de constantes com
a especificação canônica versionada `lmp_semantics.v1.yaml` (owner do
extraction: api-delpi; owner das regras: engineering-api).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
import yaml

from engineering_app.domain.lmp import (
    business_rules as br,
    listing_semantics as ls,
)
from engineering_app.domain.lmp.dates import parse_date
from engineering_app.domain.lmp.dashboard_aggregates import (
    build_charts,
    compute_summary,
)
from engineering_app.application.models.lmp import LmpDashboardItem

SPEC_PATH = (
    Path(__file__).resolve().parents[2]
    / "api-delpi"
    / "contracts"
    / "lmp"
    / "lmp_semantics.v1.yaml"
)


# --- R02/R01: nível e SLA -------------------------------------------------


@pytest.mark.parametrize(
    ("qtd_pi", "level", "sla_days"),
    [
        (0, "Nível 1", 4),
        (10, "Nível 1", 4),
        (11, "Nível 2", 8),
        (20, "Nível 2", 8),
        (21, "Nível 3", 20),
        (None, "Nível 1", 4),
    ],
)
def test_level_and_sla_boundaries(qtd_pi, level, sla_days):
    assert br.get_level(qtd_pi) == level
    assert br.get_sla_days(level) == sla_days


def test_sla_limit_minutes_includes_tolerance():
    # R03 — tolerância de +1 dia útil embutida no limite de status.
    assert br.get_sla_limit_minutes("Nível 1") == (4 + 1) * 1440


# --- R05: dias úteis --------------------------------------------------------


def test_add_business_days_skips_weekend():
    # Sexta 2026-05-01 + 4 dias úteis = quinta 2026-05-07.
    assert br.add_business_days(date(2026, 5, 1), 4) == date(2026, 5, 7)


def test_business_days_between():
    # Contagem inclusiva (legado): 1,4,5,6,7 mai = 5 dias úteis.
    assert br.business_days_between(date(2026, 5, 1), date(2026, 5, 7)) == 5
    # Callers guardam `end is None` (paridade legada — sem tratamento interno).
    assert br.business_days_between(date(2026, 5, 7), date(2026, 5, 1)) == 0


# --- datas: TOTVS YYYYMMDD, ISO, serial Excel -------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("20260501", date(2026, 5, 1)),
        (20260501, date(2026, 5, 1)),
        ("2026-05-01", date(2026, 5, 1)),
        ("05/01/2026", date(2026, 1, 5)),  # dd/mm/yyyy — formato Protheus
        (45789.0, date(2025, 5, 12)),  # serial Excel real
        ("", None),
        (None, None),
        ("99999999", None),
    ],
)
def test_parse_date_formats(raw, expected):
    assert parse_date(raw) == expected


# --- R04: status do dashboard ------------------------------------------------


def _status(**kw):
    return br.resolve_dashboard_status(**kw)


def test_status_returned_wins():
    assert (
        _status(
            start_date_str="20260401",
            end_date_str="20260410",
            qtd_pi=3,
            engineering_status="RETORNADA",
            engineering_total_minutes=99999,
        )
        == "Retornada"
    )


def test_status_open_never_late():
    # R04 — atraso só se decide no fechamento.
    for eng_status in ("EM_ANDAMENTO", "PARCIAL", "ABERTA", None):
        assert (
            _status(
                start_date_str="20260101",
                end_date_str=None,
                qtd_pi=30,
                engineering_status=eng_status,
                engineering_total_minutes=999999,
            )
            == "Andamento"
        )


def test_status_finished_ontime_or_semantics():
    # Pontual se data <= limite+tolerância OU minutos <= SLA+tolerância.
    base = dict(
        start_date_str="20260501",
        qtd_pi=5,  # Nível 1 → SLA 4d, limite+tolerância = 2026-05-08
        engineering_status="FINALIZADA",
    )
    assert (
        _status(**base, end_date_str="20260507", engineering_total_minutes=99999)
        == "Pontual"
    )
    assert (
        _status(**base, end_date_str="20260601", engineering_total_minutes=4000)
        == "Pontual"
    )
    assert (
        _status(**base, end_date_str="20260602", engineering_total_minutes=99999)
        == "Atrasado"
    )


def test_status_null_dates_pontual_by_minutes():
    # Sem datas, minutos dentro do limite ⇒ Pontual (OR semantics legada).
    assert (
        _status(
            start_date_str=None,
            end_date_str=None,
            qtd_pi=0,
            engineering_status="FINALIZADA",
            engineering_total_minutes=100,
        )
        == "Pontual"
    )


# --- S05/S07: classificação efetiva e residência -----------------------------


def test_effective_kind_lmp_to_sample():
    assert (
        ls.effective_listing_kind(
            anchor_kind="LMP",
            has_sample_anchor=True,
            sample_minutes=40,
            total_minutes=300,
            has_lmp_finalized=False,
        )
        == "AMOSTRA"
    )


def test_effective_kind_strict_demotes_low_residence():
    assert (
        ls.effective_listing_kind(
            anchor_kind="LMP",
            has_sample_anchor=False,
            sample_minutes=0,
            total_minutes=10,
            has_lmp_finalized=True,
            strict_residence_after_homolog=True,
        )
        == "OUTRO"
    )


@pytest.mark.parametrize(
    ("minutes", "expected"),
    [(29, False), (30, True), (31, True)],
)
def test_residence_boundary_29_30_31(minutes, expected):
    # S03 — piso de 30 minutos para LMP.
    assert (
        ls.lmp_passes_residence_filter(
            listing_kind="LMP",
            total_minutes=minutes,
            has_sample_anchor=False,
            has_lmp_finalized=True,
            has_engineering_stage=True,
        )
        is expected
    )


# --- R09–R11: agregações ------------------------------------------------------


def _item(status="Pontual", lead=5, nivel="Nível 1", kind="LMP"):
    return LmpDashboardItem(
        branch="01",
        sale_number="OV",
        sale_description="d",
        listing_kind=kind,
        start_date="20260501",
        end_date="20260507",
        nivel=nivel,
        dias_uteis_sla=4,
        sla_minutos=5760,
        engineering_total_minutes=100,
        data_limite="20260507",
        lead_time_util=lead,
        status=status,
    )


def test_summary_counts_andamento_as_ontime():
    # R09 — numerador = não-Atrasado (Andamento/Retornada contam: quirk legada).
    items = [_item("Pontual"), _item("Andamento"), _item("Atrasado"), _item("Retornada")]
    summary = compute_summary(items, total_items=4)
    assert summary["percent_dentro_prazo"] == 75.0
    assert summary["total_lmps"] == 4


def test_charts_shape():
    charts = build_charts([_item("Pontual"), _item("Atrasado", nivel="Nível 2")])
    assert {d["name"] for d in charts["levelData"]} == {
        "Nível 1",
        "Nível 2",
        "Nível 3",
    }
    assert any(
        d["name"] == "Atrasado" and d["value"] == 1 for d in charts["statusData"]
    )
    assert all("valor" in d for d in charts["leadByLevel"])


# --- R15/R16: histórico e transições -----------------------------------------


def test_enrich_history_events_marks_current_by_revision():
    from engineering_app.domain.lmp.history_enrichment import (
        enrich_history_events,
    )

    events = [
        {
            "revision": "001",
            "stage_code": "000003",
            "process_code": "ENG",
            "end_date": "20260501",
            "duration_minutes": 60,
        },
        {
            "revision": "002",
            "stage_code": "000003",
            "process_code": "ENG",
            "end_date": "",
            "duration_minutes": None,
        },
    ]
    enriched = enrich_history_events(events, reference_revision="002")
    assert [e["is_current"] for e in enriched] == [False, True]
    assert enriched[1]["is_open"] is True
    assert enriched[1]["is_engineering_flow"] is True
    assert enriched[0]["duration_display"] is not None


def test_flow_transition_detection():
    from engineering_app.domain.lmp.flow_transition import (
        detect_engineering_entry,
        detect_flow_transition,
    )

    # Entrada: estágio de engenharia sem estágio anterior.
    entry = {
        "stage_code": "000003",
        "is_engineering": True,
        "previous_stage_code": "",
        "revision": "001",
    }
    assert detect_engineering_entry(entry) is True

    # Avanço: fechado, próximo estágio fora de engenharia, mesma revisão.
    advanced = {
        "stage_code": "000003",
        "is_engineering": True,
        "end_date": "20260501",
        "revision": "001",
        "next_revision": "001",
        "next_stage_code": "000009",
        "next_process_code": "MED",
    }
    assert detect_flow_transition(advanced) == "advanced_from_engineering"

    # Retorno: próximo estágio menor, revisão diferente.
    returned = dict(advanced, next_revision="002", next_stage_code="000001")
    assert detect_flow_transition(returned) == "returned_from_engineering"


# --- Paridade de constantes com a spec canônica ------------------------------


def test_constants_match_semantics_spec():
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    by_id = {
        entry["id"]: entry
        for section in ("semantics", "business_rule_constants")
        for entry in spec.get(section, [])
    }
    s03 = by_id["S03"]["constants"]
    s07 = by_id["S07"]["constants"]
    r01 = by_id["R01"]["constants"]
    r03 = by_id["R03"]["constants"]

    assert br.SLA_TOLERANCE_DAYS == r03["sla_tolerance_days"]
    assert br.MINUTES_PER_DAY == r03["minutes_per_day"]
    assert ls.DEFAULT_MIN_RESIDENCE_MINUTES == s03[
        "min_engineering_residence_minutes"
    ]
    assert (
        ls.DEFAULT_STRICT_RESIDENCE_AFTER_HOMOLOG
        == s07["strict_residence_after_homolog"]
    )
    sla_map = {
        br.get_level(pis): br.get_sla_days(br.get_level(pis))
        for pis in (5, 15, 30)
    }
    assert sla_map == r01["sla_by_level"]
