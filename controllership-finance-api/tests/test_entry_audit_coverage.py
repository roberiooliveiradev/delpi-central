"""Cada rule_id tem caso no corpus, teste negativo e paridade com a skill."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from controllership_finance_app.domain.entry_audit.engine import audit
from controllership_finance_app.domain.entry_audit.models import AuditConfig
from tests.entry_audit_corpus import (
    COMPANY,
    TES,
    book_lines,
    book_specs,
    header_only_spec,
    main_specs,
    write_corpus,
)
from tests.test_entry_audit_parity import _require_skill, _skill_python

SKILL = (
    Path(__file__).resolve().parents[2]
    / "docs/12-roadmap-e-evolucao/controllership-finance/entry-audit/reference/skill-auditoria-entradas-nfe-protheus/scripts"
)

RULES = {
    "header.icms_above_xml", "header.icms_not_credited", "header.icms_credit_short", "header.icms_base_mismatch",
    "header.ipi_not_booked", "header.series_mismatch", "header.total_mismatch", "header.accessory_field",
    "header.issue_date_mismatch", "item.amount_mismatch", "item.cfop_direction_swapped", "item.inbound_booked_as_purchase",
    "item.cfop_differs_from_issued", "item.cfop_nature_mismatch", "item.fuel_cfop", "item.st_on_non_st_cfop",
    "item.st_cfop_without_st", "item.origin_mismatch", "item.cst_mismatch", "item.icms_above_xml",
    "item.simples_credit_not_taken", "item.highlighted_icms_not_credited", "item.ipi_without_tes_decision",
    "item.ipi_credit_mismatch", "item.ipi_base_mismatch", "item.st_mismatch", "item.rate_or_base_mismatch",
    "item.unusual_cfop_nature", "coherence.cfop_vs_state", "coherence.ipi_on_consumption",
    "coherence.icms_on_consumption_cfop", "coherence.icms_on_untaxed_cst", "simples.rate_above_cap",
    "simples.near_sublimite", "simples.csosn_without_rate", "simples.presumed_wrong_tes",
    "simples.presumed_above_sublimite", "simples.presumed_rate_mismatch", "simples.presumed_without_right",
    "unmatched.xml_only", "unmatched.protheus_only", "fiscal_book.item_missing", "fiscal_book.credit_against_tes",
    "fiscal_book.credit_missing", "fiscal_book.amount_mismatch", "cte.service_amount_mismatch", "cte.cfop_mismatch",
    "cte.credit_without_right", "cte.icms_not_credited", "cte.credit_mismatch", "cte.rate_or_base_mismatch",
    "cte.cst_mismatch", "cte.icms_inconclusive", "cte.booked_not_taker", "key.diverges_from_xml", "key.missing",
    "key.invalid", "key.number_mismatch", "key.series_mismatch", "key.species_mismatch", "key.supplier_mismatch",
    "suppressed.icms_without_credit", "suppressed.base_or_rate_without_credit", "suppressed.ipi_without_credit",
    "suppressed.cst_090", "suppressed.cst_060", "suppressed.header_icms_not_credited", "excluded.items",
}


def test_every_rule_has_a_positive_case_and_matches_the_skill(tmp_path: Path) -> None:
    _require_skill()
    seen = set()
    for name, specs, items, book in (
        ("main", main_specs(), True, False),
        ("header", header_only_spec(), False, False),
        ("book", book_specs(), True, True),
    ):
        folder = tmp_path / name
        headers, item_rows, invoices, ctes = write_corpus(folder, specs, with_items=items, with_book=book)
        skill = _skill(folder, with_items=items, with_book=book)
        result = audit(
            branch="01", company_tax_id=COMPANY, company_state="SC", headers=headers, items=item_rows,
            tes_records=TES, invoices=invoices, ctes=ctes, config=AuditConfig(),
            fiscal_book=book_lines() if book else None,
        )
        engine = _engine_signature(result)
        assert engine["occ"] == skill["occ"], _diff(name, engine["occ"], skill["occ"])
        assert engine["unm"] == skill["unm"], _diff(name, engine["unm"], skill["unm"])
        assert engine["sup"] == skill["sup"], (name, engine["sup"], skill["sup"])
        assert engine["exc"] == skill["exc"], (name, engine["exc"], skill["exc"])
        seen.update(row.rule_id for row in result.occurrences)
        seen.update(result.suppressed)
        if result.excluded:
            seen.add("excluded.items")
        if any(row.side == "xml" for row in result.unmatched):
            seen.add("unmatched.xml_only")
        if any(row.side == "protheus" for row in result.unmatched):
            seen.add("unmatched.protheus_only")
    missing = RULES - seen
    assert not missing, sorted(missing)


@pytest.mark.parametrize("rule_id", sorted(RULES))
def test_matching_note_does_not_fire_the_rule(rule_id: str) -> None:
    from tests.test_entry_audit_engine import _header, _invoice, _item, _key, _run, _xml_item

    key = _key("55", 1001)
    result = _run(
        [_header(1001, key, 100, 100, 12)],
        [_item(1001, "1", 100, 12)],
        {key: _invoice(1001, key, (_xml_item(1, 100, 12),), 100, 12)},
    )
    assert rule_id not in {row.rule_id for row in result.occurrences}
    assert rule_id not in result.suppressed
    assert result.unmatched == []
    assert result.excluded == []


def _engine_signature(result) -> dict:
    return {
        "occ": {
            (row.document_number, row.item, row.title, row.field, row.severity, row.protheus_value, row.xml_value)
            for row in result.occurrences
        },
        "unm": {(row.side, row.document_number, row.severity, row.reason) for row in result.unmatched},
        "sup": dict(result.not_reported),
        "exc": {(row.kind, row.document_number, row.item_count) for row in result.excluded},
    }


def _skill(folder: Path, *, with_items: bool, with_book: bool) -> dict:
    script = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from leitura import read_protheus, read_xmls
from regras import analisar, SF1_NUM, SD1_NUM
notas, ign, ctes = read_xmls([sys.argv[2]])
sf1 = read_protheus(sys.argv[3], SF1_NUM)
sd1 = read_protheus(sys.argv[4], SD1_NUM) if sys.argv[4] else None
sf4 = read_protheus(sys.argv[5])
sft = read_protheus(sys.argv[6]) if sys.argv[6] else None
R = analisar(notas, sf1, sd1, sf4, filial='01', cnpj=sys.argv[7], uf='SC', sft=sft, ctes=ctes)
out = []
for row in R['div']:
    out.append({'k':'o','n':str(row['nf']),'i':'','t':row['tipo'],'f':row['campo'],'s':row['sev'],'p':row['vp'],'x':row['vx']})
for row in R['idiv']:
    out.append({'k':'o','n':str(row['nf']),'i':str(row['item']),'t':row['tipo'],'f':row['campo'],'s':row['sev'],'p':row['vp'],'x':row['vx']})
for row in R['sox']:
    out.append({'k':'u','side':'xml','n':str(row['n']['numero']),'s':row['sev'],'r':row['mot']})
for row in R['sos']:
    out.append({'k':'u','side':'protheus','n':str(row['r']['Numero']),'s':row['sev'],'r':row['mot']})
for name, count in R['sup'].items():
    out.append({'k':'s','n':name,'c':int(count)})
exg = R['exg']
if exg is not None:
    for _, row in exg.iterrows():
        out.append({'k':'e','t':row['tipo'],'n':str(row['Documento']),'c':int(row['itens'])})
print(json.dumps(out, ensure_ascii=False, default=str))
"""
    sd1 = str(folder / "sd1.csv") if with_items else ""
    sft = str(folder / "sft.csv") if with_book else ""
    completed = subprocess.run(
        [_skill_python(), "-c", script, str(SKILL), str(folder / "xml"), str(folder / "sf1.csv"), sd1, str(folder / "sf4.csv"), sft, COMPANY],
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    occ, unm, sup, exc = set(), set(), {}, set()
    for row in payload:
        if row["k"] == "o":
            _rule(row["t"])
            occ.add((row["n"], row["i"], row["t"], row["f"], row["s"], _norm(row["p"]), _norm(row["x"])))
        elif row["k"] == "u":
            unm.add((row["side"], row["n"], row["s"], row["r"]))
        elif row["k"] == "s":
            sup[row["n"]] = row["c"]
        else:
            exc.add((row["t"], row["n"], row["c"]))
    return {"occ": occ, "unm": unm, "sup": sup, "exc": exc}


def _rule(title: str) -> str:
    table = {
        "ICMS calculado sem destaque no XML": "header.icms_above_xml",
        "Crédito de ICMS sem destaque no XML": "header.icms_above_xml",
        "ICMS calculado acima do XML": "header.icms_above_xml",
        "Crédito de ICMS acima do XML": "header.icms_above_xml",
        "ICMS do XML não creditado": "header.icms_not_credited",
        "Crédito de ICMS a menor": "header.icms_credit_short",
        "Base de ICMS divergente": "header.icms_base_mismatch",
        "Base de ICMS divergente (ICMS confere)": "header.icms_base_mismatch",
        "IPI destacado no XML não escriturado": "header.ipi_not_booked",
        "IPI escriturado sem destaque no XML": "header.ipi_not_booked",
        "Série divergente do XML": "header.series_mismatch",
        "Valor total da nota diverge": "header.total_mismatch",
        "Valor das mercadorias diverge": "header.total_mismatch",
        "ICMS ST diverge": "header.total_mismatch",
        "Desconto classificado diferente": "header.accessory_field",
        "Acessório lançado em campo diferente (total confere)": "header.accessory_field",
        "Data de emissão divergente": "header.issue_date_mismatch",
        "Valor do item diverge": "item.amount_mismatch",
        "CFOP com origem trocada (interna × interestadual)": "item.cfop_direction_swapped",
        "NF de entrada do fornecedor lançada como compra": "item.inbound_booked_as_purchase",
        "CFOP diferente do documento emitido": "item.cfop_differs_from_issued",
        "Natureza do CFOP incompatível com o documento": "item.cfop_nature_mismatch",
        "Combustível fora do CFOP x653": "item.fuel_cfop",
        "Item com ST no XML lançado em CFOP sem ST": "item.st_on_non_st_cfop",
        "CFOP de ST sem ST no XML": "item.st_cfop_without_st",
        "Origem da mercadoria divergente": "item.origin_mismatch",
        "CST diverge do documento": "item.cst_mismatch",
        "ICMS do XML não creditado em insumo/revenda": "item.highlighted_icms_not_credited",
        "Crédito do Simples não aproveitado (TES sem crédito)": "item.simples_credit_not_taken",
        "ICMS destacado não creditado em insumo/revenda (TES sem crédito)": "item.highlighted_icms_not_credited",
        "IPI do XML não escriturado": "item.ipi_without_tes_decision",
        "Crédito de IPI abaixo do XML": "item.ipi_credit_mismatch",
        "Crédito de IPI acima do XML": "item.ipi_credit_mismatch",
        "Base de IPI divergente": "item.ipi_base_mismatch",
        "ICMS ST divergente": "item.st_mismatch",
        "Alíquota de ICMS divergente (valor confere)": "item.rate_or_base_mismatch",
        "Produto lançado com natureza de CFOP diferente do usual": "item.unusual_cfop_nature",
        "CFOP de entrada incompatível com a UF do fornecedor": "coherence.cfop_vs_state",
        "Crédito de IPI em material de uso e consumo": "coherence.ipi_on_consumption",
        "ICMS calculado em CFOP de uso e consumo": "coherence.icms_on_consumption_cfop",
        "Crédito de ICMS em CFOP de uso e consumo": "coherence.icms_on_consumption_cfop",
        "ICMS calculado com CST sem tributação": "coherence.icms_on_untaxed_cst",
        "Crédito de ICMS com CST sem tributação": "coherence.icms_on_untaxed_cst",
        "Alíquota de crédito SN acima do teto do Simples": "simples.rate_above_cap",
        "Fornecedor do Simples perto do sublimite": "simples.near_sublimite",
        "CSOSN com permissão de crédito sem alíquota informada": "simples.csosn_without_rate",
        "Indústria do Simples (SC) fora da TES de crédito presumido": "simples.presumed_wrong_tes",
        "Crédito presumido com fornecedor acima do sublimite": "simples.presumed_above_sublimite",
        "Valor no item diferente do crédito presumido de 7%": "simples.presumed_rate_mismatch",
        "TES de crédito presumido em nota sem direito": "simples.presumed_without_right",
        "Item sem registro no livro fiscal (SFT)": "fiscal_book.item_missing",
        "Crédito no livro fiscal em TES que não credita": "fiscal_book.credit_against_tes",
        "Crédito previsto na TES fora do livro fiscal": "fiscal_book.credit_missing",
        "ICMS do livro fiscal diferente do item": "fiscal_book.amount_mismatch",
        "CT-e: valor da prestação diverge": "cte.service_amount_mismatch",
        "CT-e: CFOP divergente": "cte.cfop_mismatch",
        "CT-e: crédito de ICMS em frete sem direito": "cte.credit_without_right",
        "CT-e: ICMS do frete não creditado": "cte.icms_not_credited",
        "CT-e: crédito de ICMS acima do XML": "cte.credit_mismatch",
        "CT-e: crédito de ICMS abaixo do XML": "cte.credit_mismatch",
        "CT-e: alíquota de ICMS divergente": "cte.rate_or_base_mismatch",
        "CT-e: base de ICMS divergente": "cte.rate_or_base_mismatch",
        "CT-e: CST divergente": "cte.cst_mismatch",
        "CT-e: ICMS calculado em frete sem direito": "cte.icms_inconclusive",
        "CT-e: ICMS calculado diferente do XML": "cte.icms_inconclusive",
        "CT-e escriturado sem a empresa ser a tomadora": "cte.booked_not_taker",
        "Chave de acesso divergente do XML": "key.diverges_from_xml",
        "Documento eletrônico sem chave de acesso": "key.missing",
        "Chave de acesso inválida": "key.invalid",
        "Chave de acesso não confere com o número do documento": "key.number_mismatch",
        "Série divergente da chave de acesso": "key.series_mismatch",
        "Espécie do documento incompatível com a chave": "key.species_mismatch",
        "Fornecedor do lançamento com CNPJ diferente do emitente": "key.supplier_mismatch",
    }
    if title not in table:
        raise AssertionError(f"título sem rule_id: {title}")
    return table[title]


def _norm(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    text = str(value).strip()
    if text in {"", "(vazia)"}:
        return text
    try:
        if "." in text:
            return f"{float(text):.2f}"
    except ValueError:
        return text
    return text


def _diff(name: str, engine: set, skill: set) -> str:
    missing = sorted(skill - engine)[:12]
    extra = sorted(engine - skill)[:12]
    return f"{name} missing={missing} extra={extra}"
