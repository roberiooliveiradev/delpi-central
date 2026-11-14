"""T5 — análise, worker, D11, rotas e exportação. Sem dado real."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from controllership_finance_app.application.entry_audit.service import EntryAuditService
from controllership_finance_app.domain.entry_audit.models import AuditConfig
from controllership_finance_app.infrastructure.entry_audit.memory_store import MemoryEntryAuditStore
from controllership_finance_app.infrastructure.entry_audit.xlsx_export import SHEETS, build_workbook
from controllership_finance_app.interface.http.routes.entry_audit.router import router
from tests.entry_audit_corpus import COMPANY, SUPPLIER, access_key

WHEN = date(2026, 11, 12)
NS = "http://www.portalfiscal.inf.br/nfe"


class Protheus:
    def __init__(self) -> None:
        self.fail_branch = ""

    def documents(self, *, branch, received_from, received_to, species):
        if branch == self.fail_branch:
            raise RuntimeError("branch down")
        if branch != "01":
            return []
        return [_header("100", access_key("55", 100)), _header("200", "")]

    def items(self, **_kwargs):
        return []

    def fiscal_book(self, **_kwargs):
        return []

    def tes(self):
        return [{
            "code": "001", "description": "Compra", "calculates_icms": "S", "credits_icms": "S",
            "icms_book": "T", "calculates_ipi": "N", "credits_ipi": "N", "ipi_book": "O",
            "consumption_material": "N", "tes_type": "Entrada", "fiscal_code": "1101",
        }]

    def branches(self):
        return [
            {"code": "01", "name": "Matriz", "state": "SC", "tax_id": COMPANY},
            {"code": "02", "name": "Filial", "state": "ES", "tax_id": COMPANY},
        ]


class Xml:
    def __init__(self) -> None:
        self.listed: list[str] = []
        self.by_key: dict[str, bytes] = {}

    def download_by_key(self, *, branch, access_key, document_type):
        return self.by_key.get(access_key)

    def list_issued(self, *, branch, document_type, issued_from, issued_to):
        return list(self.listed)


class Posting:
    def __init__(self) -> None:
        self.open: dict[str, dict] = {}

    def find_open(self, *, branch, access_key, document_number, series, supplier_code):
        return self.open.get(access_key)


def _header(number: str, key: str) -> dict:
    return {
        "branch": "01", "document_number": number, "series": "1", "supplier_code": "000001",
        "supplier_store": "01", "supplier_name": "Fornecedor", "supplier_state": "SC",
        "supplier_tax_id": SUPPLIER, "species": "SPED", "own_form": "N", "invoice_type": "N",
        "access_key": key, "issue_date": "2026-11-12", "received_date": "2026-11-12",
        "freight_amount": 0, "expense_amount": 0, "icms_base": 100, "icms_amount": 12,
        "ipi_base": 0, "ipi_amount": 0, "goods_amount": 100, "gross_amount": 100,
        "discount_amount": 0, "st_base": 0, "st_amount": 0, "insurance_amount": 0,
    }


def _nfe(number: int, key: str) -> bytes:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><nfeProc xmlns="{NS}"><NFe><infNFe Id="NFe{key}" versao="4.00">'
        f"<ide><mod>55</mod><serie>1</serie><nNF>{number}</nNF><dhEmi>2026-11-12T10:00:00-03:00</dhEmi><tpNF>1</tpNF></ide>"
        f"<emit><CNPJ>{SUPPLIER}</CNPJ><xNome>Fornecedor</xNome><enderEmit><UF>SC</UF></enderEmit><CRT>3</CRT></emit>"
        f"<dest><CNPJ>{COMPANY}</CNPJ></dest>"
        f'<det nItem="1"><prod><cProd>P</cProd><xProd>Peca</xProd><NCM>84818099</NCM><CFOP>5101</CFOP><vProd>100.00</vProd></prod>'
        f"<imposto><ICMS><ICMS00><orig>0</orig><CST>00</CST><vBC>100.00</vBC><pICMS>12.00</pICMS><vICMS>12.00</vICMS></ICMS00></ICMS></imposto></det>"
        f"<total><ICMSTot><vBC>100.00</vBC><vICMS>12.00</vICMS><vST>0</vST><vProd>100.00</vProd><vFrete>0</vFrete><vSeg>0</vSeg><vDesc>0</vDesc><vII>0</vII><vIPI>0</vIPI><vOutro>0</vOutro><vNF>100.00</vNF></ICMSTot></total>"
        f"</infNFe></NFe><protNFe><infProt><cStat>100</cStat></infProt></protNFe></nfeProc>"
    ).encode()


def _service(protheus=None, xml=None, posting=None):
    return EntryAuditService(
        MemoryEntryAuditStore(),
        protheus or Protheus(),
        xml or Xml(),
        posting or Posting(),
        AuditConfig(),
        lookback_days=30,
    )


def test_create_is_idempotent_while_open_and_rejects_a_bad_window():
    service = _service()
    first = service.create(date_from=WHEN, date_to=WHEN, document_types=["cte", "nfe"], branches=["02", "01"], user_id="u", user_name="Ana", via="user")
    second = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe", "cte"], branches=["01", "02"], user_id="u", user_name="Ana", via="user")
    assert first["created"] is True
    assert second == {"id": first["id"], "status": "queued", "created": False}
    with pytest.raises(Exception) as caught:
        service.create(date_from=date(2026, 11, 13), date_to=WHEN, document_types=None, branches=None, user_id="u", user_name="Ana", via="user")
    assert caught.value.status_code == 422


def test_worker_runs_each_branch_and_a_failure_does_not_zero_the_other():
    protheus = Protheus()
    protheus.fail_branch = "02"
    xml = Xml()
    key = access_key("55", 100)
    xml.by_key[key] = _nfe(100, key)
    service = _service(protheus, xml)
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01", "02"], user_id="u", user_name="Ana", via="user")
    assert service.claim_and_execute() is True
    assert service.claim_and_execute() is True
    assert service.claim_and_execute() is False
    detail = service.get_analysis(created["id"])
    by_branch = {run["branch"]: run["status"] for run in detail["runs"]}
    assert by_branch == {"01": "done", "02": "failed"}
    summary = service.summary(created["id"], {})
    assert summary["branches_unavailable"] == ["02"]
    assert summary["kpis"]["documents"] == 2


def test_rerun_keeps_the_resolved_status_and_refuses_a_queued_branch():
    service = _service()
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    with pytest.raises(Exception) as caught:
        service.rerun(created["id"], ["01"])
    assert caught.value.code == "RUN_IN_PROGRESS"
    service.claim_and_execute()
    rows = service.occurrences(created["id"], {}, page=1, page_size=20, sort="severity")
    assert rows["items"]
    stable_key = rows["items"][0]["stable_key"]
    service.resolve(stable_key, kind="occurrence", user_id="u", user_name="Ana")
    service.rerun(created["id"], ["01"])
    service.claim_and_execute()
    again = service.occurrence(created["id"], stable_key)
    assert again["status"] == "resolved"


def test_orphan_running_returns_to_the_queue():
    service = _service()
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    run = service._store.claim_next_queued()
    assert service.recover_orphans() == 1
    assert service._store.get_run(run["id"])["status"] == "queued"
    assert service.get_analysis(created["id"])["status"] == "queued"


def test_xml_by_key_matches_and_lnf_explains_an_unmatched_xml():
    listed_key = access_key("55", 300)
    booked_key = access_key("55", 100)
    xml = Xml()
    xml.by_key[booked_key] = _nfe(100, booked_key)
    xml.by_key[listed_key] = _nfe(300, listed_key)
    xml.listed = [listed_key]
    posting = Posting()
    posting.open[listed_key] = {"request_id": "req-1", "status": "pending"}
    service = _service(xml=xml, posting=posting)
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    service.claim_and_execute()
    unmatched = service.unmatched_documents(created["id"], {}, page=1, page_size=20)
    xml_only = [row for row in unmatched["items"] if row["side"] == "xml"]
    assert xml_only
    assert "Em lançamento (LNF)" in xml_only[0]["reason"]
    assert xml_only[0]["severity"] == "Info"


def test_export_uses_the_skill_sheets_and_the_tes_columns():
    payload = {
        "analysis": {"date_from": WHEN, "date_to": WHEN},
        "occurrences": [],
        "documents": [],
        "unmatched": [],
        "ctes": [],
        "tes": [{
            "tes_code": "001",
            "sf4": {
                "description": "Compra", "tes_type": "Entrada", "fiscal_code": "1101", "items": 1,
                "calculates_icms": "Sim", "credits_icms": "Sim", "icms_book": "Tributado",
                "consumption_material": "Nao", "calculates_ipi": "Nao", "credits_ipi": "Nao", "ipi_book": "Outros",
            },
        }],
    }
    workbook = build_workbook(payload)
    with ZipFile(BytesIO(workbook)) as archive:
        workbook_xml = archive.read("xl/workbook.xml").decode()
        tes_sheet = archive.read("xl/worksheets/sheet2.xml").decode()
    for name, _header in SHEETS:
        assert name in workbook_xml
    assert "Tipo do TES" in tes_sheet
    assert "Cod. Fiscal" in tes_sheet
    assert "Entrada" in tes_sheet


def _app(service):
    application = FastAPI()
    application.state.entry_audit_service = service

    @application.middleware("http")
    async def _user(request, call_next):
        kind = request.headers.get("x-test-auth", "access")
        if kind == "anonymous":
            request.state.user = None
        else:
            permissions = {
                "access": ["controllership-finance.access"],
                "manage": ["controllership-finance.manage"],
                "lnf": ["lancamento-notas-fiscais.access"],
            }[kind]
            request.state.user = SimpleNamespace(
                principal_type="user", permissions=permissions, is_superadmin=False,
                rbac_unavailable=False, id="u", name="Ana",
            )
        return await call_next(request)

    application.include_router(router)
    return application


def test_routes_require_controllership_access_and_manage_inherits():
    client = TestClient(_app(_service()))
    denied = client.post(
        "/entry-audit/analyses",
        json={"date_from": "2026-11-12", "date_to": "2026-11-12"},
        headers={"x-test-auth": "lnf"},
    )
    assert denied.status_code == 403
    missing = client.post(
        "/entry-audit/analyses",
        json={"date_from": "2026-11-12", "date_to": "2026-11-12"},
        headers={"x-test-auth": "anonymous"},
    )
    assert missing.status_code == 401
    created = client.post(
        "/entry-audit/analyses",
        json={"date_from": "2026-11-12", "date_to": "2026-11-12"},
        headers={"x-test-auth": "manage"},
    )
    assert created.status_code == 202
    assert created.json()["data"]["created"] is True


def test_flag_off_does_not_mount_the_routes():
    from controllership_finance_app.config import settings
    from controllership_finance_app.main import app

    paths = [getattr(route, "path", "") for route in app.routes]
    mounted = any(str(path).startswith("/entry-audit") for path in paths)
    assert mounted is settings.ENTRY_AUDIT_ENABLED
