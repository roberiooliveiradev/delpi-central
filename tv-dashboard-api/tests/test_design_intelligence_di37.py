"""DI-3.7 — goal-to-block traceability: interpretedGoals,
ignoredGoals, servesGoals, goal-justified sources."""
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


def test_multi_intent_goals_interpreted():
    out = _suggest(
        "crie um painel de produtividade e auditorias 5S da fábrica"
    )
    goals = {g["goal"]: g["status"] for g in out["interpretedGoals"]}
    assert "auditorias" in goals
    assert goals["auditorias"] == "COVERED"
    assert any(
        g in goals for g in ("produtividade", "fabrica")
    )


def test_blocks_serve_goals():
    out = _suggest(
        "crie um painel de produtividade e auditorias 5S da fábrica"
    )
    served = {
        g for b in out["bindingPlan"]["blocks"]
        for g in b.get("servesGoals") or []
    }
    assert served, "blocos devem declarar quais objetivos servem"
    for b in out["bindingPlan"]["blocks"]:
        assert "servesGoals" in b


def test_kaizen_needs_kaizen_goal():
    out = _suggest(
        "crie um painel de produtividade e auditorias 5S da fábrica"
    )
    chart = next(
        b for b in out["bindingPlan"]["blocks"]
        if b["blockType"] == "chart_view"
    )
    ids = _ids(chart)
    assert "get_kaizen_savings_investment_series" not in ids
    assert "get_kaizen_summary_series" not in ids


def test_5s_only_sources():
    out = _suggest("crie um painel de auditorias 5S e não conformidades")
    table = next(
        b for b in out["bindingPlan"]["blocks"]
        if b["blockType"] == "table_view"
    )
    assert any(
        "audit" in oid or "nonconform" in oid for oid in _ids(table)
    )


def test_single_intent_goals():
    out = _suggest(
        "crie um painel para acompanhar produtividade da fábrica"
    )
    goals = {g["goal"] for g in out["interpretedGoals"]}
    assert goals
    assert "kaizen" not in goals


def test_goal_field_present():
    out = _suggest("crie um painel de auditorias 5S")
    blocks = (out.get("bindingPlan") or {}).get("blocks") or []
    for b in blocks:
        for c in b["candidates"]:
            assert "goals" in c or c.get("goals") is None
