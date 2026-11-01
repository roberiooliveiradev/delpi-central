"""DI-3.6.3 — unified eligibility (downloads out), Kaizen coverage,
multi-intent preservation."""
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


def _ids(b):
    return {c["operationId"] for c in b["candidates"]}


def test_downloads_not_kpi_candidates():
    out = _suggest("crie um painel de auditorias 5S e não conformidades")
    for b in out["bindingPlan"]["blocks"]:
        assert not any(
            oid.startswith(("download_", "export_"))
            for oid in _ids(b)
        )


def test_kaizen_explicit_composes():
    out = _suggest(
        "crie um painel de resultados das iniciativas Kaizen"
    )
    assert out["status"] in {"proposal", "ready"}
    ids = {
        oid for b in out["bindingPlan"]["blocks"] for oid in _ids(b)
    }
    assert any("kaizen" in oid for oid in ids)


def test_multi_intent_both_domains():
    out = _suggest(
        "crie um painel de produtividade e auditorias 5S da fábrica"
    )
    ids = {
        oid for b in out["bindingPlan"]["blocks"] for oid in _ids(b)
    }
    assert any(
        "production" in oid or "oee" in oid or "eficiencia" in oid
        for oid in ids
    ), "produtividade não pode perder cobertura"
    assert any(
        "audit" in oid or "5s" in oid or "nonconform" in oid
        for oid in ids
    ), "auditorias 5S não pode perder cobertura"


def test_gibberish_still_unsupported():
    out = _suggest("quero uma TV mostrando xyzzy foobar")
    assert out["status"] == "unsupported"


def test_5s_audit_sources_present():
    out = _suggest("crie um painel de auditorias 5S e não conformidades")
    ids = {
        oid for b in out["bindingPlan"]["blocks"] for oid in _ids(b)
    }
    assert any("audit_5s" in oid or "nonconform" in oid for oid in ids)


def test_production_clean():
    out = _suggest(
        "crie um painel para acompanhar produtividade e problemas "
        "da fábrica"
    )
    chart = next(
        b for b in out["bindingPlan"]["blocks"]
        if b["blockType"] == "chart_view"
    )
    ids = _ids(chart)
    assert "get_audit_5s_summary_series" not in ids
    assert "get_kaizen_summary_series" not in ids
