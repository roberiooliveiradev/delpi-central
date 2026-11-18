"""Paridade por construção: a mesma entrada sintética na skill e no motor.

D11 fica desligado. A skill roda pelo script de referência; o motor não a importa.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from tests.test_entry_audit_engine import (
    COMPANY,
    INPUT_TES,
    SUPPLIER,
    TES,
    _header,
    _invoice,
    _item,
    _key,
    _xml_item,
)
from controllership_finance_app.domain.entry_audit.engine import audit
from controllership_finance_app.domain.entry_audit.models import AuditConfig, TesRecord, XmlDocument
from controllership_finance_app.infrastructure.entry_audit.xml_reader import read_xml_paths

SKILL = (
    Path(__file__).resolve().parents[2]
    / "docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/reference/skill-auditoria-entradas-nfe-protheus/scripts/auditoria.py"
)
NS = "http://www.portalfiscal.inf.br/nfe"
CT = "http://www.portalfiscal.inf.br/cte"
THIRD = "33333333000133"
FOURTH = "44444444000144"
INPUT_TES_CODES = "018,052,069,106,166,169,406"
CONSUMPTION_TES = TesRecord("070", "Material de consumo", "Sim", "Sim", "Tributado", "Sim", "Sim", "Tributado", "Sim", "Entrada", "101")


def _skill_python() -> str:
    candidate = Path("/tmp/entry-audit-skill/bin/python")
    if candidate.is_file():
        return str(candidate)
    return sys.executable


def _require_skill():
    probe = subprocess.run(
        [_skill_python(), "-c", "import pandas, lxml, openpyxl"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        pytest.skip("pandas, lxml e openpyxl são necessários só para rodar a skill de referência")


def _xml_item_text(number: int, amount: float, icms: float, origin: str, ipi: float = 0) -> str:
    ipi_group = (
        f'<IPI><cEnq>999</cEnq><IPITrib><CST>00</CST><vBC>{amount:.2f}</vBC><pIPI>5.00</pIPI><vIPI>{ipi:.2f}</vIPI></IPITrib></IPI>'
        if ipi
        else '<IPI><cEnq>999</cEnq><IPINT><CST>53</CST></IPINT></IPI>'
    )
    return (
        f'<det nItem="{number}"><prod><cProd>P{number}</cProd><xProd>Peca {number}</xProd><NCM>84818099</NCM>'
        f'<CFOP>5101</CFOP><qCom>1.0000</qCom><vUnCom>{amount:.4f}</vUnCom><vProd>{amount:.2f}</vProd></prod>'
        f'<imposto><ICMS><ICMS00><orig>{origin}</orig><CST>00</CST><modBC>3</modBC>'
        f'<vBC>{amount:.2f}</vBC><pICMS>12.00</pICMS><vICMS>{icms:.2f}</vICMS></ICMS00></ICMS>'
        f'{ipi_group}</imposto></det>'
    )


def _nfe(access_key: str, number: int, items: str, goods: float, icms: float, total: float, cnpj: str = SUPPLIER, ipi: float = 0) -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><nfeProc xmlns="{NS}" versao="4.00"><NFe>'
        f'<infNFe Id="NFe{access_key}" versao="4.00"><ide><cUF>42</cUF><mod>55</mod><serie>1</serie>'
        f'<nNF>{number}</nNF><dhEmi>2026-11-12T10:00:00-03:00</dhEmi><tpNF>1</tpNF><natOp>Venda</natOp></ide>'
        f'<emit><CNPJ>{cnpj}</CNPJ><xNome>Emitente Sintetico</xNome><enderEmit><UF>SC</UF></enderEmit><CRT>3</CRT></emit>'
        f'<dest><CNPJ>{COMPANY}</CNPJ><xNome>Empresa Sintetica</xNome><enderDest><UF>SC</UF></enderDest></dest>'
        f'{items}<total><ICMSTot><vBC>{goods:.2f}</vBC><vICMS>{icms:.2f}</vICMS><vICMSDeson>0.00</vICMSDeson>'
        f'<vBCST>0.00</vBCST><vST>0.00</vST><vProd>{goods:.2f}</vProd><vFrete>0.00</vFrete><vSeg>0.00</vSeg>'
        f'<vDesc>0.00</vDesc><vII>0.00</vII><vIPI>{ipi:.2f}</vIPI><vIPIDevol>0.00</vIPIDevol><vPIS>0.00</vPIS>'
        f'<vCOFINS>0.00</vCOFINS><vOutro>0.00</vOutro><vNF>{total:.2f}</vNF></ICMSTot></total>'
        f'</infNFe></NFe><protNFe><infProt><chNFe>{access_key}</chNFe><cStat>100</cStat></infProt></protNFe></nfeProc>'
    )


def _write_fixture(root: Path) -> dict[str, str]:
    keys = {
        "clean": _key("55", 1001),
        "origin": _key("55", 1002),
        "xml_only": _key("55", 1003),
        "protheus_only": _key("55", 1004),
        "total": _key("55", 1006),
        "cst": _key("55", 1007),
        "cte": _key("57", 2001),
        "customer": _key("55", 1008, cnpj=THIRD),
        "customer_mismatch": _key("55", 1010, cnpj=FOURTH),
        "input_tes": _key("55", 1009),
    }
    xml_dir = root / "xml"
    xml_dir.mkdir()
    (xml_dir / "clean.xml").write_text(_nfe(keys["clean"], 1001, _xml_item_text(1, 100, 12, "0"), 100, 12, 100))
    origin_items = "".join(_xml_item_text(n, 30, 3.6, "1") for n in (1, 2, 3))
    (xml_dir / "origin.xml").write_text(_nfe(keys["origin"], 1002, origin_items, 90, 10.8, 90))
    (xml_dir / "xml-only.xml").write_text(_nfe(keys["xml_only"], 1003, _xml_item_text(1, 50, 6, "0"), 50, 6, 50))
    (xml_dir / "total.xml").write_text(_nfe(keys["total"], 1006, _xml_item_text(1, 70, 8.4, "0"), 70, 8.4, 70))
    (xml_dir / "cst.xml").write_text(_nfe(keys["cst"], 1007, _xml_item_text(1, 40, 4.8, "0"), 40, 4.8, 40))
    (xml_dir / "customer.xml").write_text(_nfe(keys["customer"], 1008, _xml_item_text(1, 100, 12, "0"), 100, 12, 100, cnpj=THIRD))
    (xml_dir / "customer-mismatch.xml").write_text(_nfe(keys["customer_mismatch"], 1010, _xml_item_text(1, 60, 7.2, "0"), 60, 7.2, 60, cnpj=FOURTH))
    input_items = _xml_item_text(1, 100, 12, "0", ipi=5) + _xml_item_text(2, 100, 12, "0", ipi=5)
    (xml_dir / "input-tes.xml").write_text(_nfe(keys["input_tes"], 1009, input_items, 200, 24, 200, ipi=10))
    (xml_dir / "cte.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><cteProc xmlns="{CT}" versao="4.00"><CTe><infCte Id="CTe{keys["cte"]}" versao="4.00">'
        f'<ide><mod>57</mod><serie>1</serie><nCT>2001</nCT><dhEmi>2026-11-12T11:00:00-03:00</dhEmi><CFOP>5352</CFOP>'
        f'<natOp>Transporte</natOp><UFIni>SC</UFIni><UFFim>SC</UFFim><toma3><toma>3</toma></toma3></ide>'
        f'<emit><CNPJ>{SUPPLIER}</CNPJ><xNome>Transportadora Sintetica</xNome><enderEmit><UF>SC</UF></enderEmit><CRT>3</CRT></emit>'
        f'<rem><CNPJ>{SUPPLIER}</CNPJ></rem><dest><CNPJ>{COMPANY}</CNPJ><xNome>Empresa Sintetica</xNome><enderDest><UF>SC</UF></enderDest></dest>'
        f'<vPrest><vTPrest>50.00</vTPrest><vRec>50.00</vRec></vPrest><imp><ICMS><ICMS00><CST>00</CST><vBC>50.00</vBC><pICMS>12.00</pICMS><vICMS>6.00</vICMS></ICMS00></ICMS></imp>'
        f'<infCTeNorm><infDoc><infNFe><chave>{keys["clean"]}</chave></infNFe></infDoc></infCTeNorm>'
        f'</infCte></CTe><protCTe><infProt><chCTe>{keys["cte"]}</chCTe><cStat>100</cStat></infProt></protCTe></cteProc>'
    )
    _csv(
        root / "sf1.csv",
        ["Filial", "Numero", "Serie", "Fornecedor", "Loja", "Estado", "Nome Forn.", "CNPJ", "Tipo da Nota", "Form. Prop.", "Espec.Docum.", "Chave NFe", "DT Emissao", "Dt. Receb.", "Vlr.Frete", "Vlr.Despesas", "Base p/ICMS", "Vlr.ICMS", "Base p/IPI", "Vlr.IPI", "Vlr.Mercad", "Vlr.Bruto", "Descontos", "Base ICM Sol", "ICMS Solid.", "Vlr.Seguro"],
        [
            _sf1(1001, "SPED", keys["clean"], "100", "100", "12", "100"),
            _sf1(1002, "SPED", keys["origin"], "90", "90", "10.8", "90"),
            _sf1(1004, "SPED", keys["protheus_only"], "40", "40", "4.8", "40"),
            _sf1(1006, "SPED", keys["total"], "90", "70", "8.4", "70"),
            _sf1(1007, "SPED", keys["cst"], "40", "40", "0", "0"),
            _sf1(2001, "CTE", keys["cte"], "50", "50", "6", "50"),
            _sf1(1008, "SPED", keys["customer"], "100", "100", "12", "100", tipo="B", code="C0051", store="02", state="", name="", cnpj=""),
            _sf1(1010, "SPED", keys["customer_mismatch"], "60", "60", "7.2", "60", tipo="B", code="C0051", store="02", state="", name="", cnpj=""),
            _sf1(1009, "SPED", keys["input_tes"], "200", "200", "24", "200"),
        ],
    )
    _csv(
        root / "sa1.csv",
        ["Filial", "Codigo", "Loja", "Nome", "CNPJ", "Estado"],
        [["01", "C0051", "02", "Cliente Sintetico", THIRD, "SC"]],
    )
    _csv(
        root / "sd1.csv",
        ["Filial", "Documento", "Serie", "Forn/Cliente", "Loja", "Cod. Fiscal", "Sit.Tribut.", "Tipo Entrada", "Item NF", "Produto", "Quantidade", "Vlr.Unitario", "Vlr.Total", "Base Icms", "Aliq. ICMS", "Vlr.ICMS", "Vlr.Base IPI", "Aliq. IPI", "Vlr.IPI", "ICMS Solid.", "Desconto", "DT Digitacao"],
        [
            _sd1(1001, 1, "001", "1101", "000", "100", "12"),
            _sd1(1002, 1, "001", "1101", "000", "30", "3.6"),
            _sd1(1002, 2, "001", "1101", "000", "30", "3.6"),
            _sd1(1002, 3, "001", "1101", "000", "30", "3.6"),
            _sd1(1004, 1, "001", "1101", "000", "40", "4.8"),
            _sd1(1006, 1, "001", "1101", "000", "70", "8.4"),
            _sd1(1007, 1, "002", "1101", "090", "40", "0"),
            _sd1(2001, 1, "036", "1352", "000", "50", "6"),
            _sd1(1008, 1, "001", "1101", "000", "100", "12", code="C0051", store="02"),
            _sd1(1010, 1, "001", "1101", "000", "60", "7.2", code="C0051", store="02"),
            _sd1(1009, 1, "052", "1101", "000", "100", "12", ipi="5"),
            _sd1(1009, 2, "070", "1101", "000", "100", "12", ipi="5"),
        ],
    )
    _csv(
        root / "sf4.csv",
        ["Filial", "Cod. do Tipo", "Txt Padrao", "Calcula ICMS", "Cred. ICMS ?", "L.Fisc. ICMS", "Calcula IPI?", "Credita IPI?", "L.Fiscal IPI", "Mat.Consumo", "Tipo do TES", "Cod. Fiscal"],
        [
            ["01", "001", "Compra com credito", "Sim", "Sim", "Tributado", "Nao", "Nao", "Outros", "Nao", "Entrada", "101"],
            ["01", "002", "Compra sem credito", "Sim", "Nao", "Outros", "Nao", "Nao", "Outros", "Nao", "Entrada", "101"],
            ["01", "036", "Frete com credito", "Sim", "Sim", "Tributado", "Nao", "Nao", "Outros", "Nao", "Entrada", "352"],
            ["01", "052", "Material de consumo", "Sim", "Sim", "Tributado", "Sim", "Sim", "Tributado", "Sim", "Entrada", "551"],
            ["01", "070", "Material de consumo", "Sim", "Sim", "Tributado", "Sim", "Sim", "Tributado", "Sim", "Entrada", "551"],
        ],
    )
    return keys


def _sf1(number, species, access_key, gross, goods, icms, base, *, tipo="N", code="000001", store="01", state="SC", name="Fornecedor Sintetico", cnpj=SUPPLIER):
    return ["01", str(number), "1", code, store, state, name, cnpj, tipo, "N", species, access_key, "12/11/2026", "12/11/2026", "0", "0", base, icms, "0", "0", goods, gross, "0", "0", "0", "0"]


def _sd1(number, item, tes, cfop, cst, total, icms, *, code="000001", store="01", ipi="0"):
    rate = "12" if float(icms) else "0"
    base = total if float(icms) else "0"
    ipi_base = total if float(ipi) else "0"
    ipi_rate = "5" if float(ipi) else "0"
    return ["01", str(number), "1", code, store, cfop, cst, tes, str(item), f"P{item}", "1", total, total, base, rate, icms, ipi_base, ipi_rate, ipi, "0", "0", "12/11/2026"]


def _csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    lines = [";".join(header)] + [";".join(row) for row in rows]
    path.write_text("\n".join(lines), encoding="latin-1")


def _norm(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    text = str(value).strip()
    if "." in text:
        try:
            return f"{float(text):.2f}"
        except ValueError:
            return text
    return text


def _skill_signatures(root: Path) -> tuple[set[tuple], set[tuple], dict]:
    script = r"""
import sys
sys.path.insert(0, sys.argv[1])
from leitura import read_protheus, read_xmls
from regras import analisar, SF1_NUM, SD1_NUM
notas, ign, ctes = read_xmls([sys.argv[2]])
sf1 = read_protheus(sys.argv[3], SF1_NUM)
sd1 = read_protheus(sys.argv[4], SD1_NUM)
sf4 = read_protheus(sys.argv[5])
sa1 = read_protheus(sys.argv[7]) if sys.argv[7] != "-" else None
R = analisar(notas, sf1, sd1, sf4, filial="01", cnpj=sys.argv[6], uf="SC", ctes=ctes, sa1=sa1, tes_insumo=sys.argv[8])
for kind, rows in (("H", R["div"]), ("I", R["idiv"])):
    for row in rows:
        item = row.get("item", "")
        print("OCC", kind, row["nf"], item, row["tipo"], row["campo"], row["sev"], row["vp"], row["vx"], sep="\t")
for row in R["sox"]:
    print("UNM", "xml", row["n"]["numero"], row["sev"], sep="\t")
for row in R["sos"]:
    print("UNM", "protheus", row["r"]["Numero"], row["sev"], sep="\t")
for name, count in R["sup"].items():
    print("SUP", name, count, sep="\t")
"""
    completed = subprocess.run(
        [
            _skill_python(), "-c", script, str(SKILL.parent), str(root / "xml"),
            str(root / "sf1.csv"), str(root / "sd1.csv"), str(root / "sf4.csv"), COMPANY,
            str(root / "sa1.csv") if (root / "sa1.csv").exists() else "-", INPUT_TES_CODES,
        ],
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    occurrences, unmatched, suppressed = set(), set(), {}
    for line in completed.stdout.splitlines():
        parts = line.split("\t")
        if parts[0] == "OCC":
            _, _kind, number, item, title, field, severity, protheus_value, xml_value = parts
            occurrences.add((number, item, title, field, severity, _norm(protheus_value), _norm(xml_value)))
        elif parts[0] == "UNM":
            unmatched.add((parts[1], parts[2], parts[3]))
        elif parts[0] == "SUP":
            suppressed[parts[1]] = int(parts[2])
    return occurrences, unmatched, suppressed


def test_reader_sees_the_same_documents_the_skill_reads(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    invoices, ctes, ignored = read_xml_paths([tmp_path / "xml"])
    assert ignored == 0
    assert len(invoices) == 8
    assert len(ctes) == 1
    origin = next(doc for doc in invoices.values() if doc.number == 1002)
    assert [item.origin for item in origin.items] == ["1", "1", "1"]
    assert next(iter(ctes.values())).service_amount == 50


def test_constructed_parity_matches_the_skill(tmp_path: Path) -> None:
    _require_skill()
    keys = _write_fixture(tmp_path)
    skill_occ, skill_unm, skill_sup = _skill_signatures(tmp_path)
    invoices, ctes, _ignored = read_xml_paths([tmp_path / "xml"])
    customer = dict(
        supplier_code="C0051", supplier_store="02", supplier_name="", supplier_state="", supplier_tax_id="",
        invoice_type="B", participant_kind="customer", participant_name="Cliente Sintetico",
        participant_tax_id=THIRD, participant_state="SC",
    )
    headers = [
        _header(1001, keys["clean"], 100, 100, 12),
        _header(1002, keys["origin"], 90, 90, 10.8),
        _header(1004, keys["protheus_only"], 40, 40, 4.8),
        _header(1006, keys["total"], 90, 70, 8.4),
        _header(1007, keys["cst"], 40, 40, 0),
        _header(2001, keys["cte"], 50, 50, 6, species="CTE"),
        replace(_header(1008, keys["customer"], 100, 100, 12), **customer),
        replace(_header(1010, keys["customer_mismatch"], 60, 60, 7.2), **customer),
        replace(_header(1009, keys["input_tes"], 200, 200, 24), ipi_amount=10, ipi_base=200),
    ]
    items = [
        _item(1001, "1", 100, 12),
        *[_item(1002, str(n), 30, 3.6) for n in (1, 2, 3)],
        _item(1004, "1", 40, 4.8),
        _item(1006, "1", 70, 8.4),
        _item(1007, "1", 40, 0, cst="090", tes="002", rate=0),
        _item(2001, "1", 50, 6, cfop="1352", tes="036"),
        replace(_item(1008, "1", 100, 12), supplier_code="C0051", supplier_store="02"),
        replace(_item(1010, "1", 60, 7.2), supplier_code="C0051", supplier_store="02"),
        replace(_item(1009, "1", 100, 12, tes="052"), ipi_amount=5, ipi_base=100, ipi_rate=5),
        replace(_item(1009, "2", 100, 12, tes="070"), ipi_amount=5, ipi_base=100, ipi_rate=5),
    ]
    # The reader is the XML source. Rebuild is unnecessary when the files were just parsed.
    assert isinstance(next(iter(invoices.values())), XmlDocument)
    result = audit(
        branch="01", company_tax_id=COMPANY, company_state="SC", headers=headers, items=items,
        tes_records=TES + [INPUT_TES, CONSUMPTION_TES], invoices=invoices, ctes=ctes,
        config=AuditConfig(improvements_enabled=False, participant_by_type_enabled=True, input_tes=INPUT_TES_CODES),
    )
    engine_occ = {
        (row.document_number, row.item, row.title, row.field, row.severity, _norm(row.protheus_value), _norm(row.xml_value))
        for row in result.occurrences
    }
    engine_unm = {(row.side, row.document_number, row.severity) for row in result.unmatched}
    assert engine_occ == skill_occ
    assert engine_unm == skill_unm
    assert result.suppressed.get("suppressed.cst_090") == skill_sup.get("CST 090 em TES sem crédito (padrão da empresa)")
    assert "header.total_mismatch" in {row.rule_id for row in result.occurrences}
    assert shutil.which(_skill_python())
