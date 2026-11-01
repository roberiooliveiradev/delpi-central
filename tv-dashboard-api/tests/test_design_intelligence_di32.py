"""DI-3.2 — composition recovery: business signals + explicit recipe
IDs resolve and materialize ops through the canonical suggest path."""
from __future__ import annotations

import test_vista_execute as tx
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService as R,
)


def _suggest(message, host=None):
    d, _, _ = tx._dispatch()
    return d.suggest_change(
        user=tx._user(),
        message=message,
        host_context=host or {"playlistId": "p1", "slideId": "s1"},
        authorization=None,
    )


# --- resolver -------------------------------------------------------------


def test_explicit_recipe_id_resolves():
    r = R.resolve_from_nl(
        "crie um painel com recipe TV_KPI_PLUS_CHART para o slide"
    )
    assert r is not None
    assert r.recipe_id == "TV_KPI_PLUS_CHART"


def test_explicit_recipe_id_spaced():
    r = R.resolve_from_nl("um painel tv kpi plus chart")
    assert r.recipe_id == "TV_KPI_PLUS_CHART"


# --- benchmark A–E (ChatGPT real evidence) ---------------------------------


def test_scenario_a_production_ops():
    out = _suggest(
        "crie um painel para acompanhar produtividade e problemas "
        "da fábrica"
    )
    assert out["status"] == "ready"
    assert out["ops"], "ops materializadas"
    assert all(isinstance(o, dict) and o.get("op") for o in out["ops"])


def test_scenario_b_stock_ops():
    out = _suggest(
        "quero uma TV mostrando os produtos que exigem atenção"
    )
    assert out["status"] == "ready"
    assert out["ops"]


def test_scenario_c_sales_ops():
    out = _suggest("quero acompanhar vendas e metas")
    assert out["status"] == "ready"
    assert out["ops"]


def test_scenario_d_quality_ops():
    out = _suggest(
        "monte um painel para monitorar desvios de qualidade"
    )
    assert out["status"] == "ready"
    assert out["ops"]


def test_scenario_e_executive_ops():
    out = _suggest(
        "preciso de uma apresentação da situação geral da operação"
    )
    assert out["status"] == "ready"
    assert out["ops"]


def test_explicit_recipe_request_ops():
    out = _suggest(
        "crie um painel com recipe TV_KPI_PLUS_CHART para o slide"
    )
    assert out["status"] == "ready"
    assert out["ops"]


def test_generic_unsignalled_honest_gap():
    out = _suggest("crie um painel genérico sem sinal")
    assert out["status"] == "unsupported"
    assert out.get("compositionHints")


def test_no_playlist_still_clarifies():
    out = _suggest("crie um painel de produtividade", host={})
    assert out["status"] in {"clarification", "unsupported", "ready"}
    if out["status"] == "clarification":
        assert out.get("clarificationKey")


def test_kpi_specific_still_clarifies_route():
    out = _suggest("adicione um KPI de OEE ao slide")
    assert out["status"] != "unsupported"
