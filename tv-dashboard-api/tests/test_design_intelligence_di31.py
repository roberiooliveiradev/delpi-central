"""DI-3.1 — COMPOSE_SLIDE broad intents reach the recipe composition
path instead of bare not_command/unsupported."""
from __future__ import annotations

import test_vista_execute as tx


def _suggest(message, host=None):
    d, _, _ = tx._dispatch()
    return d.suggest_change(
        user=tx._user(),
        message=message,
        host_context=host or {"playlistId": "p1", "slideId": "s1"},
        authorization=None,
    )


def test_recipe_marked_compose_produces_ops():
    out = _suggest("monte um painel com 4 kpis de produção")
    assert out["status"] == "ready"
    assert out["ops"], "recipe ops materializadas"


def test_broad_compose_without_marker_is_typed_gap_with_hints():
    out = _suggest("crie um painel generico xyzzy")
    assert out["status"] == "unsupported"
    assert out.get("compositionHints"), "hints de recipes ausentes"
    assert not out["ops"]


def test_broad_compose_stock_typed():
    out = _suggest(
        "quero uma TV mostrando xyzzy foobar"
    )
    assert out["status"] == "unsupported"
    assert out.get("compositionHints")


def test_broad_compose_executive_typed():
    out = _suggest(
        "crie uma apresentação sobre assuntos diversos"
    )
    assert out["status"] == "unsupported"
    assert out.get("compositionHints")


def test_kpi_specific_still_clarifies_route():
    out = _suggest("adicione um KPI de OEE ao slide")
    # seleção segura de fonte preservada — não escolhe sozinho
    assert out["status"] in {"clarification", "selection_pending", "ready"}
    assert out["status"] != "unsupported"


def test_no_playlist_keeps_legit_clarification():
    out = _suggest("crie um painel de vendas", host={})
    # sem contexto de playlist: clarificação legítima OU proposta
    # conceitual tipada (DI-3.6.2 — composição sem target explícito)
    assert out["status"] in {"clarification", "unsupported", "proposal"}
    if out["status"] == "clarification":
        assert out.get("clarificationKey")


def test_design_methodology_advisory_attached():
    out = _suggest("crie um painel de produtividade")
    # intent COMPOSE_SLIDE reconhecida → advisory presente
    assert out.get("designMethodology") is not None
