import json
from datetime import date
from pathlib import Path

from tm_app.domain.raw_data import TransformometroRawData
from tm_app.domain.services.dashboard_calculator import DashboardCalculatorService

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> TransformometroRawData:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return TransformometroRawData(**payload)


def test_golden_baseline_melhoria_economia_bruta_positiva():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()

    rows = [
        row
        for row in calc.build_dashboard_rows(raw)
        if row["revisao_id"] == "r-melhoria" and row["competencia"] == "2025-02"
    ]
    assert len(rows) == 1
    row = rows[0]

    # tempo: 100 * (60-30)/60 * 50 = 2500
    assert row["economia_tempo"] == 2500.0
    assert row["economia_bruta"] >= 2500.0
    assert row["economia_recursos_compartilhados"] == 0.0
    assert row["economia_liquida_mes"] == row["economia_bruta"]


def test_baseline_row_economia_bruta_zero():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()

    rows = [
        row
        for row in calc.build_dashboard_rows(raw)
        if row["revisao_id"] == "r-baseline" and row["competencia"] == "2025-01"
    ]
    assert len(rows) == 1
    assert rows[0]["economia_bruta"] == 0.0


def test_process_list_daily_savings_from_liquida():
    raw = _load_fixture("golden_baseline_melhoria.json")
    calc = DashboardCalculatorService()

    items = calc.build_process_list(raw)
    assert len(items) == 1
    daily = items[0]["economia_diaria"]
    assert daily is not None
    assert daily > 0


def test_max_zero_when_melhoria_piora_tempo():
    raw = _load_fixture("golden_baseline_melhoria.json")
    raw.revisoes[1] = {**raw.revisoes[1], "data_inicio_vigencia": "2025-03-01"}
    raw.medicoes[1] = {
        **raw.medicoes[1],
        "tempo_medio_execucao_min": 120,
    }
    calc = DashboardCalculatorService()
    rows = [
        row
        for row in calc.build_dashboard_rows(raw)
        if row["revisao_id"] == "r-melhoria" and row["competencia"] == "2025-03"
    ]
    assert rows[0]["economia_tempo"] == 0.0
