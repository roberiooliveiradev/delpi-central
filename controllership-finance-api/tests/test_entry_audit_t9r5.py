"""T9R5 — F1–F4: leitura + gravado. Sem dado real."""

from __future__ import annotations

from datetime import date

from controllership_finance_app.application.entry_audit.service import (
    EntryAuditService,
    _cte_comparison,
    _public_occurrence,
)
from controllership_finance_app.domain.entry_audit.models import AuditConfig
from controllership_finance_app.interface.mcp import entry_audit_bridge as bridge
from tests.entry_audit_corpus import access_key
from tests.test_entry_audit_application import Posting, Protheus, Xml, _header, _nfe, _service

WHEN = date(2026, 11, 12)


def test_f1_read_nulls_stored_difference_on_code_fields():
    key = f"01|{'1' * 44}|item.origin_mismatch|CST (origem)|1"
    row = {
        "stable_key": key,
        "rule_id": "item.origin_mismatch",
        "title": "Origem da mercadoria divergente",
        "severity": "Média",
        "theme": "item",
        "document_number": "100",
        "item": "1",
        "field": "origin",
        "protheus_value": "090",
        "xml_value": "200",
        "difference": "-110.00",
        "series": "1",
        "supplier_name": "Forn",
        "tes": "001",
        "why": "x",
        "action": "y",
        "access_key": "1" * 44,
    }
    public = _public_occurrence(row, {"status": "pending"})
    assert public["field"] == "origin"
    assert public["difference"] is None

    numeric = {**row, "stable_key": key.replace("CST (origem)", "icms"), "field": "icms", "difference": "1.50"}
    assert _public_occurrence(numeric, None)["difference"] == "1.50"


def test_f3_cte_read_strips_legacy_fiscal_code(monkeypatch):
    assert "fiscal_code" not in _cte_comparison({"gross_amount": 10}, None, [])

    class _Store:
        def get_analysis(self, _id):
            return {
                "id": _id, "date_from": WHEN, "date_to": WHEN, "document_types": ["cte"],
                "branches": ["01"], "status": "done", "requested_via": "user",
                "created_at": WHEN, "finished_at": WHEN, "config_snapshot": {},
            }

        def runs_of(self, _id):
            return [{"branch_code": "01", "status": "done"}]

        def rows(self, kind, _id):
            if kind != "ctes":
                return []
            return [{
                "branch": "01",
                "document_number": "9",
                "access_key": access_key("57", 9),
                "comparison": {"cfop": "5352", "fiscal_code": "", "gross": 10},
            }]

    service = EntryAuditService(
        store=_Store(),
        protheus=Protheus(),
        fiscal_xml=Xml(),
        posting=Posting(),
        config=AuditConfig(),
    )
    page = service.ctes("a1", {}, page=1, page_size=20)
    assert page["total"] == 1
    assert "fiscal_code" not in page["items"][0]["comparison"]
    assert page["items"][0]["comparison"]["cfop"] == "5352"


def test_f2_posted_outside_uses_xml_party_when_sa2_name_empty():
    posted = access_key("55", 777)

    class _Lookup(Protheus):
        def documents(self, *, branch, received_from, received_to, species):
            del branch, received_from, received_to, species
            return []

        def documents_by_access_keys(self, *, branch, access_keys):
            del branch
            if posted in access_keys:
                row = _header("777", posted)
                row["supplier_name"] = ""
                row["supplier_code"] = "000001"
                row["supplier_store"] = "13"
                row["received_date"] = "2026-11-02"
                row["issue_date"] = "2026-10-23"
                return [row]
            return []

    xml = Xml()
    xml.listed = [posted]
    xml.by_key[posted] = _nfe(777, posted, issued="2026-10-23T10:00:00-03:00")
    service = _service(protheus=_Lookup(), xml=xml)
    created = service.create(
        date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"],
        user_id="u", user_name="Ana", via="user",
    )
    service.claim_and_execute()
    outside = service.documents(created["id"], {"situation": "posted_outside_period"}, page=1, page_size=20)
    assert outside["total"] == 1
    assert outside["items"][0]["supplier_code"] == "000001"
    assert outside["items"][0]["supplier_store"] == "13"
    assert outside["items"][0]["supplier_name"] == "Fornecedor"


def test_f4_analyze_coverage_keeps_documents_under_theme_filter(monkeypatch):
    from controllership_finance_app.config import settings

    class _Service:
        def occurrences(self, analysis_id, filters, *, page, page_size, sort):
            del analysis_id, sort
            assert filters.get("theme") == "simples"
            items = [{
                "rule_id": "simples.near_sublimite",
                "title": "Simples próximo do sublimite",
                "severity": "Info",
                "tes": "",
                "action": "Acompanhar.",
                "document_number": "1",
            }]
            return {"items": items if page == 1 else [], "page": page, "page_size": page_size, "total": 1}

        def summary(self, analysis_id, filters):
            del analysis_id
            # Com o _filtered por kind, theme não zera documentos.
            occs = 1 if filters.get("theme") == "simples" else 5
            return {
                "kpis": {"documents": 19, "occurrences": occs, "xml_unavailable": 0},
                "conformity": {"unmatched_explained": 2},
            }

    monkeypatch.setattr(settings, "ENTRY_AUDIT_ENABLED", True)
    monkeypatch.setattr(bridge, "build_entry_audit_service", lambda: _Service())
    monkeypatch.setattr(bridge, "_service", lambda: _Service())
    result = bridge.tool_analyze_entry_audit_findings(ref="a1", theme="simples")
    assert result.is_error is False
    coverage = next(row for row in result.structured_content["data"]["findings"] if row["code"] == "entry_audit.coverage")
    assert "0 notas" not in coverage["message"]
    assert "19 notas" in coverage["message"]
    assert "filtro: theme=simples" in coverage["message"]
    assert coverage["value"]["filters"]["theme"] == "simples"


def test_f4_summary_theme_does_not_zero_documents():
    service = _service()
    created = service.create(
        date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"],
        user_id="u", user_name="Ana", via="user",
    )
    service.claim_and_execute()
    full = service.summary(created["id"], {})
    themed = service.summary(created["id"], {"theme": "simples"})
    assert full["kpis"]["documents"] >= 1
    assert themed["kpis"]["documents"] == full["kpis"]["documents"]
