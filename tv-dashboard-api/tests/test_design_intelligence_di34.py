"""DI-3.4 — source qualification per component + honest readiness."""
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


def test_per_block_binding_plan():
    out = _suggest(
        "crie um painel para acompanhar produtividade e problemas "
        "da fábrica"
    )
    bp = out["bindingPlan"]
    assert bp["blocks"], "plano por bloco ausente"
    types = {b["blockType"] for b in bp["blocks"]}
    assert {"kpi_view", "chart_view", "table_view"} <= types
    for b in bp["blocks"]:
        assert b["state"] in {
            "RESOLVED", "NEEDS_SOURCE_SELECTION", "NEEDS_CONTEXT",
        }
        assert b["requiredModes"]


def test_document_export_disqualified():
    out = _suggest("quero acompanhar vendas e metas")
    bp = out["bindingPlan"]
    for b in bp["blocks"]:
        for c in b["candidates"]:
            assert c.get("metaShape") != "document_export"


def test_modes_qualify_candidates():
    out = _suggest("crie um painel de produtividade")
    bp = out["bindingPlan"]
    for b in bp["blocks"]:
        allowed = set(b["requiredModes"])
        for c in b["candidates"]:
            declared = set(c.get("allowedDisplayModes") or [])
            # modo específico OU auto + shape compatível (DI-3.5)
            assert (allowed & (declared - {"auto"})) or (
                "auto" in declared
                and c.get("metaShape") is not None
            )


def test_pending_binding_honest_readiness():
    out = _suggest("crie um painel de produtividade da fábrica")
    assert out["status"] == "ready"
    if out["bindingPlan"]["state"] != "RESOLVED":
        assert out.get("dataReadiness") == "pending_source_selection"
        reason = out.get("reason") or ""
        assert "execução direta" not in reason


def test_sales_block_modes():
    out = _suggest("quero acompanhar vendas e metas")
    bp = out["bindingPlan"]
    assert bp["dataBlockOps"] >= 2
    assert any(
        b["blockType"] == "kpi_view" for b in bp["blocks"]
    )
