"""CLARA — auditoria de entradas no catálogo existente. Sem tool nova."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from controllership_finance_app.application.clara.entry_audit_capabilities import (
    _exec_run,
)
from controllership_finance_app.application.clara.governed_writes import (
    ClaraGovernedWrites,
)
from controllership_finance_app.config import settings
from controllership_finance_app.interface.mcp import entry_audit_bridge as bridge
from controllership_finance_app.interface.mcp import semantic_bridge as sb

REPO = Path(__file__).resolve().parents[2]
FICHAS = REPO / "docs/12-roadmap-e-evolucao/controllership-finance/fichas/auditoria-entradas"
ENGINE = REPO / "controllership-finance-api/controllership_finance_app/domain/entry_audit/engine.py"
READS = (
    "options", "analysis", "summary", "daily", "breakdowns", "trend",
    "occurrences", "occurrence", "documents", "unmatched", "cte", "tes",
)
DIRECTS = (
    "entry_audit.run", "entry_audit.rerun",
    "entry_audit.resolve", "entry_audit.reopen",
)


def _actions(identity):
    catalog = sb._semantic_catalog(identity)
    read = {(row["entity"], row["action"]) for row in catalog["actions"]["read"]}
    analyze = {row["action"] for row in catalog["actions"]["analyze"]}
    governed = {row.get("capability") for row in catalog["actions"]["governed"]}
    return read, analyze, governed


def test_catalog_lists_entry_audit_only_with_access(monkeypatch):
    monkeypatch.setattr(settings, "ENTRY_AUDIT_ENABLED", True)
    read, analyze, governed = _actions({"has_cf_access": True})
    for action in READS:
        assert ("entry_audit", action) in read
    assert "entry_audit_findings" in analyze
    for capability in DIRECTS:
        assert capability in governed

    read, analyze, governed = _actions({"has_lnf_any": True, "lnf_read": True})
    assert not any(entity == "entry_audit" for entity, _action in read)
    assert "entry_audit_findings" not in analyze
    assert not any(cap in DIRECTS for cap in governed)

    read, analyze, _governed = _actions({})
    assert not any(entity == "entry_audit" for entity, _action in read)
    assert "entry_audit_findings" not in analyze


def test_catalog_hides_entry_audit_when_flag_is_off(monkeypatch):
    monkeypatch.setattr(settings, "ENTRY_AUDIT_ENABLED", False)
    read, analyze, governed = _actions({"has_cf_access": True, "is_manage": True})
    assert not any(entity == "entry_audit" for entity, _action in read)
    assert "entry_audit_findings" not in analyze
    assert not any(cap in DIRECTS for cap in governed)
    assert sb._schema_for("entry_audit", "summary") is None
    table = ClaraGovernedWrites()._capability_table()
    assert "entry_audit.run" not in table


def test_schema_is_callable_for_each_entry(monkeypatch):
    monkeypatch.setattr(settings, "ENTRY_AUDIT_ENABLED", True)
    for action in READS:
        schema = sb._schema_for("entry_audit", action)
        assert schema["tool"] == "read"
        assert schema["entity"] == "entry_audit"
    findings = sb._schema_for("entry_audit", "entry_audit_findings")
    assert findings["tool"] == "analyze"
    assert findings["analysis_type"] == "entry_audit_findings"
    for capability in DIRECTS:
        entity, action = capability.split(".", 1)
        schema = sb._schema_for(entity, action)
        assert schema["tool"] == "execute"
        assert schema["direct"] is True


def test_run_is_idempotent_on_the_same_filters(monkeypatch):
    calls = {"n": 0}

    class _Service:
        def create(self, **kwargs):
            calls["n"] += 1
            assert kwargs["via"] == "clara"
            return {"id": "analysis-1", "status": "queued", "created": calls["n"] == 1}

    monkeypatch.setattr(bridge, "build_entry_audit_service", lambda: _Service())
    from controllership_finance_app.application.clara import entry_audit_capabilities as caps
    monkeypatch.setattr(caps, "build_entry_audit_service", lambda: _Service())
    params = {"date_from": "2026-11-12", "date_to": "2026-11-12"}
    first = _exec_run(params, "sub-1", ())
    second = _exec_run(params, "sub-1", ())
    assert first["created"] is True
    assert second["created"] is False
    assert first["id"] == second["id"]


def test_direct_capabilities_are_registered_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "ENTRY_AUDIT_ENABLED", True)
    table = ClaraGovernedWrites()._capability_table()
    for capability in DIRECTS:
        assert table[capability]["direct"] is True
        assert table[capability]["gate"] == "access"


def test_mcp_flow_run_analysis_findings_occurrence_resolve(monkeypatch):
    state = {"status": "pending"}

    class _Service:
        def create(self, **_kwargs):
            return {"id": "analysis-1", "status": "queued", "created": True}

        def get_analysis(self, analysis_id):
            return {"id": analysis_id, "status": "done", "runs": [{"branch": "01", "status": "done"}]}

        def summary(self, analysis_id, filters):
            return {"kpis": {"documents": 2, "occurrences": 1, "high": 1, "pending": 1, "xml_unavailable": 0}, "conformity": {"clean": 1, "divergent": 1, "unmatched_open": 0, "unmatched_explained": 1}}

        def occurrences(self, analysis_id, filters, *, page, page_size, sort):
            return {"items": [{"rule_id": "item.origin_mismatch", "title": "Origem da mercadoria divergente", "severity": "Média", "tes": "101", "action": "Rever a origem na TES.", "document_number": "1"}], "page": page, "page_size": page_size, "total": 1}

        def occurrence(self, analysis_id, key):
            return {"rule_id": "item.origin_mismatch", "title": "Origem da mercadoria divergente", "status": state["status"]}

        def resolve(self, key, *, kind, user_id, user_name):
            state["status"] = "resolved"
            return {"stable_key": key, "kind": kind, "status": "resolved"}

    monkeypatch.setattr(settings, "ENTRY_AUDIT_ENABLED", True)
    monkeypatch.setattr(bridge, "build_entry_audit_service", lambda: _Service())
    from controllership_finance_app.application.clara import entry_audit_capabilities as caps
    monkeypatch.setattr(caps, "build_entry_audit_service", lambda: _Service())
    created = _exec_run({"date_from": "2026-11-12", "date_to": "2026-11-12"}, "sub-1", ())
    analysis = bridge.tool_entry_audit_analysis(analysis_id=created["id"])
    assert analysis.structured_content["data"]["status"] == "done"
    findings = bridge.tool_analyze_entry_audit_findings(ref=created["id"])
    payload = findings.structured_content["data"]
    kinds = {row["kind"] for row in payload["findings"]}
    assert {"FACT", "RECOMMENDATION"} <= kinds
    assert "access_key" not in str(payload)
    detail = bridge.tool_entry_audit_occurrence(created["id"], key="stable-1")
    assert detail.structured_content["data"]["status"] == "pending"
    from controllership_finance_app.application.clara.entry_audit_capabilities import (
        build_entry_audit_capability_table,
    )
    resolved = build_entry_audit_capability_table(require=lambda p, n: p[n])["entry_audit.resolve"]["execute"](
        {"key": "stable-1", "kind": "occurrence"}, "sub-1", (),
    )
    assert resolved["status"] == "resolved"


def test_fichas_cover_engine_rules_and_open_questions():
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(FICHAS.glob("AE-*.md")))
    rule_ids = set(re.findall(r'"(?:header|item|cte|key|simples|coherence|fiscal_book)\.[a-z0-9_]+"', ENGINE.read_text()))
    missing = {rule_id.strip('"') for rule_id in rule_ids if rule_id.strip('"') not in text}
    assert not missing, missing
    for marker in ("TO_INVENTORY (P2)", "TO_INVENTORY (P4)", "TO_INVENTORY (P5)", "TO_INVENTORY (P7)"):
        assert marker in text
    assert not (FICHAS / "AE-15.md").exists()
    from controllership_finance_app.application.clara.corpus_manifest import AUTHORIZED_SOURCES
    registered = {spec.source_id: spec for spec in AUTHORIZED_SOURCES}
    for number in range(15):
        source_id = f"ficha-ae-{number:02d}"
        spec = registered[source_id]
        assert spec.access_scope == "PORTAL_ACCESS"
        assert spec.domain_scope == "controllership"
        assert (REPO / spec.path).is_file()


def test_branding_mentions_the_audit_directives():
    from controllership_finance_app.interface.mcp.branding import CLARA_MCP_INSTRUCTIONS
    assert "entry_audit.run" in CLARA_MCP_INSTRUCTIONS
    assert "do not guess" in CLARA_MCP_INSTRUCTIONS
    assert "unavailable, not zero" in CLARA_MCP_INSTRUCTIONS
