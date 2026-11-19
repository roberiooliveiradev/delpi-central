"""T19/FA-8 a FA-12 — IBS/CBS nas entradas (NF-e e CT-e): presença, valores e livro."""

from __future__ import annotations

from datetime import date, datetime
from xml.etree import ElementTree as ET

from controllership_finance_app.domain.entry_audit.engine import audit
from controllership_finance_app.domain.entry_audit.models import (
    AuditConfig,
    ProtheusHeader,
    ProtheusItem,
    ReformBookLine,
    ReformTaxLine,
    TesRecord,
    XmlDocument,
    XmlItem,
)
from controllership_finance_app.infrastructure.entry_audit.xml_reader import (
    _ibscbs,
    read_xml_payloads,
)

_CTE_NS = "http://www.portalfiscal.inf.br/cte"


def _cte_xml(access_key: str, number: int, total: float, *, with_ibscbs: bool = True) -> bytes:
    ibscbs = (
        "<IBSCBS><CST>000</CST><cClassTrib>000001</cClassTrib><gIBSCBS>"
        "<vBC>50.00</vBC>"
        "<gIBSUF><pIBSUF>0.10</pIBSUF><vIBSUF>0.05</vIBSUF></gIBSUF>"
        "<gIBSMun><pIBSMun>0.00</pIBSMun><vIBSMun>0.00</vIBSMun></gIBSMun>"
        "<vIBS>0.05</vIBS>"
        "<gCBS><pCBS>0.90</pCBS><vCBS>0.45</vCBS></gCBS>"
        "</gIBSCBS></IBSCBS>"
        if with_ibscbs else ""
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><cteProc xmlns="{_CTE_NS}" versao="4.00">'
        f'<CTe><infCte Id="CTe{access_key}" versao="4.00">'
        f'<ide><mod>57</mod><serie>1</serie><nCT>{number}</nCT><dhEmi>2026-11-12T11:00:00-03:00</dhEmi>'
        f'<CFOP>5352</CFOP><UFIni>SC</UFIni><UFFim>SC</UFFim><toma3><toma>3</toma></toma3></ide>'
        f'<emit><CNPJ>{SUPPLIER}</CNPJ><xNome>Transportadora Sintetica</xNome>'
        f'<enderEmit><UF>SC</UF></enderEmit><CRT>3</CRT></emit>'
        f'<dest><CNPJ>{COMPANY}</CNPJ><enderDest><UF>SC</UF></enderDest></dest>'
        f'<vPrest><vTPrest>{total:.2f}</vTPrest></vPrest>'
        f'<imp><ICMS><ICMS00><CST>00</CST><vBC>50.00</vBC><pICMS>12.00</pICMS><vICMS>6.00</vICMS>'
        f'</ICMS00></ICMS>{ibscbs}<vTotDFe>{total:.2f}</vTotDFe></imp>'
        f'</infCte></CTe><protCTe><infProt><cStat>100</cStat></infProt></protCTe></cteProc>'
    ).encode()

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


def _header(number: int, access_key: str, gross: float, *, species: str = "SPED") -> ProtheusHeader:
    return ProtheusHeader(
        branch="01", number=str(number), series="1", supplier_code="000001", supplier_store="01",
        supplier_name="Fornecedor Sintetico", supplier_state="SC", supplier_tax_id=SUPPLIER,
        species=species, own_form="N", access_key=access_key, issue_date=DAY, received_date=DAY,
        freight_amount=0, expense_amount=0, icms_base=0, icms_amount=0, ipi_base=0, ipi_amount=0,
        goods_amount=gross, gross_amount=gross, discount_amount=0, st_base=0, st_amount=0, insurance_amount=0,
    )


def _item(number: int, item: str, total: float, *, cfop: str = "1556", tes: str = "001") -> ProtheusItem:
    return ProtheusItem(
        branch="01", number=str(number), series="1", supplier_code="000001", supplier_store="01",
        item=item, product_code=f"P{item}", cfop=cfop, tax_situation="090", tes=tes, total_amount=total,
        icms_base=0, icms_rate=0, icms_amount=0, ipi_base=0, ipi_rate=0, ipi_amount=0, st_amount=0,
    )


def _xml_item(number: int, amount: float, *, ibscbs: bool = True, cbs: float = 9.0, ibs_uf: float = 1.0, ibs_mun: float = 0.0, cfop: str = "5101") -> XmlItem:
    return XmlItem(
        number=number, product_code=f"P{number}", description=f"Peca {number}", ncm="84818099", cfop=cfop,
        amount=amount, origin="0", cst="00", csosn="", icms_base=0, icms_rate=0, icms_amount=0,
        ipi_amount=0, ipi_base=0, ipi_rate=0, st_amount=0,
        has_ibscbs=ibscbs, ibscbs_cst="000", ibscbs_class="000001" if ibscbs else "",
        reform_base=amount if ibscbs else 0.0,
        ibs_uf_rate=0.1, ibs_uf_amount=ibs_uf,
        ibs_mun_rate=0.0, ibs_mun_amount=ibs_mun,
        cbs_rate=0.9, cbs_amount=cbs,
    )


def _invoice(number: int, access_key: str, items: tuple[XmlItem, ...], total: float) -> XmlDocument:
    return XmlDocument(
        access_key=access_key, model="55", number=number, series="1", issued_at=WHEN,
        issuer_tax_id=SUPPLIER, issuer_name="Fornecedor Sintetico", issuer_state="SC",
        recipient_tax_id=COMPANY, direction="Saída", crt="3", goods_amount=total, freight_amount=0,
        discount_amount=0, other_amount=0, icms_base=0, icms_amount=0, st_amount=0, ipi_amount=0,
        total_amount=total, status_code="100", items=items,
        has_ibscbs=any(item.has_ibscbs for item in items),
        reform_base=total,
        ibs_uf_amount=sum(item.ibs_uf_amount for item in items),
        ibs_mun_amount=sum(item.ibs_mun_amount for item in items),
        cbs_amount=sum(item.cbs_amount for item in items),
    )


def _cte(number: int, access_key: str, *, ibscbs: bool = True, cbs: float = 4.5) -> XmlDocument:
    return XmlDocument(
        access_key=access_key, model="57", number=number, series="1", issued_at=WHEN,
        issuer_tax_id=SUPPLIER, issuer_name="Transportadora Sintetica", issuer_state="SC",
        recipient_tax_id=COMPANY, direction="CT-e", crt="3", goods_amount=0, freight_amount=0,
        discount_amount=0, other_amount=0, icms_base=50, icms_amount=6, st_amount=0, ipi_amount=0,
        total_amount=50, status_code="100", service_amount=50, cfop="5352", origin_state="SC",
        destination_state="SC", taker_tax_id=COMPANY, icms_rate=12, cst="00",
        has_ibscbs=ibscbs, ibscbs_cst="000", ibscbs_class="000001" if ibscbs else "",
        reform_base=50 if ibscbs else 0.0, ibs_uf_rate=0.1, ibs_uf_amount=0.5 if ibscbs else 0.0,
        cbs_rate=0.9, cbs_amount=cbs if ibscbs else 0.0,
    )


def _reform(number: int, item: str, tax: str, amount: float, *, base: float = 0.0, rate: float = 0.0, rule: str = "REGRA001", tes: str = "001") -> ReformTaxLine:
    return ReformTaxLine(
        branch="01", number=str(number), series="1", supplier_code="000001", supplier_store="01",
        item=item, tes=tes, tax_code=tax, rule_code=rule, base_amount=base, tax_rate=rate, tax_amount=amount,
    )


def _booked(number: int, item: str, tax: str, amount: float, *, base: float = 0.0) -> ReformBookLine:
    return ReformBookLine(
        branch="01", number=str(number), series="1", supplier_code="000001", supplier_store="01",
        item=item, tax_code=tax, cst="000", base_amount=base, tax_rate=0.9, tax_amount=amount,
    )


TES = [
    TesRecord("001", "Compra", "Nao", "Nao", "Outros", "Nao", "Nao", "Outros", "Nao", "Entrada", "556"),
    TesRecord("036", "Frete", "Sim", "Sim", "Tributado", "Nao", "Nao", "Outros", "Nao", "Entrada", "352"),
]

CONFIG = AuditConfig(improvements_enabled=False, ibscbs_enabled=True, cause_grouping_enabled=True)


def _run(headers, items, invoices=None, ctes=None, *, reform=(), book=None, config=CONFIG):
    return audit(
        branch="01", company_tax_id=COMPANY, company_state="SC", headers=headers, items=items,
        tes_records=TES, invoices=invoices or {}, ctes=ctes or {}, config=config,
        reform_taxes=list(reform), reform_book=book,
    )


def _rules(result) -> list[str]:
    return [occurrence.rule_id for occurrence in result.occurrences]


def test_xml_ibscbs_without_f2d_flags_xml_not_posted() -> None:
    key = _key("55", 1001)
    result = _run(
        [_header(1001, key, 100)], [_item(1001, "1", 100)],
        {key: _invoice(1001, key, (_xml_item(1, 100),), 100)},
    )
    ibscbs = [occurrence for occurrence in result.occurrences if occurrence.rule_id.startswith("ibscbs.")]
    assert [occurrence.rule_id for occurrence in ibscbs] == ["ibscbs.xml_not_posted"]
    assert ibscbs[0].severity == "Alta"
    assert ibscbs[0].cause_id == "ibscbs.xml_not_posted"
    assert "TES 001" in ibscbs[0].action
    assert "000001" in ibscbs[0].action  # cClassTrib no texto


def test_no_ibscbs_and_no_f2d_flags_posting_missing() -> None:
    key = _key("55", 1002)
    result = _run(
        [_header(1002, key, 100)], [_item(1002, "1", 100)],
        {key: _invoice(1002, key, (_xml_item(1, 100, ibscbs=False),), 100)},
    )
    assert "ibscbs.posting_missing" in _rules(result)
    assert "ibscbs.xml_not_posted" not in _rules(result)


def test_posted_values_matching_xml_stay_clean() -> None:
    key = _key("55", 1003)
    result = _run(
        [_header(1003, key, 100)], [_item(1003, "1", 100)],
        {key: _invoice(1003, key, (_xml_item(1, 100),), 100)},
        reform=[
            _reform(1003, "1", "CBSFED", 9.0, base=100, rate=0.9),
            _reform(1003, "1", "IBSEST", 1.0, base=100, rate=0.1, rule="IBS001"),
        ],
    )
    assert not [rule for rule in _rules(result) if rule.startswith("ibscbs.")]


def test_posted_cbs_differs_flags_value_mismatch_with_tes_and_rule() -> None:
    key = _key("55", 1004)
    result = _run(
        [_header(1004, key, 100)], [_item(1004, "1", 100)],
        {key: _invoice(1004, key, (_xml_item(1, 100),), 100)},
        reform=[_reform(1004, "1", "CBSFED", 7.0, base=100, rate=0.9)],
    )
    mismatches = [occurrence for occurrence in result.occurrences if occurrence.rule_id == "ibscbs.value_mismatch"]
    assert len(mismatches) == 1
    assert mismatches[0].severity == "Alta"
    assert "TES 001" in mismatches[0].action and "REGRA001" in mismatches[0].action
    # causa única: item + total da nota dentro da mesma ocorrência
    fields = {item.field for item in mismatches[0].items}
    assert "CBS" in fields


def test_cte_ibscbs_not_posted_flags_at_document_level() -> None:
    key = _key("57", 2001)
    result = _run(
        [_header(2001, key, 50, species="CTE")], [_item(2001, "1", 50, cfop="1352", tes="036")],
        ctes={key: _cte(2001, key)},
    )
    assert "ibscbs.xml_not_posted" in _rules(result)


def test_posted_without_xml_ibscbs_produces_no_occurrence() -> None:
    """FA-19 (i): lançamento com F2D e XML sem IBSCBS não gera ocorrência ibscbs.*."""
    key = _key("55", 2006)
    reform = [
        _reform(2006, "1", "CBSFED", 9.0, base=1000.0, rate=0.9, rule="CBS100"),
        _reform(2006, "1", "IBSEST", 1.0, base=1000.0, rate=0.1, rule="IBS100"),
    ]
    result = _run(
        [_header(2006, key, 1000)], [_item(2006, "1", 1000)],
        {key: _invoice(2006, key, (_xml_item(1, 1000, ibscbs=False),), 1000)},
        reform=reform,
    )
    assert not [rule for rule in _rules(result) if rule.startswith("ibscbs.")]


def test_posted_and_xml_with_different_values_still_flags() -> None:
    """FA-19 (ii): IBSCBS nos dois lados com valores diferentes → value_mismatch continua."""
    key = _key("55", 2007)
    reform = [
        _reform(2007, "1", "CBSFED", 12.0, base=1000.0, rate=0.9, rule="CBS100"),
        _reform(2007, "1", "IBSEST", 1.3, base=1000.0, rate=0.1, rule="IBS100"),
    ]
    result = _run(
        [_header(2007, key, 1000)], [_item(2007, "1", 1000)],
        {key: _invoice(2007, key, (_xml_item(1, 1000, cbs=7.19, ibs_uf=0.80),), 1000)},
        reform=reform,
    )
    assert "ibscbs.value_mismatch" in _rules(result)


def test_cte_posted_without_xml_ibscbs_produces_no_occurrence() -> None:
    """FA-19 (iii): CT-e lançado com F2D e XML sem IBSCBS → nenhuma ocorrência ibscbs.*."""
    key = _key("57", 2008)
    reform = [
        _reform(2008, "1", "CBSFED", 0.45, base=50.0, rate=0.9, rule="CBS100", tes="036"),
        _reform(2008, "1", "IBSEST", 0.05, base=50.0, rate=0.1, rule="IBS100", tes="036"),
    ]
    result = _run(
        [_header(2008, key, 50, species="CTE")], [_item(2008, "1", 50, cfop="1352", tes="036")],
        ctes={key: _cte(2008, key, ibscbs=False)}, reform=reform,
    )
    assert not [rule for rule in _rules(result) if rule.startswith("ibscbs.")]


def test_flag_off_produces_no_ibscbs_hits() -> None:
    key = _key("55", 1005)
    config = AuditConfig(improvements_enabled=False, ibscbs_enabled=False, cause_grouping_enabled=True)
    result = _run(
        [_header(1005, key, 100)], [_item(1005, "1", 100)],
        {key: _invoice(1005, key, (_xml_item(1, 100),), 100)},
        config=config,
    )
    assert not [rule for rule in _rules(result) if rule.startswith("ibscbs.")]


def test_exceptions_skip_the_item() -> None:
    key = _key("55", 1006)
    config = AuditConfig(improvements_enabled=False, ibscbs_enabled=True, ibscbs_exceptions="tes:001", cause_grouping_enabled=True)
    result = _run(
        [_header(1006, key, 100)], [_item(1006, "1", 100)],
        {key: _invoice(1006, key, (_xml_item(1, 100),), 100)},
        config=config,
    )
    assert not [rule for rule in _rules(result) if rule.startswith("ibscbs.")]


def test_book_mismatch_only_after_book_from() -> None:
    key = _key("55", 1007)
    posted = [_reform(1007, "1", "CBSFED", 9.0, base=100, rate=0.9)]
    book = [_booked(1007, "1", "CBSFED", 8.0, base=100)]
    off = _run(
        [_header(1007, key, 100)], [_item(1007, "1", 100)],
        {key: _invoice(1007, key, (_xml_item(1, 100),), 100)},
        reform=posted, book=book,
    )
    assert "ibscbs.book_mismatch" not in _rules(off)

    config = AuditConfig(improvements_enabled=False, ibscbs_enabled=True, ibscbs_book_from="2026-01-01", cause_grouping_enabled=True)
    on = _run(
        [_header(1007, key, 100)], [_item(1007, "1", 100)],
        {key: _invoice(1007, key, (_xml_item(1, 100),), 100)},
        reform=posted, book=book, config=config,
    )
    assert "ibscbs.book_mismatch" in _rules(on)


def test_cte_parser_reads_ibscbs_from_imp_group() -> None:
    """T19R2/A: no CT-e o grupo de impostos é infCte/imp (não «imposto»)."""
    key = _key("57", 2002)
    _, ctes, ignored = read_xml_payloads([_cte_xml(key, 2002, 50.0)])
    assert ignored == 0
    document = ctes[key]
    assert document.has_ibscbs
    assert document.ibscbs_cst == "000"
    assert document.ibscbs_class == "000001"
    assert document.reform_base == 50.0
    assert document.ibs_uf_rate == 0.1
    assert document.ibs_uf_amount == 0.05
    assert document.ibs_mun_rate == 0.0
    assert document.ibs_mun_amount == 0.0
    assert document.cbs_rate == 0.9
    assert document.cbs_amount == 0.45


def test_cte_parsed_with_ibscbs_and_no_f2d_flags_xml_not_posted() -> None:
    """T19R2/A: CT-e real (com IBSCBS) e sem cálculo F2D → xml_not_posted, nunca posting_missing."""
    key = _key("57", 2003)
    _, ctes, _ = read_xml_payloads([_cte_xml(key, 2003, 50.0)])
    result = _run(
        [_header(2003, key, 50, species="CTE")], [_item(2003, "1", 50, cfop="1352", tes="036")],
        ctes=ctes,
    )
    assert "ibscbs.xml_not_posted" in _rules(result)
    assert "ibscbs.posting_missing" not in _rules(result)


def test_value_mismatch_hints_lc214_when_posted_base_includes_other_taxes() -> None:
    """T19R2/C — P1: lançado ≈ vProd−vDesc e XML ≈ vProd−vDesc−ICMS−PIS−COFINS."""
    key = _key("55", 2004)
    xml_item = XmlItem(
        number=1, product_code="P1", description="Peca 1", ncm="84818099", cfop="5101",
        amount=1000.0, origin="0", cst="00", csosn="", icms_base=1000.0, icms_rate=12.0,
        icms_amount=120.0, ipi_amount=0.0, ipi_base=0.0, ipi_rate=0.0, st_amount=0.0,
        pis_amount=14.52, cofins_amount=66.88,
        has_ibscbs=True, ibscbs_cst="000", ibscbs_class="000001",
        reform_base=798.60, ibs_uf_rate=0.1, ibs_uf_amount=0.80,
        ibs_mun_rate=0.0, ibs_mun_amount=0.0, cbs_rate=0.9, cbs_amount=7.19,
    )
    invoice = _invoice(2004, key, (xml_item,), 1000.0)
    invoice = XmlDocument(**{**invoice.__dict__, "reform_base": 798.60})
    reform = [
        _reform(2004, "1", "CBSFED", 9.0, base=1000.0, rate=0.9, rule="CBS100"),
        _reform(2004, "1", "IBSEST", 1.0, base=1000.0, rate=0.1, rule="IBS100"),
    ]
    result = _run(
        [_header(2004, key, 1000)], [_item(2004, "1", 1000)], {key: invoice}, reform=reform,
    )
    texts = [occurrence.action for occurrence in result.occurrences if occurrence.rule_id == "ibscbs.value_mismatch"]
    assert texts
    assert any(
        "LC 214/2025" in text and "CBS100" in text for text in texts
    )


def test_value_mismatch_without_p1_has_no_lc214_hint() -> None:
    """Base divergente fora do padrão P1: texto sem a orientação da LC 214."""
    key = _key("55", 2005)
    xml_item = XmlItem(
        number=1, product_code="P1", description="Peca 1", ncm="84818099", cfop="5101",
        amount=1000.0, origin="0", cst="00", csosn="", icms_base=1000.0, icms_rate=12.0,
        icms_amount=120.0, ipi_amount=0.0, ipi_base=0.0, ipi_rate=0.0, st_amount=0.0,
        pis_amount=14.52, cofins_amount=66.88,
        has_ibscbs=True, ibscbs_cst="000", ibscbs_class="000001",
        reform_base=798.60, ibs_uf_rate=0.1, ibs_uf_amount=0.80,
        ibs_mun_rate=0.0, ibs_mun_amount=0.0, cbs_rate=0.9, cbs_amount=7.19,
    )
    invoice = _invoice(2005, key, (xml_item,), 1000.0)
    invoice = XmlDocument(**{**invoice.__dict__, "reform_base": 798.60})
    # Lançado com base 800 — não é vProd−vDesc e não é a fórmula da LC 214.
    reform = [
        _reform(2005, "1", "CBSFED", 7.2, base=800.0, rate=0.9, rule="CBS100"),
        _reform(2005, "1", "IBSEST", 0.8, base=800.0, rate=0.1, rule="IBS100"),
    ]
    result = _run(
        [_header(2005, key, 1000)], [_item(2005, "1", 1000)], {key: invoice}, reform=reform,
    )
    texts = [occurrence.action for occurrence in result.occurrences if occurrence.rule_id == "ibscbs.value_mismatch"]
    assert texts
    assert all("LC 214/2025" not in text for text in texts)


def test_ibscbs_group_parses_from_xml_item() -> None:
    detail = ET.fromstring(
        """
        <det>
          <imposto>
            <IBSCBS>
              <CST>000</CST>
              <cClassTrib>000001</cClassTrib>
              <gIBSCBS>
                <vBC>100.00</vBC>
                <gIBSUF><pIBSUF>0.10</pIBSUF><vIBSUF>0.10</vIBSUF></gIBSUF>
                <gIBSMun><pIBSMun>0.00</pIBSMun><vIBSMun>0.00</vIBSMun></gIBSMun>
                <vIBS>0.10</vIBS>
                <gCBS><pCBS>0.90</pCBS><vCBS>0.90</vCBS></gCBS>
              </gIBSCBS>
            </IBSCBS>
          </imposto>
        </det>
        """
    )
    parsed = _ibscbs(detail)
    assert parsed == {
        "cst": "000", "class": "000001", "base": 100.0,
        "ibs_uf_rate": 0.1, "ibs_uf_amount": 0.1,
        "ibs_mun_rate": 0.0, "ibs_mun_amount": 0.0,
        "cbs_rate": 0.9, "cbs_amount": 0.9,
    }
