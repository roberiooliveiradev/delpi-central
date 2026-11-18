"""T18/FA-4/FA-5/FA-7 — uma ocorrência por causa, fila consolidada e KPIs."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from uuid import uuid4

from controllership_finance_app.application.entry_audit.service import (
    EntryAuditService,
    _cause_groups,
)
from controllership_finance_app.application.entry_audit.vocabulary import (
    stable_key_v2_from_v1,
)
from controllership_finance_app.domain.entry_audit.causes import cause_id_for
from controllership_finance_app.domain.entry_audit.engine import _consolidate, audit
from controllership_finance_app.domain.entry_audit.models import (
    AuditConfig,
    ProtheusHeader,
    ProtheusItem,
    TesRecord,
    XmlDocument,
    XmlItem,
)
from controllership_finance_app.infrastructure.entry_audit.memory_store import (
    MemoryEntryAuditStore,
)

SUPPLIER = "22222222000191"
COMPANY = "11111111000191"
WHEN = datetime(2026, 11, 12, 10, 0, 0)
DAY = date(2026, 11, 12)
KEY = "42261122222222000191550010000099991000000012"


def _key(model: str, number: int, cnpj: str = SUPPLIER) -> str:
    body = f"422611{cnpj}{model}001{number:09d}100000001"
    total, weight = 0, 2
    for digit in reversed(body):
        total += int(digit) * weight
        weight = 2 if weight == 9 else weight + 1
    check = 11 - total % 11
    return body + str(0 if check >= 10 else check)


def _header(number: int, access_key: str, gross: float, goods: float, icms: float, base: float) -> ProtheusHeader:
    return ProtheusHeader(
        branch="01", number=str(number), series="1", supplier_code="000001", supplier_store="01",
        supplier_name="Fornecedor Sintetico", supplier_state="SC", supplier_tax_id=SUPPLIER,
        species="SPED", own_form="N", access_key=access_key, issue_date=DAY, received_date=DAY,
        freight_amount=0, expense_amount=0, icms_base=base, icms_amount=icms, ipi_base=0, ipi_amount=0,
        goods_amount=goods, gross_amount=gross, discount_amount=0, st_base=0, st_amount=0, insurance_amount=0,
    )


def _item(number: int, item: str, total: float, icms: float, *, tes: str = "001", cst: str = "000") -> ProtheusItem:
    return ProtheusItem(
        branch="01", number=str(number), series="1", supplier_code="000001", supplier_store="01",
        item=item, product_code=f"P{item}", cfop="1101", tax_situation=cst, tes=tes, total_amount=total,
        icms_base=total if icms else 0, icms_rate=12 if icms else 0, icms_amount=icms,
        ipi_base=0, ipi_rate=0, ipi_amount=0, st_amount=0,
    )


def _xml_item(number: int, amount: float, icms: float, *, origin: str = "0") -> XmlItem:
    return XmlItem(
        number=number, product_code=f"P{number}", description=f"Peca {number}", ncm="84818099", cfop="5101",
        amount=amount, origin=origin, cst="00", csosn="", icms_base=amount, icms_rate=12, icms_amount=icms,
        ipi_amount=0, ipi_base=0, ipi_rate=0, st_amount=0,
    )


def _invoice(number: int, access_key: str, items: tuple[XmlItem, ...], total: float, icms: float, base: float) -> XmlDocument:
    return XmlDocument(
        access_key=access_key, model="55", number=number, series="1", issued_at=WHEN,
        issuer_tax_id=SUPPLIER, issuer_name="Fornecedor Sintetico", issuer_state="SC",
        recipient_tax_id=COMPANY, direction="Saída", crt="3", goods_amount=total, freight_amount=0,
        discount_amount=0, other_amount=0, icms_base=base, icms_amount=icms, st_amount=0, ipi_amount=0,
        total_amount=total, status_code="100", items=items,
    )


TES = [
    TesRecord("001", "Compra com credito", "Sim", "Sim", "Tributado", "Nao", "Nao", "Outros", "Nao", "Entrada", "101"),
]


def _run(headers, items, invoices, grouping: bool):
    return audit(
        branch="01", company_tax_id=COMPANY, company_state="SC", headers=headers, items=items,
        tes_records=TES, invoices=invoices, ctes={},
        config=AuditConfig(improvements_enabled=False, cause_grouping_enabled=grouping),
    )


def _hit(rule_id: str, severity: str, *, item: str = "", follower: bool = False, cause: str | None = None) -> dict:
    return {
        "rule_id": rule_id, "title": rule_id, "severity": severity, "number": "1", "item": item,
        "field": "ICMS", "protheus_value": "10", "xml_value": "8",
        "access_key": KEY, "supplier": "Fornecedor", "action": "acao",
        "cause_id": cause or cause_id_for(rule_id), "follower": follower,
    }


def _settings(grouping: bool = True) -> AuditConfig:
    return AuditConfig(cause_grouping_enabled=grouping)


def test_nf_b_header_item_icms_and_accompanying_base_become_one_cause() -> None:
    """NF-B: ICMS cabeçalho + ICMS item + base «Acompanha…» = 1 ocorrência."""
    key = _key("55", 9999)
    header = _header(9999, key, 100, 100, 20, 110)
    result = _run(
        [header], [_item(9999, "1", 100, 20)],
        {key: _invoice(9999, key, (_xml_item(1, 100, 12),), 100, 12, 100)},
        grouping=True,
    )
    assert len(result.occurrences) == 1
    cause = result.occurrences[0]
    assert cause.cause_id == "icms_amount"
    assert cause.severity == "Alta"
    assert len(cause.items) == 2  # cabeçalho + item
    assert {entry.item for entry in cause.items} == {"", "1"}
    assert len(cause.followers) == 1
    assert cause.followers[0].rule_id == "header.icms_base_mismatch"


def test_flag_off_keeps_v1_rows_unchanged() -> None:
    """Flag desligada: as três linhas v1 continuam separadas (compatibilidade)."""
    key = _key("55", 9999)
    header = _header(9999, key, 100, 100, 20, 110)
    result = _run(
        [header], [_item(9999, "1", 100, 20)],
        {key: _invoice(9999, key, (_xml_item(1, 100, 12),), 100, 12, 100)},
        grouping=False,
    )
    assert {row.rule_id for row in result.occurrences} == {
        "header.icms_above_xml", "header.icms_base_mismatch", "item.icms_above_xml",
    }
    assert all(not row.items and not row.followers for row in result.occurrences)


def test_nf_c_two_items_same_rule_become_items_of_one_cause() -> None:
    """NF-C: mesma divergência em dois itens = uma causa com items[]."""
    key = _key("55", 9998)
    result = _run(
        [_header(9998, key, 200, 200, 24, 200)],
        [_item(9998, "1", 100, 12, cst="000"), _item(9998, "2", 100, 12, cst="000")],
        {key: _invoice(9998, key, (
            _xml_item(1, 100, 12, origin="1"), _xml_item(2, 100, 12, origin="1"),
        ), 200, 24, 200)},
        grouping=True,
    )
    assert len(result.occurrences) == 1
    cause = result.occurrences[0]
    assert cause.cause_id == "item.origin_mismatch"
    assert {entry.item for entry in cause.items} == {"1", "2"}


def test_different_causes_stay_separate() -> None:
    """Causas diferentes na mesma nota não se fundem."""
    key = _key("55", 9997)
    result = _run(
        [_header(9997, key, 100, 100, 20, 110)],
        [_item(9997, "1", 100, 20)],
        {key: _invoice(9997, key, (_xml_item(1, 100, 12, origin="1"),), 100, 12, 100)},
        grouping=True,
    )
    causes = {row.cause_id for row in result.occurrences}
    assert "icms_amount" in causes
    assert "item.origin_mismatch" in causes
    assert len(result.occurrences) == 2


def test_standalone_base_mismatch_is_own_cause_icms_base() -> None:
    """Base divergente com ICMS conferindo é causa própria (icms_base), não follower."""
    key = _key("55", 9996)
    result = _run(
        [_header(9996, key, 100, 100, 12, 110)],
        [_item(9996, "1", 100, 12)],
        {key: _invoice(9996, key, (_xml_item(1, 100, 12),), 100, 12, 100)},
        grouping=True,
    )
    assert len(result.occurrences) == 1
    cause = result.occurrences[0]
    assert cause.cause_id == "icms_base"
    assert cause.rule_id == "header.icms_base_mismatch"
    assert not cause.followers


def test_consolidate_keeps_max_severity_and_promotes_orphan_follower() -> None:
    settings = _settings(True)
    merged = _consolidate([
        _hit("header.icms_above_xml", "Média"),
        _hit("item.icms_above_xml", "Alta", item="2"),
        _hit("header.icms_base_mismatch", "Alta", follower=True, cause="icms_amount"),
    ], settings)
    assert len(merged) == 1
    assert merged[0]["severity"] == "Alta"
    assert len(merged[0]["cause_items"]) == 2
    assert len(merged[0]["cause_followers"]) == 1
    # Acompanhante órfão (principal suprimida) é promovido — nunca desaparece.
    orphan = _consolidate([
        _hit("header.icms_base_mismatch", "Média", follower=True, cause="icms_amount"),
    ], settings)
    assert len(orphan) == 1
    assert orphan[0]["cause_items"]
    assert not orphan[0]["cause_followers"]


def test_stable_key_v2_from_v1_parses_key44_and_doc_forms() -> None:
    key44 = f"01|{KEY}|item.origin_mismatch|CST (origem)|2"
    assert stable_key_v2_from_v1(key44, cause_id_for) == f"01|{KEY}|cause:item.origin_mismatch"
    doc = "01|doc:22288|1|000001|01|header.icms_above_xml|ICMS|"
    assert stable_key_v2_from_v1(doc, cause_id_for) == "01|doc:22288|1|000001|01|cause:icms_amount"
    # «Acompanha» v1 é indistinguível: migração mapeia conservadoramente para icms_base.
    ambiguous = f"01|{KEY}|header.icms_base_mismatch|Base ICMS|"
    assert stable_key_v2_from_v1(ambiguous, cause_id_for).endswith("cause:icms_base")
    assert stable_key_v2_from_v1(f"01|{KEY}|cause:icms_amount", cause_id_for) is None
    assert stable_key_v2_from_v1("lixo", cause_id_for) is None


def _add_analysis(store: MemoryEntryAuditStore, created: datetime, **overrides) -> str:
    analysis_id = str(uuid4())
    store.analyses[analysis_id] = {
        "id": analysis_id, "status": "done",
        "date_from": date(2026, 11, 1), "date_to": date(2026, 11, 17),
        "document_types": ["nfe"], "branches": ["01"],
        "requested_via": "user", "created_at": created,
        **overrides,
    }
    run_id = str(uuid4())
    store.runs[run_id] = {
        "id": run_id, "analysis_id": analysis_id, "branch_code": "01",
        "status": "done", "stage": "done", "error_message": "", "counts": {},
    }
    return analysis_id


def _cause_row(analysis_id: str, run_id: str, stable_key: str, **overrides) -> dict:
    return {
        "analysis_id": analysis_id, "run_id": run_id, "stable_key": stable_key,
        "cause_id": "icms_amount", "severity": "Alta", "theme": "icms",
        "title": "ICMS calculado acima do XML", "document_number": "9999",
        "series": "1", "supplier_name": "Fornecedor", "access_key": KEY,
        "branch": "01", "difference": "8", "field": "icms",
        "items": [], "followers": [],
        **overrides,
    }


def _service(store: MemoryEntryAuditStore) -> EntryAuditService:
    class _Ports:
        def documents(self, **_kw):
            return []

        def documents_by_access_keys(self, **_kw):
            return []

        def items(self, **_kw):
            return []

        def fiscal_book(self, **_kw):
            return []

        def tes(self):
            return []

        def branches(self):
            return []

        def download_by_key(self, **_kw):
            return None

        def list_issued(self, **_kw):
            return []

        def find_open(self, **_kw):
            return None

    ports = _Ports()
    return EntryAuditService(store, ports, ports, ports, AuditConfig(), lookback_days=30)


def test_pending_queue_keeps_latest_analysis_per_note_and_cause() -> None:
    """FA-5: a fila mostra a ocorrência da análise mais recente, por nota+causa."""
    store = MemoryEntryAuditStore()
    old_analysis = _add_analysis(store, datetime(2026, 11, 12, tzinfo=timezone.utc))
    old_run = next(iter(store.runs))
    store.occurrences.append(_cause_row(old_analysis, old_run, "old-key", severity="Baixa", title="antiga"))
    new_analysis = _add_analysis(store, datetime(2026, 11, 15, tzinfo=timezone.utc))
    new_run = [run for run in store.runs.values() if run["analysis_id"] == new_analysis][0]
    store.occurrences.append(_cause_row(new_analysis, new_run["id"], f"01|{KEY}|cause:icms_amount"))
    service = _service(store)
    payload = service.pending()
    assert payload["total"] == 1
    assert payload["items"][0]["stable_key"] == f"01|{KEY}|cause:icms_amount"
    assert payload["items"][0]["title"] != "antiga"
    assert payload["kpis"]["pending"] == 1
    assert payload["kpis"]["pending_high"] == 1
    # Resolvida sai da pendência.
    store.upsert_status(f"01|{KEY}|cause:icms_amount", kind="occurrence", status="resolved", user_id="u", user_name="Ana")
    payload = service.pending()
    assert payload["kpis"]["resolved"] == 1
    assert payload["kpis"]["pending"] == 0


def test_cause_groups_split_clean_corrected_and_pending() -> None:
    """FA-7: três grupos — sem problema, corrigida (causas resolvidas), pendente."""
    documents = [
        {"access_key": "A", "branch": "01", "document_number": "1", "series": "1"},
        {"access_key": "B", "branch": "01", "document_number": "2", "series": "1"},
        {"access_key": "C", "branch": "01", "document_number": "3", "series": "1"},
    ]
    occurrences = [
        {"access_key": "B", "branch": "01", "document_number": "2", "series": "1", "cause_id": "icms_amount", "stable_key": "k1", "severity": "Alta", "difference": "5"},
        {"access_key": "C", "branch": "01", "document_number": "3", "series": "1", "cause_id": "icms_amount", "stable_key": "k2", "severity": "Alta", "difference": "7"},
        {"access_key": "C", "branch": "01", "document_number": "3", "series": "1", "cause_id": "item.origin_mismatch", "stable_key": "k3", "severity": "Média", "difference": ""},
    ]
    groups = _cause_groups(documents, occurrences, {"k2": {"status": "resolved"}})
    assert groups == {
        "clean": 1, "corrected": 0, "pending": 2,
        "pending_high": 1, "pending_medium": 1, "pending_difference": 5.0,
    }
    # C com as duas causas resolvidas vira «corrigida».
    groups = _cause_groups(documents, occurrences, {"k2": {"status": "resolved"}, "k3": {"status": "resolved"}})
    assert groups["corrected"] == 1
    assert groups["pending"] == 1
    # Linhas v1 (sem cause_id) não produzem o bloco.
    assert _cause_groups(documents, [{"access_key": "B", "branch": "01", "document_number": "2", "series": "1"}], {}) is None
