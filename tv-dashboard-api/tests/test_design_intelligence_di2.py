"""DI-2 — semantic design reasoning regression (golden fixtures).

Proves DG-7 (intent narrow) and DG-8 (role detection) resolved:
temporal keys + ISO-date values, detail listing, composition-vs-bar,
and painel/TV/apresentação compose intent markers.
"""
from __future__ import annotations

from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService as D,
)


def _rec(rows, columns=None):
    return D.visual_recommendation(D.semantic_digest(rows, columns=columns))


# ---------------------------------------------------------------------------
# DG-8 — role detection
# ---------------------------------------------------------------------------


def test_temporal_pt_key_detected():
    r = _rec([{"dia": "01", "qty": 10}, {"dia": "02", "qty": 15}])
    assert r["recommendedType"] == "line"


def test_temporal_iso_value_detected():
    r = _rec([
        {"periodo": "2024-01", "qty": 10},
        {"periodo": "2024-02", "qty": 15},
    ])
    assert r["recommendedType"] == "line"


def test_goal_gauge_preserved():
    r = _rec([{"nome": "OEE", "real": 82, "meta": 90}])
    assert r["recommendedType"] == "gauge"


def test_state_listing_preserved():
    r = _rec([
        {"maquina": "M1", "status": "parada"},
        {"maquina": "M2", "status": "ok"},
    ])
    assert r["recommendedType"] == "table_view"


def test_two_category_prefers_bar():
    r = _rec([{"linha": "L1", "qty": 10}, {"linha": "L2", "qty": 15}])
    assert r["recommendedType"] == "bar"


def test_composition_many_categories_doughnut():
    rows = [
        {"faixa": f"F{i}", "qtd": i + 1} for i in range(4)
    ]
    r = _rec(rows)
    assert r["recommendedType"] in {"doughnut", "bar"}


def test_detail_listing_table():
    r = _rec([
        {"cod": "A", "desc": "item", "qtd": 5, "valor": 1.5, "extra": "x"}
    ])
    assert r["recommendedType"] == "table_view"


def test_no_metrics_stays_table():
    r = _rec([{"a": "x", "b": "y"}, {"a": "x2", "b": "y2"}])
    assert r["recommendedType"] == "table_view"


# ---------------------------------------------------------------------------
# DG-7 — design intent breadth
# ---------------------------------------------------------------------------


def test_intent_crie_painel():
    assert D.design_intent_for_message(
        "crie um painel para a equipe acompanhar as vendas"
    ) == "COMPOSE_SLIDE"


def test_intent_tv():
    assert D.design_intent_for_message(
        "quero uma TV mostrando os produtos que exigem atenção"
    ) == "COMPOSE_SLIDE"


def test_intent_monte_apresentacao():
    assert D.design_intent_for_message(
        "monte uma apresentação dos problemas de qualidade"
    ) == "COMPOSE_SLIDE"


def test_intent_typed_command_returns_none():
    assert D.design_intent_for_message(
        "delete slide 3"
    ) is None
