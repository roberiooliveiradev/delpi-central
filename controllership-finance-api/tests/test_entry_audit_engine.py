"""Motor da auditoria: caso que a skill aponta, irmão e caso que não pode apontar."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime

from controllership_finance_app.domain.entry_audit.engine import audit
from controllership_finance_app.domain.entry_audit.models import (
    AuditConfig,
    ProtheusHeader,
    ProtheusItem,
    TesRecord,
    XmlDocument,
    XmlItem,
)

SUPPLIER = "22222222000191"
COMPANY = "11111111000191"
WHEN = datetime(2026, 11, 12, 10, 0, 0)
DAY = date(2026, 11, 12)


def _key(model: str, number: int, cnpj: str = SUPPLIER) -> str:
    body = f"422611{cnpj}{model}001{number:09d}100000001"
    total, weight = 0, 2
    for digit in reversed(body):
        total += int(digit) * weight
        weight = 2 if weight == 9 else weight + 1
    check = 11 - total % 11
    return body + str(0 if check >= 10 else check)


def _header(number: int, access_key: str, gross: float, goods: float, icms: float, *, species: str = "SPED") -> ProtheusHeader:
    return ProtheusHeader(
        branch="01", number=str(number), series="1", supplier_code="000001", supplier_store="01",
        supplier_name="Fornecedor Sintetico", supplier_state="SC", supplier_tax_id=SUPPLIER,
        species=species, own_form="N", access_key=access_key, issue_date=DAY, received_date=DAY,
        freight_amount=0, expense_amount=0, icms_base=goods, icms_amount=icms, ipi_base=0, ipi_amount=0,
        goods_amount=goods, gross_amount=gross, discount_amount=0, st_base=0, st_amount=0, insurance_amount=0,
    )


def _item(number: int, item: str, total: float, icms: float, *, cfop: str = "1101", cst: str = "000", tes: str = "001", rate: float = 12) -> ProtheusItem:
    return ProtheusItem(
        branch="01", number=str(number), series="1", supplier_code="000001", supplier_store="01",
        item=item, product_code=f"P{item}", cfop=cfop, tax_situation=cst, tes=tes, total_amount=total,
        icms_base=total if icms else 0, icms_rate=rate if icms else 0, icms_amount=icms,
        ipi_base=0, ipi_rate=0, ipi_amount=0, st_amount=0,
    )


def _xml_item(number: int, amount: float, icms: float, *, origin: str = "0", cst: str = "00", cfop: str = "5101") -> XmlItem:
    return XmlItem(
        number=number, product_code=f"P{number}", description=f"Peca {number}", ncm="84818099", cfop=cfop,
        amount=amount, origin=origin, cst=cst, csosn="", icms_base=amount, icms_rate=12, icms_amount=icms,
        ipi_amount=0, ipi_base=0, ipi_rate=0, st_amount=0,
    )


def _invoice(number: int, access_key: str, items: tuple[XmlItem, ...], total: float, icms: float) -> XmlDocument:
    return XmlDocument(
        access_key=access_key, model="55", number=number, series="1", issued_at=WHEN,
        issuer_tax_id=SUPPLIER, issuer_name="Fornecedor Sintetico", issuer_state="SC",
        recipient_tax_id=COMPANY, direction="Saída", crt="3", goods_amount=total, freight_amount=0,
        discount_amount=0, other_amount=0, icms_base=total, icms_amount=icms, st_amount=0, ipi_amount=0,
        total_amount=total, status_code="100", items=items,
    )


TES = [
    TesRecord("001", "Compra com credito", "Sim", "Sim", "Tributado", "Nao", "Nao", "Outros", "Nao", "Entrada", "101"),
    TesRecord("002", "Compra sem credito", "Sim", "Nao", "Outros", "Nao", "Nao", "Outros", "Nao", "Entrada", "101"),
    TesRecord("036", "Frete com credito", "Sim", "Sim", "Tributado", "Nao", "Nao", "Outros", "Nao", "Entrada", "352"),
]


def _run(headers, items, invoices, ctes=None):
    return audit(
        branch="01", company_tax_id=COMPANY, company_state="SC", headers=headers, items=items,
        tes_records=TES, invoices=invoices, ctes=ctes or {}, config=AuditConfig(improvements_enabled=False),
    )


def test_matching_note_and_matching_cte_stay_clean() -> None:
    key = _key("55", 1001)
    cte_key = _key("57", 2001)
    invoice = _invoice(1001, key, (_xml_item(1, 100, 12),), 100, 12)
    cte = XmlDocument(
        access_key=cte_key, model="57", number=2001, series="1", issued_at=WHEN,
        issuer_tax_id=SUPPLIER, issuer_name="Transportadora Sintetica", issuer_state="SC",
        recipient_tax_id=COMPANY, direction="CT-e", crt="3", goods_amount=0, freight_amount=0,
        discount_amount=0, other_amount=0, icms_base=50, icms_amount=6, st_amount=0, ipi_amount=0,
        total_amount=50, status_code="100", service_amount=50, cfop="5352", origin_state="SC",
        destination_state="SC", taker_tax_id=COMPANY, icms_rate=12, cst="00", linked_keys=(key,),
    )
    result = _run(
        [_header(1001, key, 100, 100, 12), _header(2001, cte_key, 50, 50, 6, species="CTE")],
        [_item(1001, "1", 100, 12), _item(2001, "1", 50, 6, cfop="1352", tes="036")],
        {key: invoice},
        {cte_key: cte},
    )
    assert result.occurrences == []
    assert result.unmatched == []
    assert result.suppressed == {}


def test_total_mismatch_does_not_invent_a_goods_mismatch() -> None:
    key = _key("55", 1006)
    result = _run(
        [_header(1006, key, 90, 70, 8.4)],
        [_item(1006, "1", 70, 8.4)],
        {key: _invoice(1006, key, (_xml_item(1, 70, 8.4),), 70, 8.4)},
    )
    assert [(row.rule_id, row.title, row.protheus_value, row.xml_value) for row in result.occurrences] == [
        ("header.total_mismatch", "Valor total da nota diverge", "90.00", "70.00"),
    ]


def test_origin_mismatch_on_three_items_and_not_on_a_matching_sibling() -> None:
    key = _key("55", 1002)
    items = tuple(_xml_item(n, 30, 3.6, origin="1") for n in (1, 2, 3))
    result = _run(
        [_header(1002, key, 90, 90, 10.8)],
        [_item(1002, str(n), 30, 3.6) for n in (1, 2, 3)],
        {key: _invoice(1002, key, items, 90, 10.8)},
    )
    assert [row.item for row in result.occurrences] == ["1", "2", "3"]
    assert {row.rule_id for row in result.occurrences} == {"item.origin_mismatch"}
    matched = _run(
        [_header(1002, key, 90, 90, 10.8)],
        [_item(1002, str(n), 30, 3.6, cst="100") for n in (1, 2, 3)],
        {key: _invoice(1002, key, items, 90, 10.8)},
    )
    assert matched.occurrences == []


def test_tes_without_credit_flags_highlighted_icms_and_suppresses_cst_090() -> None:
    key = _key("55", 1007)
    result = _run(
        [_header(1007, key, 40, 40, 0)],
        [_item(1007, "1", 40, 0, cst="090", tes="002", rate=0)],
        {key: _invoice(1007, key, (_xml_item(1, 40, 4.8),), 40, 4.8)},
    )
    assert [(row.rule_id, row.severity) for row in result.occurrences] == [
        ("item.highlighted_icms_not_credited", "Média"),
    ]
    assert result.suppressed["suppressed.cst_090"] == 1
    assert result.suppressed["suppressed.header_icms_not_credited"] == 1


def test_same_cst_difference_is_an_occurrence_when_the_tes_credits() -> None:
    key = _key("55", 1008)
    result = _run(
        [_header(1008, key, 40, 40, 4.8)],
        [_item(1008, "1", 40, 4.8, cst="020")],
        {key: _invoice(1008, key, (_xml_item(1, 40, 4.8, cst="00"),), 40, 4.8)},
    )
    assert [row.rule_id for row in result.occurrences] == ["item.cst_mismatch"]


def test_xml_only_and_protheus_only_are_unmatched_and_a_booked_note_is_not() -> None:
    booked = _key("55", 1001)
    xml_only = _key("55", 1003)
    protheus_only = _key("55", 1004)
    result = _run(
        [_header(1001, booked, 100, 100, 12), _header(1004, protheus_only, 40, 40, 4.8)],
        [_item(1001, "1", 100, 12), _item(1004, "1", 40, 4.8)],
        {
            booked: _invoice(1001, booked, (_xml_item(1, 100, 12),), 100, 12),
            xml_only: _invoice(1003, xml_only, (_xml_item(1, 50, 6),), 50, 6),
        },
    )
    assert [(row.side, row.document_number, row.severity) for row in result.unmatched] == [
        ("xml", "1003", "Média"),
        ("protheus", "1004", "Média"),
    ]
    assert "trânsito" in result.unmatched[0].reason


def test_transit_uses_the_analysis_end_and_is_info() -> None:
    inside = _key("55", 1101)
    outside = _key("55", 1102)
    border = datetime(2026, 11, 9, 8, 0, 0)
    older = datetime(2026, 11, 8, 8, 0, 0)
    result = audit(
        branch="01", company_tax_id=COMPANY, company_state="SC", headers=[], items=[],
        tes_records=TES,
        invoices={
            inside: XmlDocument(
                access_key=inside, model="55", number=1101, series="1", issued_at=border,
                issuer_tax_id=SUPPLIER, issuer_name="Fornecedor Sintetico", issuer_state="SC",
                recipient_tax_id=COMPANY, direction="Saída", crt="3", goods_amount=10, freight_amount=0,
                discount_amount=0, other_amount=0, icms_base=10, icms_amount=1, st_amount=0, ipi_amount=0,
                total_amount=10, status_code="100", items=(_xml_item(1, 10, 1),),
            ),
            outside: XmlDocument(
                access_key=outside, model="55", number=1102, series="1", issued_at=older,
                issuer_tax_id=SUPPLIER, issuer_name="Fornecedor Sintetico", issuer_state="SC",
                recipient_tax_id=COMPANY, direction="Saída", crt="3", goods_amount=10, freight_amount=0,
                discount_amount=0, other_amount=0, icms_base=10, icms_amount=1, st_amount=0, ipi_amount=0,
                total_amount=10, status_code="100", items=(_xml_item(1, 10, 1),),
            ),
        },
        ctes={},
        config=AuditConfig(improvements_enabled=True, period_end=DAY),
    )
    by_number = {row.document_number: row for row in result.unmatched}
    assert by_number["1101"].severity == "Info"
    assert "trânsito" in by_number["1101"].reason
    assert by_number["1102"].severity == "Média"
    assert "trânsito" not in by_number["1102"].reason


OTHER = "33333333000181"
EMITTER = "44444444000191"


def _run_participant(headers, items, invoices, enabled=True):
    return audit(
        branch="01", company_tax_id=COMPANY, company_state="SC", headers=headers, items=items,
        tes_records=TES, invoices=invoices, ctes={},
        config=AuditConfig(improvements_enabled=False, participant_by_type_enabled=enabled),
    )


def test_customer_note_with_matching_participant_stays_clean_and_flag_off_keeps_supplier_rule() -> None:
    key = _key("55", 1201)
    header = replace(
        _header(1201, key, 100, 100, 12),
        supplier_tax_id=OTHER, invoice_type="B",
        participant_kind="customer", participant_name="Cliente Sintetico",
        participant_tax_id=SUPPLIER, participant_state="SC",
    )
    invoice = _invoice(1201, key, (_xml_item(1, 100, 12),), 100, 12)
    items = [_item(1201, "1", 100, 12)]
    assert _run_participant([header], items, {key: invoice}).occurrences == []
    flagged = _run_participant([header], items, {key: invoice}, enabled=False)
    mismatch = [row for row in flagged.occurrences if row.rule_id == "key.supplier_mismatch"]
    assert len(mismatch) == 1
    assert "Fornecedor" in mismatch[0].title


def test_customer_note_with_different_participant_flags_customer_wording() -> None:
    key = _key("55", 1202)
    header = replace(
        _header(1202, key, 100, 100, 12),
        invoice_type="D", participant_kind="customer", participant_name="Cliente Sintetico",
        participant_tax_id=OTHER, participant_state="SC",
    )
    invoice = _invoice(1202, key, (_xml_item(1, 100, 12),), 100, 12)
    result = _run_participant([header], [_item(1202, "1", 100, 12)], {key: invoice})
    mismatch = [row for row in result.occurrences if row.rule_id == "key.supplier_mismatch"]
    assert len(mismatch) == 1
    assert mismatch[0].severity == "Alta"
    assert "cliente" in mismatch[0].title.lower()
    assert "cliente" in mismatch[0].action.lower()


def test_cfop_vs_state_uses_the_customer_state_only_with_the_flag() -> None:
    key = _key("55", 1203)
    header = replace(
        _header(1203, key, 100, 100, 12),
        invoice_type="B", participant_kind="customer", participant_name="Cliente Sintetico",
        participant_tax_id=SUPPLIER, participant_state="ES",
    )
    invoice = _invoice(1203, key, (_xml_item(1, 100, 12),), 100, 12)
    items = [_item(1203, "1", 100, 12, cfop="1101")]
    flagged = _run_participant([header], items, {key: invoice})
    hits = [row for row in flagged.occurrences if row.rule_id == "coherence.cfop_vs_state"]
    assert len(hits) == 1
    assert "participante" in hits[0].title
    clean = _run_participant([header], items, {key: invoice}, enabled=False)
    assert [row for row in clean.occurrences if row.rule_id == "coherence.cfop_vs_state"] == []


def test_seen_heuristic_does_not_mix_customer_and_supplier_with_same_code() -> None:
    key_a, key_b, key_c = _key("55", 1211), _key("55", 1212), _key("55", 1213)
    customer = replace(
        _header(1213, key_c, 100, 100, 12),
        supplier_tax_id="", invoice_type="B", participant_kind="customer",
        participant_name="Cliente Sintetico", participant_tax_id="", participant_state="SC",
    )
    result = _run_participant(
        [_header(1211, key_a, 100, 100, 12), _header(1212, key_b, 100, 100, 12), customer],
        [_item(1211, "1", 100, 12), _item(1212, "1", 100, 12), _item(1213, "1", 100, 12)],
        {
            key_a: _invoice(1211, key_a, (_xml_item(1, 100, 12),), 100, 12),
            key_b: _invoice(1212, key_b, (_xml_item(1, 100, 12),), 100, 12),
            key_c: replace(_invoice(1213, key_c, (_xml_item(1, 100, 12),), 100, 12), issuer_tax_id=EMITTER),
        },
    )
    assert [row for row in result.occurrences if row.rule_id == "key.supplier_mismatch" and row.document_number == "1213"] == []


INPUT_TES = TesRecord("052", "Material de consumo", "Sim", "Sim", "Tributado", "Sim", "Sim", "Tributado", "Sim", "Entrada", "101")
INCOHERENT_INPUT_TES = TesRecord("069", "Insumo livro incoerente", "Sim", "Sim", "Tributado", "Sim", "Nao", "Tributado", "Sim", "Entrada", "101")


def _run_input_tes(tes_code, ipi, xml_ipi, *, input_tes="052,069", record=INPUT_TES, cfop="1101", book=None):
    key = _key("55", 1301)
    header = _header(1301, key, 100, 100, 12)
    item = _item(1301, "1", 100, 12, tes=tes_code)
    xml = XmlDocument(
        access_key=key, model="55", number=1301, series="1", issued_at=WHEN,
        issuer_tax_id=SUPPLIER, issuer_name="Fornecedor Sintetico", issuer_state="SC",
        recipient_tax_id=COMPANY, direction="Saída", crt="3", goods_amount=100, freight_amount=0,
        discount_amount=0, other_amount=0, icms_base=100, icms_amount=12, st_amount=0,
        ipi_amount=xml_ipi, total_amount=100, status_code="100",
        items=(XmlItem(
            number=1, product_code="P1", description="Peca 1", ncm="84818099", cfop="5101",
            amount=100, origin="0", cst="00", csosn="", icms_base=100, icms_rate=12, icms_amount=12,
            ipi_amount=xml_ipi, ipi_base=100, ipi_rate=xml_ipi, st_amount=0,
        ),),
    )
    item_row = ProtheusItem(
        branch="01", number="1301", series="1", supplier_code="000001", supplier_store="01",
        item="1", product_code="P1", cfop=cfop, tax_situation="000", tes=tes_code, total_amount=100,
        icms_base=100, icms_rate=12, icms_amount=12, ipi_base=100, ipi_rate=ipi, ipi_amount=ipi,
        st_amount=0,
    )
    return audit(
        branch="01", company_tax_id=COMPANY, company_state="SC", headers=[header], items=[item_row],
        tes_records=TES + [record, INCOHERENT_INPUT_TES], invoices={key: xml}, ctes={},
        config=AuditConfig(improvements_enabled=False, input_tes=input_tes), fiscal_book=book,
    )


def test_input_tes_drops_ipi_on_consumption_but_keeps_other_ipi_rules() -> None:
    result = _run_input_tes("052", 5, 5)
    assert [row for row in result.occurrences if row.rule_id == "coherence.ipi_on_consumption"] == []
    baseline = _run_input_tes("052", 5, 5, input_tes="")
    assert [row for row in baseline.occurrences if row.rule_id == "coherence.ipi_on_consumption"] != []


def test_input_tes_keeps_ipi_above_xml_and_posted_without_highlight() -> None:
    above = _run_input_tes("052", 8, 5)
    hits = {row.rule_id: row for row in above.occurrences}
    assert "item.ipi_credit_mismatch" in hits
    assert hits["item.ipi_credit_mismatch"].title == "Crédito de IPI acima do XML"
    assert "coherence.ipi_on_consumption" not in hits
    posted = _run_input_tes("069", 5, 0, record=INCOHERENT_INPUT_TES)
    hits = {row.rule_id: row for row in posted.occurrences}
    assert "item.ipi_without_tes_decision" in hits
    assert hits["item.ipi_without_tes_decision"].title == "IPI escriturado sem destaque no XML"
    assert "coherence.ipi_on_consumption" not in hits


def test_consumption_tes_outside_the_input_list_still_flags_ipi_on_consumption() -> None:
    result = _run_input_tes("052", 5, 5, input_tes="018,406")
    assert [row for row in result.occurrences if row.rule_id == "coherence.ipi_on_consumption"] != []


def test_input_tes_also_drops_the_book_path_of_ipi_on_consumption() -> None:
    from controllership_finance_app.domain.entry_audit.models import FiscalBookLine

    book = [FiscalBookLine(
        number="1301", series="1", supplier_code="000001", supplier_store="01",
        item="1", ipi_amount=5, branch="01",
    )]
    result = _run_input_tes("052", 5, 5, book=book)
    assert [row for row in result.occurrences if row.rule_id == "coherence.ipi_on_consumption"] == []
    baseline = _run_input_tes("052", 5, 5, input_tes="", book=book)
    assert [row for row in baseline.occurrences if row.rule_id == "coherence.ipi_on_consumption"] != []
