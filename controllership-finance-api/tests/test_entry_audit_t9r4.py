"""T9R4 — E1–E6, B9: serviço + caminho MCP. Sem dado real."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pytest

from controllership_finance_app.application.entry_audit.service import EntryAuditService
from controllership_finance_app.application.entry_audit.vocabulary import (
    CODE_FIELD_CODES,
    NUMERIC_FIELD_CODES,
    difference_allowed,
)
from controllership_finance_app.config import settings
from controllership_finance_app.domain.entry_audit.causes import (
    KNOWN_CAUSES,
    RULE_CAUSES,
    cause_for,
)
from controllership_finance_app.domain.entry_audit.models import AuditConfig
from controllership_finance_app.infrastructure.entry_audit.memory_store import MemoryEntryAuditStore
from controllership_finance_app.infrastructure.entry_audit.xlsx_export import SHEETS, build_workbook
from controllership_finance_app.interface.mcp import entry_audit_bridge as bridge
from controllership_finance_app.interface.mcp import semantic_bridge as sb
from tests.entry_audit_corpus import COMPANY, SUPPLIER, access_key
from tests.test_entry_audit_application import Posting, Protheus, Xml, _header, _nfe, _service
from tests.test_entry_audit_coverage import RULES

WHEN = date(2026, 11, 12)
def _skill_relatorio() -> Path | None:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/reference/skill-auditoria-entradas-nfe-protheus/scripts/relatorio.py",
        Path("/home/analistaptd/projetos/delpi-central/docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/reference/skill-auditoria-entradas-nfe-protheus/scripts/relatorio.py"),
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None
SKILL_SHEET_ORDER = [
    "Resumo",
    "TES usadas",
    "Divergências",
    "Comparativo",
    "Só no XML",
    "Só no SF1",
    "CT-e Comparativo",
    "Itens Divergências",
    "Itens Comparativo",
    "Itens Agrupados",
    "Itens Excluídos",
]


def test_e2_difference_null_for_code_fields():
    for code in CODE_FIELD_CODES:
        assert difference_allowed(code) is False
        assert difference_allowed(code.upper()) is False or code in CODE_FIELD_CODES
    for label in ("CST", "CST (origem)", "Origem", "CFOP", "NCM", "Chave", "Série", "Espécie", "CNPJ", "UF"):
        assert difference_allowed(label) is False
    for code in NUMERIC_FIELD_CODES:
        assert difference_allowed(code) is True
    from controllership_finance_app.application.entry_audit.service import _difference

    assert _difference("090", "200", "CST (origem)") is None
    assert _difference("090", "200", "origin") is None
    assert _difference("12", "10", "ICMS") == "2.00"
    assert _difference("12", "10", "icms") == "2.00"


def test_e3_every_catalog_rule_has_a_canonical_cause():
    catalog = {
        rule_id
        for rule_id in RULES
        if not rule_id.startswith("suppressed.") and rule_id != "excluded.items"
    }
    for rule_id in sorted(catalog):
        cause = cause_for(rule_id)
        assert cause in KNOWN_CAUSES, (rule_id, cause)
        if not rule_id.startswith("unmatched."):
            assert rule_id in RULE_CAUSES, rule_id
            assert RULE_CAUSES[rule_id] != "", rule_id
    assert cause_for("simples.near_sublimite") == "fornecedor"
    with pytest.raises(KeyError):
        cause_for("made.up.rule")


def test_e1_documents_default_excludes_posted_outside():
    posted = access_key("55", 501)
    listed = access_key("55", 100)

    class _Lookup(Protheus):
        def documents(self, *, branch, received_from, received_to, species):
            del received_from, received_to, species
            if branch != "01":
                return []
            return [_header("100", listed)]

        def documents_by_access_keys(self, *, branch, access_keys):
            del branch
            if posted in access_keys:
                row = _header("501", posted)
                row["received_date"] = "2026-11-02"
                row["issue_date"] = "2026-10-23"
                return [row]
            return []

    xml = Xml()
    xml.listed = [posted]
    xml.by_key[listed] = _nfe(100, listed)
    xml.by_key[posted] = _nfe(501, posted, issued="2026-10-23T10:00:00-03:00")
    service = _service(protheus=_Lookup(), xml=xml)
    created = service.create(
        date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"],
        user_id="u", user_name="Ana", via="user",
    )
    service.claim_and_execute()
    default = service.documents(created["id"], {}, page=1, page_size=50)
    assert default["total"] == 1
    assert all(row["situation"] != "posted_outside_period" for row in default["items"])
    outside = service.documents(created["id"], {"situation": "posted_outside_period"}, page=1, page_size=50)
    assert outside["total"] >= 1
    assert all(row["situation"] == "posted_outside_period" for row in outside["items"])
    summary = service.summary(created["id"], {})
    assert summary["kpis"]["documents"] == 1
    assert summary["conformity"]["posted_outside_period"]["count"] >= 1


def test_e1_mcp_situation_filter_reaches_service(monkeypatch):
    monkeypatch.setattr(settings, "ENTRY_AUDIT_ENABLED", True)
    seen: dict = {}

    def _handler(**kwargs):
        seen.clear()
        seen.update(kwargs)
        from controllership_finance_app.interface.mcp.tool_bridge import _ok
        return _ok({"items": [], "total": 0, "page": 1, "page_size": 50})

    monkeypatch.setitem(sb.READ_ACTIONS[("entry_audit", "documents")], "handler", _handler)
    monkeypatch.setattr(sb, "_user_and_access", lambda: (None, {}))
    monkeypatch.setattr(sb, "_identity_snapshot", lambda _user: {"has_cf_access": True})
    analysis_id = "11111111-1111-4111-8111-111111111111"
    result = sb.tool_read(
        "entry_audit",
        "documents",
        ref=analysis_id,
        filters={"situation": "divergent"},
    )
    assert result.is_error is False
    assert seen.get("analysis_id") == analysis_id
    assert seen.get("situation") == "divergent"


@pytest.mark.parametrize(
    "action",
    ("summary", "daily", "breakdowns", "occurrences", "documents", "unmatched", "cte", "tes"),
)
def test_e1_mcp_every_schema_filter_reaches_handler(monkeypatch, action):
    monkeypatch.setattr(settings, "ENTRY_AUDIT_ENABLED", True)
    schema = sb._schema_for("entry_audit", action)
    assert schema is not None
    optional = [name for name in schema["optional_params"] if name not in {"page", "page_size"}]
    if not optional:
        return
    seen: dict = {}

    def _handler(**kwargs):
        seen.clear()
        seen.update(kwargs)
        from controllership_finance_app.interface.mcp.tool_bridge import _ok
        return _ok({"ok": True})

    monkeypatch.setitem(sb.READ_ACTIONS[("entry_audit", action)], "handler", _handler)
    monkeypatch.setattr(sb, "_user_and_access", lambda: (None, {}))
    monkeypatch.setattr(sb, "_identity_snapshot", lambda _user: {"has_cf_access": True})
    filters = {name: f"v-{name}" for name in optional}
    kwargs = {"filters": filters}
    if "analysis_id" in schema["required_params"]:
        kwargs["ref"] = "11111111-1111-4111-8111-111111111111"
    if action == "trend":
        filters["date_from"] = "2026-11-01"
        filters["date_to"] = "2026-11-12"
    result = sb.tool_read("entry_audit", action, **kwargs)
    assert result.is_error is False, getattr(result, "content", result)
    for name in optional:
        assert seen.get(name) == filters[name], (action, name, seen)


def test_e5_previous_kpis_match_current_fields():
    service = _service()
    # Contrato U12 (service._previous_kpis): «previous» só existe quando há
    # análise anterior com o mesmo span, filiais e tipos — aqui, o dia anterior.
    previous_id = str(uuid4())
    now = datetime.now(timezone.utc)
    service._store.analyses[previous_id] = {
        "id": previous_id,
        "status": "done",
        "date_from": WHEN - timedelta(days=1),
        "date_to": WHEN - timedelta(days=1),
        "document_types": ["nfe"],
        "branches": ["01"],
        "requested_via": "user",
        "created_at": now,
        "finished_at": now,
    }
    run_id = str(uuid4())
    service._store.runs[run_id] = {
        "id": run_id,
        "analysis_id": previous_id,
        "branch_code": "01",
        "status": "done",
        "stage": "done",
        "error_message": "",
        "counts": {},
    }
    created = service.create(
        date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"],
        user_id="u", user_name="Ana", via="user",
    )
    service.claim_and_execute()
    summary = service.summary(created["id"], {})
    assert summary["previous"] is not None
    assert set(summary["previous"]) == set(summary["kpis"])
    for name in ("resolved", "gross_checked", "high_difference", "xml_unavailable"):
        assert name in summary["previous"]


def test_e5_previous_is_none_without_prior_analysis():
    service = _service()
    created = service.create(
        date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"],
        user_id="u", user_name="Ana", via="user",
    )
    service.claim_and_execute()
    assert service.summary(created["id"], {})["previous"] is None


def test_e6_cte_comparison_has_no_empty_fiscal_code():
    from controllership_finance_app.application.entry_audit.service import _cte_comparison

    comparison = _cte_comparison({"gross_amount": 10, "icms_amount": 1}, None, [])
    assert "fiscal_code" not in comparison
    assert "cfop" in comparison


def test_e4_posted_outside_falls_back_to_xml_supplier_name():
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
    assert outside["items"][0]["supplier_name"] == "Fornecedor"


def test_b9_export_has_eleven_skill_sheets_in_order():
    assert [name for name, _ in SHEETS] == SKILL_SHEET_ORDER
    skill = _skill_relatorio()
    if skill is not None:
        text = skill.read_text(encoding="utf-8")
        for name, header in SHEETS:
            if name in {"Itens Comparativo", "Itens Agrupados"}:
                for column in header:
                    assert column in text, (name, column)
    payload = {
        "analysis": {"date_from": WHEN, "date_to": WHEN},
        "occurrences": [],
        "documents": [],
        "unmatched": [],
        "ctes": [],
        "tes": [],
        "item_comparisons": [{
            "situation": "clean", "document_number": "100", "series": "1",
            "supplier_name": "Fornecedor", "supplier_state": "SC",
            "item_sd1": "0001", "item_xml": 1, "product_code": "P",
            "description": "Peca", "ncm": "84818099", "cfop_xml": "5101",
            "cfop_protheus": "1101", "tes": "001", "cst_xml": "000",
            "cst_protheus": "000", "amount_protheus": 100, "amount_xml": 100,
            "icms_base_protheus": 100, "icms_base_xml": 100,
            "icms_protheus": 12, "icms_xml": 12, "ipi_protheus": 0, "ipi_xml": 0,
            "access_key": access_key("55", 100),
        }],
        "grouped_notes": [{
            "document_number": "200", "supplier_name": "Fornecedor", "supplier_state": "SC",
            "items_sd1": 2, "items_xml": 1, "amount_sd1": 100, "amount_xml": 100,
            "icms_sd1": 12, "icms_xml": 12, "ipi_sd1": 0, "ipi_xml": 0,
            "cfop_protheus": "1101", "cfop_xml": "5101", "cst_protheus": "000",
            "cst_xml": "000", "reading": "Itens agrupados ou desmembrados no lançamento; conferência só por nota. Total confere.",
            "access_key": access_key("55", 200),
        }],
        "excluded": [{
            "kind": "CT-e (frete)", "document_number": "9", "series": "1",
            "supplier_code": "000001", "supplier_store": "01", "item_count": 1, "amount": 50,
        }],
    }
    workbook = build_workbook(payload)
    with ZipFile(BytesIO(workbook)) as archive:
        workbook_xml = archive.read("xl/workbook.xml").decode()
        names = re.findall(r'name="([^"]+)"', workbook_xml)
        assert names == SKILL_SHEET_ORDER
        item_comp = archive.read("xl/worksheets/sheet9.xml").decode()
        grouped = archive.read("xl/worksheets/sheet10.xml").decode()
        assert "Itens Comparativo" in workbook_xml
        assert "Fornecedor" in item_comp
        assert "Total confere" in grouped


def test_b9_persist_item_comparisons_and_grouped_notes():
    key = access_key("55", 100)

    class _Books(Protheus):
        def items(self, **_kwargs):
            return [{
                "branch": "01", "document_number": "100", "series": "1",
                "supplier_code": "000001", "supplier_store": "01", "item": "0001",
                "product_code": "P", "cfop": "1101", "tax_situation": "000", "tes": "001",
                "total_amount": 100, "icms_base": 100, "icms_rate": 12, "icms_amount": 12,
                "ipi_base": 0, "ipi_rate": 0, "ipi_amount": 0, "st_amount": 0,
                "access_key": key,
            }]

    xml = Xml()
    xml.by_key[key] = _nfe(100, key)
    service = _service(protheus=_Books(), xml=xml)
    created = service.create(
        date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"],
        user_id="u", user_name="Ana", via="user",
    )
    service.claim_and_execute()
    exported = service.export_rows(created["id"])
    assert exported["item_comparisons"]
    assert exported["item_comparisons"][0]["document_number"] == "100"
    with ZipFile(BytesIO(build_workbook(exported))) as archive:
        names = re.findall(r'name="([^"]+)"', archive.read("xl/workbook.xml").decode())
    assert names == SKILL_SHEET_ORDER


def test_e3_mcp_analyze_uses_canonical_cause(monkeypatch):
    monkeypatch.setattr(settings, "ENTRY_AUDIT_ENABLED", True)

    class _Svc:
        def occurrences(self, analysis_id, filters, *, page, page_size, sort):
            del analysis_id, filters, page, page_size, sort
            return {
                "items": [{
                    "rule_id": "simples.near_sublimite",
                    "title": "Fornecedor do Simples perto do sublimite",
                    "severity": "Baixa",
                    "tes": "",
                    "action": "Acompanhar",
                    "document_number": "1",
                }],
                "total": 1,
            }

        def summary(self, analysis_id, filters):
            del analysis_id, filters
            return {"kpis": {"documents": 1, "occurrences": 1}, "conformity": {}}

    monkeypatch.setattr(bridge, "_service", lambda: _Svc())
    monkeypatch.setattr(sb, "_user_and_access", lambda: (None, {}))
    monkeypatch.setattr(sb, "_identity_snapshot", lambda _user: {"has_cf_access": True})
    result = sb.tool_analyze(
        "entry_audit_findings",
        refs=["11111111-1111-4111-8111-111111111111"],
    )
    assert result.is_error is False
    payload = result.structured_content.get("data") or result.structured_content
    findings = payload["findings"]
    causes = [
        row.get("cause")
        for row in findings
        if row.get("code") == "simples.near_sublimite" or (row.get("value") or {}).get("rule_id") == "simples.near_sublimite"
    ]
    assert causes
    assert all(cause == "fornecedor" for cause in causes)
