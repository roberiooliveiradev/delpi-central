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
from tests.entry_audit_corpus import COMPANY, OTHER, SUPPLIER, access_key

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

    def documents_by_access_keys(self, *, branch, access_keys):
        del branch, access_keys
        return []


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


def _nfe(number: int, key: str, *, issued: str = "2026-11-12T10:00:00-03:00", issuer: str = SUPPLIER, direction: str = "1") -> bytes:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><nfeProc xmlns="{NS}"><NFe><infNFe Id="NFe{key}" versao="4.00">'
        f"<ide><mod>55</mod><serie>1</serie><nNF>{number}</nNF><dhEmi>{issued}</dhEmi><tpNF>{direction}</tpNF></ide>"
        f"<emit><CNPJ>{issuer}</CNPJ><xNome>Fornecedor</xNome><enderEmit><UF>SC</UF></enderEmit><CRT>3</CRT></emit>"
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
    orphan_key = access_key("55", 400)

    class _WithOrphan(Protheus):
        def documents(self, *, branch, received_from, received_to, species):
            rows = super().documents(branch=branch, received_from=received_from, received_to=received_to, species=species)
            orphan = _header("400", orphan_key)
            orphan["supplier_name"] = "Fornecedor C"
            return [*rows, orphan]

    service = _service(protheus=_WithOrphan(), xml=xml, posting=posting)
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    service.claim_and_execute()
    unmatched = service.unmatched_documents(created["id"], {}, page=1, page_size=20)
    xml_only = [row for row in unmatched["items"] if row["side"] == "xml"]
    assert xml_only
    assert "Em lançamento (LNF)" in xml_only[0]["reason"]
    assert xml_only[0]["severity"] == "Info"
    assert xml_only[0]["party_name"] == "Fornecedor"
    assert xml_only[0]["series"] == "1"
    assert str(xml_only[0]["issue_date"]).startswith("2026-11-12")
    assert xml_only[0]["amount"] == 100
    assert xml_only[0]["cfop"] == "5101"
    booked = [row for row in unmatched["items"] if row["access_key"] == orphan_key]
    assert booked[0]["side"] == "protheus"
    assert booked[0]["party_name"] == "Fornecedor C"
    assert booked[0]["series"] == "1"
    assert booked[0]["amount"] == 100
    exported = service.export_rows(created["id"])
    with ZipFile(BytesIO(build_workbook(exported))) as archive:
        sheets = "".join(
            archive.read(name).decode()
            for name in archive.namelist()
            if name.startswith("xl/worksheets/")
        )
    assert "Fornecedor" in sheets
    assert "5101" in sheets
    assert "Fornecedor C" in sheets


def test_xml_posted_outside_the_period_is_not_unmatched():
    posted = access_key("55", 501)
    missing = access_key("55", 502)
    own_posted = access_key("55", 503)
    own_open = access_key("55", 504)
    issued = "2026-10-23T10:00:00-03:00"

    class _Lookup(Protheus):
        def documents(self, *, branch, received_from, received_to, species):
            del branch, received_from, received_to, species
            return []

        def documents_by_access_keys(self, *, branch, access_keys):
            del branch
            rows = []
            if posted in access_keys:
                row = _header("501", posted)
                row["received_date"] = "2026-11-02"
                row["issue_date"] = "2026-10-23"
                rows.append(row)
            if own_posted in access_keys:
                row = _header("503", own_posted)
                row["received_date"] = "2026-11-01"
                row["issue_date"] = "2026-10-23"
                row["own_form"] = "S"
                row["supplier_tax_id"] = COMPANY
                rows.append(row)
            return rows

    xml = Xml()
    xml.listed = [posted, missing, own_posted, own_open]
    xml.by_key[posted] = _nfe(501, posted, issued=issued)
    xml.by_key[missing] = _nfe(502, missing, issued=issued)
    xml.by_key[own_posted] = _nfe(503, own_posted, issued=issued, issuer=COMPANY, direction="0")
    xml.by_key[own_open] = _nfe(504, own_open, issued=issued, issuer=COMPANY, direction="0")
    service = _service(protheus=_Lookup(), xml=xml)
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    service.claim_and_execute()
    unmatched = service.unmatched_documents(created["id"], {}, page=1, page_size=20)["items"]
    keys = {row["access_key"] for row in unmatched}
    assert posted not in keys
    assert own_posted not in keys
    assert missing in keys
    own = next(row for row in unmatched if row["access_key"] == own_open)
    assert own["severity"] == "Alta"
    assert "formulário próprio" in own["reason"]
    summary = service.summary(created["id"], {})
    outside = summary["conformity"]["posted_outside_period"]
    assert outside["count"] == 2
    assert "2026-11-02" in outside["received_dates"]
    assert "2026-11-01" in outside["received_dates"]
    assert summary["kpis"]["documents"] == 0


def test_same_document_number_does_not_share_occurrences():
    key_a = access_key("55", 100, cnpj=SUPPLIER)
    key_b = access_key("55", 100, cnpj=OTHER)

    class _Books(Protheus):
        def documents(self, *, branch, received_from, received_to, species):
            note_a = _header("100", key_a)
            note_a["supplier_code"] = "000001"
            note_a["supplier_name"] = "Fornecedor A"
            note_a["supplier_tax_id"] = SUPPLIER
            note_b = _header("100", key_b)
            note_b["supplier_code"] = "000002"
            note_b["supplier_name"] = "Fornecedor B"
            note_b["supplier_tax_id"] = OTHER
            return [note_a, note_b]

        def items(self, **_kwargs):
            return [{
                "branch": "01", "document_number": "100", "series": "1",
                "supplier_code": "000001", "supplier_store": "01", "item": "0001",
                "product_code": "P", "cfop": "1101", "tax_situation": "000", "tes": "001",
                "total_amount": 100, "icms_base": 100, "icms_rate": 12, "icms_amount": 12,
                "ipi_base": 0, "ipi_rate": 0, "ipi_amount": 0, "st_amount": 0,
            }]

    xml = Xml()
    xml.by_key[key_a] = _nfe(100, key_a).replace(b"<vNF>100.00</vNF>", b"<vNF>80.00</vNF>")
    xml.by_key[key_b] = _nfe(100, key_b).replace(SUPPLIER.encode(), OTHER.encode()).replace(b"Fornecedor", b"Fornecedor B")
    service = _service(protheus=_Books(), xml=xml)
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    service.claim_and_execute()
    occurrences = service.occurrences(created["id"], {}, page=1, page_size=50, sort="severity")
    keys = [row["stable_key"] for row in occurrences["items"]]
    assert len(keys) == len(set(keys))
    assert all(row["access_key"] == key_a for row in occurrences["items"])
    summary = service.summary(created["id"], {})
    assert summary["kpis"]["occurrences"] == len(keys)
    assert summary["kpis"]["high"] == 1
    documents = service.documents(created["id"], {}, page=1, page_size=20)["items"]
    by_key = {row["access_key"]: row for row in documents}
    assert by_key[key_a]["situation"] == "divergent"
    assert by_key[key_a]["divergence_count"] == len(keys)
    assert by_key[key_b]["situation"] == "clean"
    assert by_key[key_b]["divergence_count"] == 0
    assert by_key[key_b]["supplier_name"] == "Fornecedor B"
    suppliers = {row["name"]: row["count"] for row in service.breakdowns(created["id"], {})["suppliers"]}
    assert suppliers["Fornecedor A"] == len(keys)
    assert "Fornecedor B" not in suppliers
    tes = {row["name"] for row in service.breakdowns(created["id"], {})["tes"]}
    assert tes == {"001"}


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


def test_a_short_lived_service_token_is_renewed_and_the_run_finishes():
    from delpi_auth.service_token_provider import ClientCredentialsTokenProvider, ServiceTokenProviderConfig

    clock = {"now": 1_000.0}
    issued = {"n": 0}

    def http_post(url, data=None, timeout=None):
        issued["n"] += 1
        return SimpleNamespace(
            status_code=200,
            json=lambda n=issued["n"]: {"access_token": f"service-{n}", "expires_in": 10},
        )

    provider = ClientCredentialsTokenProvider(
        ServiceTokenProviderConfig(
            token_url="https://issuer.example/token",
            client_id="controllership-finance-api",
            client_secret="secret",
            scopes=("stock-inventory.read",),
            timeout_seconds=5,
        ),
        http_post=http_post,
        clock=lambda: clock["now"],
        refresh_margin_seconds=0,
    )
    seen: list[str] = []

    class Reading(Protheus):
        def _touch(self):
            seen.append(provider.get_token())
            clock["now"] += 11

        def documents(self, **kwargs):
            self._touch()
            return super().documents(**kwargs)

        def items(self, **kwargs):
            self._touch()
            return super().items(**kwargs)

        def fiscal_book(self, **kwargs):
            self._touch()
            return super().fiscal_book(**kwargs)

        def tes(self):
            self._touch()
            return super().tes()

        def branches(self):
            self._touch()
            return super().branches()

    service = _service(Reading())
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    assert service.claim_and_execute() is True
    assert {run["status"] for run in service.get_analysis(created["id"])["runs"]} == {"done"}
    assert len(set(seen)) > 1


def test_orphan_recovery_after_restart_does_not_need_a_user_bearer():
    store = MemoryEntryAuditStore()
    first = EntryAuditService(store, Protheus(), Xml(), Posting(), AuditConfig(), lookback_days=30)
    created = first.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    assert first._store.claim_next_queued() is not None
    restarted = EntryAuditService(store, Protheus(), Xml(), Posting(), AuditConfig(), lookback_days=30)
    assert restarted.recover_orphans() == 1
    assert restarted.claim_and_execute() is True
    assert restarted.get_analysis(created["id"])["runs"][0]["status"] == "done"


def test_clara_request_records_the_requester_on_her_behalf():
    service = _service()
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="clara")
    stored = service._store.get_analysis(created["id"])
    assert stored["requested_by_name"] == "CLARA em nome de Ana"
    assert stored["requested_via"] == "clara"


def test_a_failed_xml_download_is_unavailable_and_not_an_unmatched_note():
    from controllership_finance_app.application.entry_audit.errors import XmlSourceUnavailable

    class Failing(Xml):
        def download_by_key(self, *, branch, access_key, document_type):
            raise XmlSourceUnavailable("document")

    service = _service(xml=Failing())
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    service.claim_and_execute()
    run = service.get_analysis(created["id"])["runs"][0]
    assert run["status"] == "partial"
    assert run["error"] == "XML_UNAVAILABLE"
    summary = service.summary(created["id"], {})
    assert summary["kpis"]["xml_unavailable"] == 1
    unmatched = service.unmatched_documents(created["id"], {}, page=1, page_size=20)
    assert access_key("55", 100) not in {row.get("access_key") for row in unmatched["items"]}


def test_a_failed_listing_fails_the_branch_instead_of_reporting_zero():
    from controllership_finance_app.application.entry_audit.errors import XmlSourceUnavailable

    class ListingDown(Xml):
        def list_issued(self, **_kwargs):
            raise XmlSourceUnavailable("listing")

    service = _service(xml=ListingDown())
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    service.claim_and_execute()
    run = service.get_analysis(created["id"])["runs"][0]
    assert run["status"] == "failed"
    assert run["error"] == "XML_LISTING_UNAVAILABLE"
    with pytest.raises(Exception) as caught:
        service.summary(created["id"], {})
    assert caught.value.code == "ANALYSIS_NOT_READY"


def test_xml_retry_recovers_and_a_persistent_failure_stays_unavailable():
    from controllership_finance_app.application.entry_audit.errors import XmlSourceUnavailable
    from controllership_finance_app.infrastructure.entry_audit.sources import FiscalXmlGateway
    from controllership_finance_app.infrastructure.invoice_posting.financial_received_invoice_gateway import (
        FinancialReceivedInvoiceGatewayError,
    )

    class Recovers:
        def __init__(self) -> None:
            self.calls = 0

        def download_xml_by_key_as_service(self, **_kwargs):
            self.calls += 1
            if self.calls < 3:
                raise FinancialReceivedInvoiceGatewayError("indisponível", 503)
            return b"<nfeProc></nfeProc>"

        def export_received_documents_as_service(self, **_kwargs):
            raise FinancialReceivedInvoiceGatewayError("listagem", 503)

    source = Recovers()
    gateway = FiscalXmlGateway(source, attempts=3, sleep=lambda _delay: None)
    assert gateway.download_by_key(branch="01", access_key="1" * 44, document_type="nfe") == b"<nfeProc></nfeProc>"
    assert source.calls == 3
    with pytest.raises(XmlSourceUnavailable) as caught:
        gateway.list_issued(branch="01", document_type="nfe", issued_from=WHEN, issued_to=WHEN)
    assert caught.value.scope == "listing"


def test_every_contract_route_covers_success_denial_and_missing_records():
    xml = Xml()
    extra = access_key("55", 300)
    xml.listed = [extra]
    xml.by_key[extra] = _nfe(300, extra)
    service = _service(xml=xml)
    created = service.create(date_from=WHEN, date_to=WHEN, document_types=["nfe"], branches=["01"], user_id="u", user_name="Ana", via="user")
    service.claim_and_execute()
    analysis_id = created["id"]
    stable_key = service.occurrences(analysis_id, {}, page=1, page_size=20, sort="severity")["items"][0]["stable_key"]
    unmatched_key = service.unmatched_documents(analysis_id, {}, page=1, page_size=20)["items"][0]["stable_key"]
    client = TestClient(_app(service))
    missing_id = "00000000-0000-0000-0000-000000000000"
    reads = [
        f"/entry-audit/analyses/options",
        "/entry-audit/analyses",
        f"/entry-audit/analyses/{analysis_id}",
        f"/entry-audit/analyses/{analysis_id}/summary",
        f"/entry-audit/analyses/{analysis_id}/daily",
        f"/entry-audit/analyses/{analysis_id}/breakdowns",
        f"/entry-audit/analyses/{analysis_id}/facets",
        "/entry-audit/trend",
        f"/entry-audit/analyses/{analysis_id}/occurrences",
        f"/entry-audit/analyses/{analysis_id}/occurrences/{stable_key}",
        f"/entry-audit/analyses/{analysis_id}/documents",
        f"/entry-audit/analyses/{analysis_id}/unmatched",
        f"/entry-audit/analyses/{analysis_id}/cte",
        f"/entry-audit/analyses/{analysis_id}/tes",
        f"/entry-audit/analyses/{analysis_id}/export",
    ]
    for path in reads:
        assert client.get(path).status_code == 200, path
        assert client.get(path, headers={"x-test-auth": "lnf"}).status_code == 403, path
    denied_posts = [
        ("/entry-audit/analyses", {"date_from": "2026-11-12", "date_to": "2026-11-12"}),
        (f"/entry-audit/analyses/{analysis_id}/rerun", {}),
        (f"/entry-audit/occurrences/{stable_key}/resolve", None),
        (f"/entry-audit/occurrences/{stable_key}/reopen", None),
        (f"/entry-audit/unmatched/{stable_key}/resolve", None),
        (f"/entry-audit/unmatched/{stable_key}/reopen", None),
    ]
    for path, body in denied_posts:
        response = client.post(path, json=body, headers={"x-test-auth": "lnf"})
        assert response.status_code == 403, path
    managed = client.post(
        "/entry-audit/analyses",
        json={"date_from": "2026-11-12", "date_to": "2026-11-12", "branches": ["02"]},
        headers={"x-test-auth": "manage"},
    )
    assert managed.status_code == 202
    invalid = client.post("/entry-audit/analyses", json={"date_from": "2026-11-13", "date_to": "2026-11-12"})
    assert invalid.status_code == 422
    assert client.get(f"/entry-audit/analyses/{missing_id}").status_code == 404
    assert client.get(f"/entry-audit/analyses/{missing_id}/summary").status_code == 404
    assert client.get(f"/entry-audit/analyses/{analysis_id}/occurrences/missing-key").status_code == 404
    assert client.post("/entry-audit/occurrences/missing-key/resolve").status_code == 404
    assert client.post("/entry-audit/unmatched/missing-key/reopen").status_code == 404
    resolved = client.post(f"/entry-audit/occurrences/{stable_key}/resolve")
    assert resolved.status_code == 200
    reopened = client.post(f"/entry-audit/occurrences/{stable_key}/reopen")
    assert reopened.status_code == 200
    unmatched_resolved = client.post(f"/entry-audit/unmatched/{unmatched_key}/resolve")
    assert unmatched_resolved.status_code == 200
    unmatched_reopened = client.post(f"/entry-audit/unmatched/{unmatched_key}/reopen")
    assert unmatched_reopened.status_code == 200
    rerun = client.post(f"/entry-audit/analyses/{analysis_id}/rerun", json={})
    assert rerun.status_code == 202
