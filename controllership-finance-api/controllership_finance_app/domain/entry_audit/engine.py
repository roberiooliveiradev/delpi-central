"""Motor das regras da skill, em Python puro.

D11 não altera estas regras: a folga de XML e o status do LNF ficam na orquestração.
O texto de cada ocorrência é o da skill (leitura curta e orientação).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta

from controllership_finance_app.domain.entry_audit.catalog import (
    ANNEX,
    CFOP_GROUPS,
    CONSUMPTION_OR_ASSET,
    CRT_NAME,
    ELECTRONIC_SPECIES,
    EXCLUDED_BY_SPECIES,
    EXCLUDED_BY_SUFFIX,
    FUEL_NCM,
    FUEL_SUFFIXES,
    INDUSTRY_SUFFIXES,
    LABEL_CST_060,
    LABEL_CST_090,
    LABEL_HEADER_BASE,
    LABEL_ICMS_WITHOUT_CREDIT,
    LABEL_IPI_TOTAL_OK,
    LABEL_IPI_WITHOUT_CREDIT,
    LABEL_RATE_OR_BASE,
    MODEL_SPECIES,
    NATURE,
    OTHER_EXCLUDED,
    PRESUMED,
    SEVERITY_ORDER,
    ST_CSOSN,
    ST_CST,
    SUBLIMIT,
    SUBLIMIT_ALERT,
    SUPPLY_SUFFIXES,
    TAKER_ROLE,
    WHY,
)
from controllership_finance_app.domain.entry_audit.models import (
    AuditConfig,
    AuditResult,
    ExcludedItem,
    FiscalBookLine,
    Occurrence,
    ProtheusHeader,
    ProtheusItem,
    TesRecord,
    UnmatchedDocument,
    XmlDocument,
    XmlItem,
)


def audit(
    *,
    branch: str,
    company_tax_id: str,
    company_state: str,
    headers: list[ProtheusHeader],
    items: list[ProtheusItem],
    tes_records: list[TesRecord],
    invoices: dict[str, XmlDocument],
    ctes: dict[str, XmlDocument],
    config: AuditConfig | None = None,
    fiscal_book: list[FiscalBookLine] | None = None,
) -> AuditResult:
    settings = config or AuditConfig()
    result = AuditResult()
    tes = {record.code: record for record in tes_records}
    company_tax_id = _digits(company_tax_id)
    presumed_tes = settings.presumed_credit_tes or PRESUMED["tes"]
    presumed_on = company_state == PRESUMED["state"]
    documents = {**invoices, **ctes}
    rows = [_view(header) for header in headers if header.branch == branch]
    _correct_keys(rows, documents, company_tax_id, settings.tolerance, result)
    for row in rows:
        row["danfe"] = len(row["access_key"]) == 44 and row["access_key"][20:22] == "55"
        row["cte"] = len(row["access_key"]) == 44 and row["access_key"][20:22] in {"57", "67"}
    invoices_only = [row for row in rows if row["danfe"]]
    book = _Book(fiscal_book, branch)
    item_rows = _items(items, rows, branch)
    tes_by_document = _tes_by_document(item_rows)
    header_hits: list[dict] = []
    item_hits: list[dict] = []
    boosted: set[tuple[str, str]] = set()

    _headers(
        result, invoices_only, invoices, item_rows, tes, book, tes_by_document,
        company_state, presumed_tes, presumed_on, settings, header_hits,
    )
    _ctes(
        result, rows, ctes, item_rows, tes, book, tes_by_document, company_tax_id,
        company_state, settings, header_hits,
    )
    _keys(result, rows, documents, company_tax_id, header_hits)
    _supplier_keys(result, rows, documents, company_tax_id, header_hits)
    _unmatched(result, rows, invoices_only, invoices, ctes, company_tax_id, settings)
    _items_rules(
        result, item_rows, invoices, tes, book, company_state, presumed_tes, presumed_on,
        settings, item_hits, boosted,
    )
    header_hits.sort(key=lambda hit: (SEVERITY_ORDER[hit["severity"]], hit["title"], hit["supplier"], hit["number"]))
    item_hits.sort(key=lambda hit: (SEVERITY_ORDER[hit["severity"]], hit["title"], hit["supplier"], hit["number"], hit["item"]))
    for hit in header_hits + item_hits:
        result.occurrences.append(_occurrence(hit))
    result.summary["protheus_documents"] = len(rows)
    result.summary["protheus_invoices"] = len(invoices_only)
    result.summary["xml_invoices"] = len(invoices)
    result.summary["matched_invoices"] = sum(1 for row in invoices_only if row["access_key"] in invoices)
    result.summary["protheus_ctes"] = sum(1 for row in rows if row["cte"])
    result.summary["xml_ctes"] = len(ctes)
    result.summary["matched_ctes"] = sum(1 for row in rows if row["cte"] and row["access_key"] in ctes)
    result.summary["keys_corrected"] = sum(1 for row in rows if row["fixed"])
    return result


def _headers(result, rows, invoices, item_rows, tes, book, tes_by_document, company_state, presumed_tes, presumed_on, settings, hits) -> None:
    del presumed_tes, company_state
    for row in sorted((row for row in rows if row["access_key"] in invoices), key=lambda item: (item["name"], item["number"])):
        document = invoices[row["access_key"]]
        if document.cancelled:
            continue
        before = len(hits)
        simple = document.crt in {"1", "4"}
        reference = _simple_credit(document) if simple else document.icms_amount
        booked = row["icms"]
        amounts_match = abs(booked - reference) <= settings.tolerance
        if simple:
            _simple_header(result, row, document, hits)
        if any(_eligible(presumed_on, document.issuer_state, document.crt, item.cfop) for item in document.items):
            amounts_match = True
            reference = booked
        if not amounts_match:
            _header_icms(result, row, document, booked, reference, simple, item_rows, tes, book, tes_by_document, hits)
        if not simple and not any(_eligible(presumed_on, document.issuer_state, document.crt, item.cfop) for item in document.items):
            _header_base(result, row, document, booked, amounts_match, before, hits, tes, book, tes_by_document, settings)
        xml_ipi = _ipi_from_items(document) or document.ipi_amount
        gross_gap = round(row["gross"] - document.total_amount, 2)
        _header_ipi(result, row, document, xml_ipi, gross_gap, hits, settings)
        if abs(gross_gap) > settings.tolerance:
            _hit(hits, row, document, "header.total_mismatch", "Valor total da nota diverge", "Alta", "Vlr Total", row["gross"], document.total_amount, "Total escriturado diferente do vNF: afeta contas a pagar e SPED.")
        if abs(row["goods"] - document.goods_amount) > settings.tolerance:
            _hit(hits, row, document, "header.total_mismatch", "Valor das mercadorias diverge", "Alta", "Vlr Mercadorias", row["goods"], document.goods_amount, "Quantidade/preço digitado diferente do XML.")
        if abs(row["st"] - document.st_amount) > settings.tolerance:
            _hit(hits, row, document, "header.total_mismatch", "ICMS ST diverge", "Alta", "ICMS ST", row["st"], document.st_amount, "Conferir ST na TES.")
        if abs(row["discount"] - document.discount_amount) > settings.tolerance and abs(gross_gap) <= settings.tolerance:
            _hit(hits, row, document, "header.accessory_field", "Desconto classificado diferente", "Baixa", "Desconto", row["discount"], document.discount_amount, "Total confere.")
        _header_accessories(row, document, xml_ipi, gross_gap, hits, settings)
        if _series(row["series"]) != _series(document.series):
            _hit(hits, row, document, "header.series_mismatch", "Série divergente do XML", "Média", "Série", row["series"], document.series, "Série digitada diferente da do documento: corrigir (o SPED leva a série do lançamento).")
        _dates(row, document, hits, "Data digitada diferente da do XML: corrigir.")


def _header_icms(result, row, document, booked, reference, simple, item_rows, tes, book, tes_by_document, hits) -> None:
    if booked > 0 and reference == 0:
        _depend(result, hits, row, document, "", "header.icms_above_xml", "ICMS calculado sem destaque no XML", "ICMS", booked, reference, ("Fornecedor do Simples sem crédito SN no XML. " if simple else f'XML sem ICMS destacado (CST {_cst_list(document)}). '), tes, book, tes_by_document)
    elif booked > reference:
        _depend(result, hits, row, document, "", "header.icms_above_xml", "ICMS calculado acima do XML", "ICMS", booked, reference, (f"Simples: o crédito permitido é só o vCredICMSSN ({_brl(reference)})." if simple else "Alíquota ou base no Protheus maior que no XML."), tes, book, tes_by_document)
    elif booked == 0 and not item_rows and not _note_consumption(row, tes, tes_by_document):
        _hit(hits, row, document, "header.icms_not_credited", "ICMS do XML não creditado", "Média", "ICMS", booked, reference, f'ICMS destacado e zerado no Protheus em nota que não é só de consumo/ativo (TES {tes_by_document.get(row["k"], "")}). Se for insumo ou revenda, é crédito perdido.')
    elif booked == 0 and item_rows:
        result.suppress("suppressed.header_icms_not_credited")
    elif booked > 0 and _note_credit(row, tes, book, tes_by_document) is False:
        result.suppress("suppressed.icms_without_credit", LABEL_ICMS_WITHOUT_CREDIT)
    elif booked > 0:
        _hit(hits, row, document, "header.icms_credit_short", "Crédito de ICMS a menor", "Média", "ICMS", booked, reference, "ICMS no Protheus menor que o do XML: conferir alíquota/redução na TES.")


def _header_base(result, row, document, booked, amounts_match, before, hits, tes, book, tes_by_document, settings) -> None:
    if abs(round(row["icms_base"] - document.icms_base, 2)) <= settings.tolerance:
        return
    if not amounts_match and len(hits) > before:
        _hit(hits, row, document, "header.icms_base_mismatch", "Base de ICMS divergente", hits[-1]["severity"], "Base ICMS", row["icms_base"], document.icms_base, "Acompanha a divergência de ICMS acima.")
    elif amounts_match and (booked <= settings.tolerance or _note_credit(row, tes, book, tes_by_document) is False):
        result.suppress("suppressed.base_or_rate_without_credit", LABEL_HEADER_BASE)
    elif amounts_match:
        _hit(hits, row, document, "header.icms_base_mismatch", "Base de ICMS divergente (ICMS confere)", "Média", "Base ICMS", row["icms_base"], document.icms_base, "ICMS igual ao XML, mas a base escriturada difere (ex.: IPI na base). Vai assim para o C100/C190 do SPED: corrigir a base no documento.")


def _header_ipi(result, row, document, xml_ipi, gross_gap, hits, settings) -> None:
    if abs(row["ipi"] - xml_ipi) <= settings.tolerance:
        return
    if abs(gross_gap) <= settings.tolerance:
        result.suppress("suppressed.ipi_without_credit", LABEL_IPI_TOTAL_OK)
    elif row["ipi"] < xml_ipi:
        _hit(hits, row, document, "header.ipi_not_booked", "IPI destacado no XML não escriturado", "Alta", "IPI", row["ipi"], xml_ipi, "TES sem cálculo de IPI: total e título a pagar menores que o documento. Corrigir a TES e relançar.")
    else:
        _hit(hits, row, document, "header.ipi_not_booked", "IPI escriturado sem destaque no XML", "Alta", "IPI", row["ipi"], xml_ipi, "Protheus calcula IPI que o documento não traz.")


def _header_accessories(row, document, xml_ipi, gross_gap, hits, settings) -> None:
    pairs = (("freight", document.freight_amount, "Frete"), ("expense", document.other_amount, "Outras despesas"))
    for field, xml_value, label in pairs:
        ipi_moved = abs(row["ipi"] - xml_ipi) > settings.tolerance and abs((row[field] + row["ipi"]) - (xml_value + xml_ipi)) <= settings.tolerance
        if abs(row[field] - xml_value) > settings.tolerance and abs(gross_gap) <= settings.tolerance and not (label == "Outras despesas" and ipi_moved):
            action = (
                "Nota de importação: vOutro do XML soma II/PIS/COFINS/despesas aduaneiras. Total confere."
                if row["state"] == "EX"
                else "Frete lançado como despesa (ou o inverso). Sem impacto no total; afeta rateio de custo e SPED."
            )
            _hit(hits, row, document, "header.accessory_field", "Acessório lançado em campo diferente (total confere)", "Baixa", label, row[field], xml_value, action)


def _simple_header(result, row, document, hits) -> None:
    del result
    rates = [item.simple_rate for item in document.items]
    highest = max(rates, default=0)
    annex = "II" if any(item.cfop[1:] in INDUSTRY_SUFFIXES for item in document.items if len(item.cfop) > 1) else "I"
    if highest > 0:
        cap, revenue = _simple_band(highest, annex)
        if revenue is None:
            _hit(hits, row, document, "simples.rate_above_cap", "Alíquota de crédito SN acima do teto do Simples", "Média", "pCredSN (%)", highest, round(cap, 2), f"Pela tabela do Anexo {annex}, o maior percentual de ICMS possível dentro do sublimite (RBT12 de R$ 3,6 mi) é {cap:.2f}%. {highest:g}% só se explica se o fornecedor ultrapassou o sublimite (aí o ICMS sai do DAS e é pago por fora, sem crédito SN) ou se calculou errado. Consultar a situação do fornecedor e pedir correção; em SC, acima do sublimite também não há crédito presumido de 7%.")
        elif revenue >= SUBLIMIT_ALERT:
            _hit(hits, row, document, "simples.near_sublimite", "Fornecedor do Simples perto do sublimite", "Baixa", "pCredSN (%)", highest, round(cap, 2), f"{highest:g}% corresponde a um faturamento (RBT12) estimado de R$ {revenue / 1e6:.2f} mi no Anexo {annex}, perto do sublimite de R$ 3,6 mi. Acompanhar: ao ultrapassar, o crédito SN (e, em SC, o presumido de 7%) deixa de valer.")
    if any(item.csosn in {"101", "201"} and item.simple_rate == 0 for item in document.items):
        _hit(hits, row, document, "simples.csosn_without_rate", "CSOSN com permissão de crédito sem alíquota informada", "Baixa", "pCredSN (%)", 0.0, 0.0, "O item vem com CSOSN 101/201, mas sem pCredSN/vCredICMSSN. Sem a alíquota no documento não há crédito do art. 23 (LC 123, art. 23, § 4º, II). Pedir carta de correção ou nota complementar ao fornecedor.")


def _ctes(result, rows, ctes, item_rows, tes, book, tes_by_document, company_tax_id, company_state, settings, hits) -> None:
    nature_by_key: dict[str, set[str]] = defaultdict(set)
    for item in item_rows:
        if item["access_key"]:
            nature_by_key[item["access_key"]].add(_nature(item["cfop"]))
    freight_codes = sorted(
        code for code, record in tes.items()
        if record.tes_type == "Entrada" and record.fiscal_code[1:] == settings.freight_cfop_suffix
    )
    with_credit = [code for code in freight_codes if _credits_icms(tes.get(code)) is True]
    without_credit = [code for code in freight_codes if _credits_icms(tes.get(code)) is False]
    root = company_tax_id[:8]
    for row in sorted((row for row in rows if row["cte"] and row["access_key"] in ctes), key=lambda item: (item["name"], item["number"])):
        document = ctes[row["access_key"]]
        lines = [item for item in item_rows if item["k"] == row["k"]]
        if lines:
            base = sum(item["icms_base"] for item in lines)
            icms = sum(item["icms"] for item in lines)
            rate = max(item["icms_rate"] for item in lines)
            cfops = {item["cfop"] for item in lines if item["cfop"]}
            csts = {item["cst"] for item in lines if item["cst"]}
            codes = sorted({item["tes"] for item in lines if item["tes"]})
        else:
            base, icms, rate, cfops, csts, codes = row["icms_base"], row["icms"], None, set(), set(), []
        credit, credited = _cte_credit(row, lines, icms, tes, book)
        allowed, reason = _freight_right(document, company_tax_id, root, nature_by_key, settings)
        expected_cst = "0" + document.cst.zfill(2) if document.cst else ""
        tes_list = ", ".join(codes)
        if abs(row["gross"] - document.service_amount) > settings.tolerance:
            _hit(hits, row, document, "cte.service_amount_mismatch", "CT-e: valor da prestação diverge", "Alta", "Vlr Total", row["gross"], document.service_amount, "Valor escriturado diferente do vTPrest do CT-e: afeta contas a pagar e o D100 do SPED.")
        if _series(row["series"]) != _series(document.series):
            _hit(hits, row, document, "header.series_mismatch", "Série divergente do XML", "Média", "Série", row["series"], document.series, "Série digitada diferente da do CT-e: corrigir.")
        _dates(row, document, hits, "Data digitada diferente da do CT-e: corrigir.")
        if document.taker_tax_id and document.taker_tax_id != company_tax_id:
            _hit(hits, row, document, "cte.booked_not_taker", "CT-e escriturado sem a empresa ser a tomadora", "Média", "Tomador", _cnpj(company_tax_id), _cnpj(document.taker_tax_id), f"No CT-e o tomador (quem paga o frete) é o {document.taker_role or 'outro'}, CNPJ {_cnpj(document.taker_tax_id)}. Só o tomador escritura o CT-e e toma o crédito: conferir se o lançamento é desta filial.")
        prefix = "3" if document.origin_state == "EX" else ("1" if document.origin_state == company_state else "2")
        expected = prefix + settings.freight_cfop_suffix
        if cfops and document.model == "57" and any(code != expected for code in cfops):
            _hit(hits, row, document, "cte.cfop_mismatch", "CT-e: CFOP divergente", "Média", "CFOP", ", ".join(sorted(cfops)), expected, f"Transporte de {document.origin_state} para {document.destination_state} (CFOP do CT-e {document.cfop}), empresa em {company_state}. Aquisição de serviço de transporte por estabelecimento industrial: {expected} (1 quando a prestação começa na UF da empresa, 2 quando começa em outra UF).")
        detail = f' Base R$ {_brl(document.icms_base)}, alíquota {document.icms_rate:g}%, ICMS R$ {_brl(document.icms_amount)}, CST {expected_cst}.'
        if credit is True and allowed is False:
            extra = f' numa TES de frete sem crédito ({", ".join(without_credit)})' if without_credit else ""
            _hit(hits, row, document, "cte.credit_without_right", "CT-e: crédito de ICMS em frete sem direito", "Alta", "ICMS", credited, 0.0, f"{reason}. TES {tes_list} credita ICMS: crédito indevido. Zerar base, alíquota e ICMS e lançar com CST 090{extra}.")
        elif credit is False and allowed is True:
            option = f' TES de frete com crédito: {", ".join(with_credit)}.' if with_credit else ""
            _hit(hits, row, document, "cte.icms_not_credited", "CT-e: ICMS do frete não creditado", "Média", "ICMS", 0.0, document.icms_amount, f"{reason}: dá direito a crédito, mas a TES {tes_list or 'usada'} não credita. Lançar com os valores do CT-e:{detail}{option}")
        elif credit is True:
            if abs(credited - document.icms_amount) > settings.tolerance:
                if credited > document.icms_amount:
                    _hit(hits, row, document, "cte.credit_mismatch", "CT-e: crédito de ICMS acima do XML", "Alta", "ICMS", credited, document.icms_amount, "Crédito maior que o ICMS do CT-e: estornar o excedente. Valores do CT-e:" + detail)
                else:
                    _hit(hits, row, document, "cte.credit_mismatch", "CT-e: crédito de ICMS abaixo do XML", "Média", "ICMS", credited, document.icms_amount, "Crédito menor que o ICMS do CT-e. Valores do CT-e:" + detail)
            if rate is not None and abs(rate - document.icms_rate) > 0.01:
                _hit(hits, row, document, "cte.rate_or_base_mismatch", "CT-e: alíquota de ICMS divergente", "Média", "Alíq. ICMS", rate, document.icms_rate, f'Alíquota do CT-e: {document.icms_rate:g}% (prestação {document.origin_state}→{document.destination_state}). Corrigir no lançamento.')
            if abs(base - document.icms_base) > settings.tolerance:
                _hit(hits, row, document, "cte.rate_or_base_mismatch", "CT-e: base de ICMS divergente", "Média", "Base ICMS", base, document.icms_base, "Base escriturada diferente da do CT-e: corrigir (vai para o D100/D190).")
            if csts and expected_cst and any(code != expected_cst for code in csts):
                _hit(hits, row, document, "cte.cst_mismatch", "CT-e: CST divergente", "Média", "CST", ", ".join(sorted(csts)), expected_cst, f"Com crédito, o CST é o do CT-e ({expected_cst}).")
        elif credit is None and icms > settings.tolerance and allowed is False:
            _depend(result, hits, row, document, "", "cte.icms_inconclusive", "CT-e: ICMS calculado em frete sem direito", "ICMS", icms, 0.0, f"{reason}. Só é crédito indevido se a TES {tes_list} creditar.", tes, book, tes_by_document, item_scope=False)
        elif credit is None and allowed is True and abs(icms - document.icms_amount) > settings.tolerance:
            _depend(result, hits, row, document, "", "cte.icms_inconclusive", "CT-e: ICMS calculado diferente do XML", "ICMS", icms, document.icms_amount, f"{reason}. Valores do CT-e:{detail}", tes, book, tes_by_document, item_scope=False)
        if credit is False and allowed is not True and csts and any(code[-2:] != "90" for code in csts):
            _hit(hits, row, document, "cte.cst_mismatch", "CT-e: CST divergente", "Média", "CST", ", ".join(sorted(csts)), "090", "Frete sem crédito de ICMS: CST 090 e base, alíquota e ICMS zerados.")


def _keys(result, rows, documents, company_tax_id, hits) -> None:
    del result, company_tax_id
    for row in rows:
        key = row["access_key"]
        species = row["species"]
        document = documents.get(key)
        if row["fixed"]:
            action = (
                f"Documento lançado sem chave. O XML de mesmo número ({document.number}) e valor (R$ {_brl(document.total_amount)}) de {document.issuer_name} traz a chave ao lado: informá-la no documento de entrada. Sem a chave, o SPED não identifica o documento. O cruzamento seguiu pela chave do XML."
                if not row["original_key"]
                else f"O XML de mesmo número ({document.number}) e valor (R$ {_brl(document.total_amount)}) de {document.issuer_name} tem outra chave. Corrigir a chave no documento de entrada: com a chave errada o SPED informa um documento que não existe na SEFAZ. O cruzamento seguiu pela chave do XML."
            )
            _hit(hits, row, document, "key.diverges_from_xml", "Chave de acesso divergente do XML", "Alta", "Chave", row["original_key"] or "(vazia)", key, action)
            continue
        if not key:
            if species in ELECTRONIC_SPECIES:
                _hit(hits, row, document, "key.missing", "Documento eletrônico sem chave de acesso", "Alta", "Chave", "(vazia)", "", f"Espécie {species} exige a chave de 44 dígitos. Informar a chave do XML/DANFE.")
            continue
        if not _check_digit(key):
            _hit(hits, row, document, "key.invalid", "Chave de acesso inválida", "Alta", "Chave", key, "", "A chave não tem 44 dígitos ou o dígito verificador não confere: foi digitada errada. Copiar a chave do XML/DANFE.")
            continue
        model = key[20:22]
        if species and model in MODEL_SPECIES and species not in MODEL_SPECIES[model][0]:
            _hit(hits, row, document, "key.species_mismatch", "Espécie do documento incompatível com a chave", "Média", "Espécie", species, MODEL_SPECIES[model][1], f"A chave é de modelo {model} ({MODEL_SPECIES[model][1]}) e o documento foi lançado com espécie {species}. Corrigir a espécie: o SPED leva cada modelo num registro diferente (C100, D100, C500...).")
        if document is None:
            number = _as_int(row["number"])
            if number is not None and int(key[25:34]) != number:
                _hit(hits, row, document, "key.number_mismatch", "Chave de acesso não confere com o número do documento", "Alta", "Número", row["number"], str(int(key[25:34])), "O número embutido na chave é outro: a chave ou o número foi digitado errado. Conferir no DANFE/XML.")
            elif _series(key[22:25]) != _series(row["series"]):
                _hit(hits, row, document, "key.series_mismatch", "Série divergente da chave de acesso", "Média", "Série", row["series"], key[22:25].lstrip("0") or "0", "A série embutida na chave é outra: corrigir a série do lançamento.")


def _supplier_keys(result, rows, documents, company_tax_id, hits) -> None:
    del result
    seen: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for row in rows:
        document = documents.get(row["access_key"])
        if document and document.issuer_tax_id and document.issuer_tax_id != company_tax_id and row["own_form"] != "S":
            seen[(row["supplier"], row["store"])][document.issuer_tax_id] += 1
    for row in rows:
        document = documents.get(row["access_key"])
        issuer = document.issuer_tax_id if document else (row["access_key"][6:20] if _check_digit(row["access_key"]) else "")
        if not issuer or issuer == company_tax_id or row["own_form"] == "S":
            continue
        launched = row["tax_id"]
        if not launched:
            counts = seen.get((row["supplier"], row["store"]))
            if counts:
                top, count = counts.most_common(1)[0]
                if top != issuer and count >= 2 and count > counts.get(issuer, 0):
                    launched = top
        if launched and launched != issuer:
            who = f" ({document.issuer_name})" if document else ""
            source = "do XML" if document else "na chave"
            _hit(hits, row, document, "key.supplier_mismatch", "Fornecedor do lançamento com CNPJ diferente do emitente", "Alta", "CNPJ", _cnpj(launched), _cnpj(issuer), f"Lançada no fornecedor {row['supplier']}/{row['store']} ({row['name']}), que é o CNPJ {_cnpj(launched)}; o emitente {source} é o CNPJ {_cnpj(issuer)}{who}. Escriturar no código/loja do CNPJ certo: o SPED leva o participante errado (0150) e o título fica no fornecedor errado.")


def _unmatched(result, rows, invoices_only, invoices, ctes, company_tax_id, settings) -> None:
    booked = {row["access_key"] for row in rows}
    issued = [document.issued_at for document in invoices.values() if document.issued_at is not None]
    latest = max(issued) if issued else datetime.now()
    if settings.improvements_enabled and settings.period_end is not None:
        recent = datetime.combine(settings.period_end, datetime.min.time()) - timedelta(days=settings.unmatched_grace_days)
        transit_is_info = True
    else:
        recent = latest - timedelta(days=settings.unmatched_grace_days)
        transit_is_info = False
    root = company_tax_id[:8]
    for document in sorted(invoices.values(), key=lambda item: item.issued_at or datetime.min):
        if document.access_key in booked:
            continue
        result.unmatched.append(_xml_unmatched(document, *_xml_situation(document, company_tax_id, recent, transit_is_info=transit_is_info), "SPED"))
    for document in sorted(ctes.values(), key=lambda item: item.issued_at or datetime.min):
        if document.access_key in booked:
            continue
        result.unmatched.append(_xml_unmatched(document, *_cte_situation(document, company_tax_id, root), "CTE"))
    earliest = min(issued) if issued else None
    latest_invoice = max(issued) if issued else None
    for row in sorted((row for row in invoices_only if row["access_key"] not in invoices), key=lambda item: item["issue_date"] or datetime.min.date()):
        if earliest is not None and row["issue_date"] is not None and row["issue_date"] < earliest.date():
            reason = f'Emitida em {row["issue_date"]:%m/%Y}, antes do período do download de XML ({earliest:%d/%m/%Y} a {latest_invoice:%d/%m/%Y}). Para fechar, baixar os XML do mês anterior.'
            severity = "Info"
        else:
            reason, severity = "Emitida dentro do período, mas o XML não veio no download. Baixar e conferir.", "Média"
        result.unmatched.append(_book_unmatched(row, severity, reason))
    if ctes:
        cte_dates = [document.issued_at for document in ctes.values() if document.issued_at is not None]
        first = min(cte_dates) if cte_dates else None
        for row in sorted((row for row in rows if row["cte"] and row["access_key"] not in ctes), key=lambda item: item["issue_date"] or datetime.min.date()):
            if first is not None and row["issue_date"] is not None and row["issue_date"] < first.date():
                reason = f'CT-e emitido em {row["issue_date"]:%m/%Y}, antes do período dos XML de CT-e. Para fechar, baixar os do mês anterior.'
                severity = "Info"
            else:
                reason, severity = "CT-e emitido dentro do período, mas o XML não veio no download. Baixar e conferir.", "Média"
            result.unmatched.append(_book_unmatched(row, severity, reason))


def _items_rules(result, item_rows, invoices, tes, book, company_state, presumed_tes, presumed_on, settings, hits, boosted) -> None:
    danfe = [item for item in item_rows if item["danfe"]]
    grouped = 0
    for key in sorted({item["access_key"] for item in danfe if item["access_key"] in invoices}):
        rows = sorted((item for item in danfe if item["access_key"] == key), key=lambda item: _item_number(item["item"]))
        xml_items = sorted(invoices[key].items, key=lambda item: item.number)
        if len(rows) != len(xml_items):
            grouped += 1
            for row in rows:
                _internal(result, row, None, 0.0, True, company_state, tes, book, hits, boosted, settings)
            continue
        paired = list(zip(rows, xml_items, strict=True))
        bad = sum(abs(row["total"] - xml_item.amount) > settings.tolerance for row, xml_item in paired)
        if bad:
            remaining = list(xml_items)
            alternative = []
            for row in rows:
                index = min(range(len(remaining)), key=lambda position: abs(remaining[position].amount - row["total"]))
                alternative.append(remaining.pop(index))
            if sum(abs(row["total"] - xml_item.amount) > settings.tolerance for row, xml_item in zip(rows, alternative, strict=True)) < bad:
                paired = list(zip(rows, alternative, strict=True))
        for row, xml_item in paired:
            _one_item(result, row, xml_item, invoices[key], tes, book, company_state, presumed_tes, presumed_on, settings, hits, boosted)
    result.summary["grouped_notes"] = grouped
    _unusual_nature(danfe, hits)
    for row in danfe:
        if row["access_key"] not in invoices:
            _internal(result, row, None, 0.0, True, company_state, tes, book, hits, boosted, settings)
    _excluded(result, item_rows)
    if book.present:
        _fiscal_book(result, danfe, tes, book, hits, boosted, settings)


def _one_item(result, row, xml_item, document, tes, book, company_state, presumed_tes, presumed_on, settings, hits, boosted) -> None:
    simple = xml_item and document.crt in {"1", "4"}
    reference = round(xml_item.simple_credit, 2) if simple else xml_item.icms_amount
    _internal(result, row, xml_item, reference, False, company_state, tes, book, hits, boosted, settings)
    if abs(row["total"] - xml_item.amount) > settings.tolerance:
        _hit(hits, row, document, "item.amount_mismatch", "Valor do item diverge", "Alta", "Vlr Item", row["total"], xml_item.amount, "Quantidade ou preço digitado diferente do XML.", item=row["item"])
    _cfop(row, xml_item, document, hits)
    _origin_and_cst(result, row, xml_item, document, tes, book, hits, settings)
    eligible = _eligible(presumed_on, row["state"], document.crt, xml_item.cfop)
    reference_rate = xml_item.simple_rate if simple else xml_item.icms_rate
    booked = row["icms"]
    amounts_match = abs(booked - reference) <= settings.tolerance
    if eligible:
        reference, reference_rate, amounts_match = _presumed(result, row, xml_item, document, presumed_tes, booked, hits, settings)
    elif presumed_on and row["tes"] == presumed_tes:
        _presumed_without_right(row, xml_item, document, presumed_tes, hits)
    if not eligible and not amounts_match and not (row["cfop"][1:] in {"556", "407"} and booked > settings.tolerance):
        _item_icms(result, row, xml_item, document, booked, reference, reference_rate, simple, tes, hits, settings)
    _item_credit_lost(row, xml_item, document, reference, simple, eligible, tes, book, hits, settings)
    _item_rate_and_base(result, row, xml_item, document, booked, reference, simple, eligible, amounts_match, tes, book, hits, settings)
    _item_ipi(result, row, xml_item, document, tes, book, hits, settings)
    if abs(row["st"] - xml_item.st_amount) > settings.tolerance:
        _hit(hits, row, document, "item.st_mismatch", "ICMS ST divergente", "Alta", "ICMS ST", row["st"], xml_item.st_amount, "Rever ST na TES.", item=row["item"])


def _cfop(row, xml_item, document, hits) -> None:
    protheus_cfop = row["cfop"]
    xml_cfop = xml_item.cfop
    if row["own_form"] == "S":
        if xml_cfop != protheus_cfop:
            _hit(hits, row, document, "item.cfop_differs_from_issued", "CFOP diferente do documento emitido", "Alta", "CFOP", protheus_cfop, xml_cfop, "Formulário próprio: o CFOP lançado tem de ser o do XML.", item=row["item"])
        return
    if xml_cfop and xml_cfop[0] in "123":
        _hit(hits, row, document, "item.inbound_booked_as_purchase", "NF de entrada do fornecedor lançada como compra", "Alta", "CFOP", protheus_cfop, xml_cfop, "O XML é uma nota de ENTRADA emitida pelo fornecedor (a empresa é a remetente). Verificar e excluir o lançamento.", item=row["item"])
        return
    if not xml_cfop:
        return
    expected = {"5": "1", "6": "2", "7": "3"}.get(xml_cfop[0], "")
    if protheus_cfop[:1] != expected:
        _hit(hits, row, document, "item.cfop_direction_swapped", "CFOP com origem trocada (interna × interestadual)", "Alta", "CFOP", protheus_cfop, xml_cfop, f"CFOP {xml_cfop} do fornecedor pede entrada iniciada em {expected}.", item=row["item"])
    group = next((item for item in CFOP_GROUPS if xml_cfop[1:] in item[0]), None)
    if group and protheus_cfop[1:] not in group[1]:
        _hit(hits, row, document, "item.cfop_nature_mismatch", "Natureza do CFOP incompatível com o documento", "Média", "CFOP", protheus_cfop, xml_cfop, f"O fornecedor emitiu como {group[2]} ({xml_cfop}); o CFOP de entrada {protheus_cfop} é de outra natureza.", item=row["item"])
    elif xml_cfop[1:] == "653" and protheus_cfop[1:] != "653":
        _hit(hits, row, document, "item.fuel_cfop", "Combustível fora do CFOP x653", "Baixa", "CFOP", protheus_cfop, xml_cfop, "Venda de combustível a consumidor final: entrada usual em 1653/2653.", item=row["item"])
    taxed = xml_item.cst in ST_CST or xml_item.csosn in ST_CSOSN or xml_cfop[1:] in {"401", "402", "403", "404", "405"}
    if taxed and protheus_cfop[1:] in {"101", "102", "556", "551"}:
        suggestion = {"556": "407", "551": "406", "101": "401", "102": "403"}[protheus_cfop[1:]]
        _hit(hits, row, document, "item.st_on_non_st_cfop", "Item com ST no XML lançado em CFOP sem ST", "Média", "CFOP", protheus_cfop, xml_cfop, f"Item com ICMS-ST (CST/CSOSN {xml_item.cst or xml_item.csosn}). CFOP de entrada correspondente: {protheus_cfop[0]}{suggestion}.", item=row["item"])
    elif not taxed and protheus_cfop[1:] in {"401", "403", "406", "407"}:
        _hit(hits, row, document, "item.st_cfop_without_st", "CFOP de ST sem ST no XML", "Média", "CFOP", protheus_cfop, xml_cfop, "Entrada classificada como ST, mas o item não tem ST no documento.", item=row["item"])


def _origin_and_cst(result, row, xml_item, document, tes, book, hits, settings) -> None:
    if row["cst"] and xml_item.origin and row["cst"][0] != xml_item.origin:
        _hit(hits, row, document, "item.origin_mismatch", "Origem da mercadoria divergente", "Média", "CST (origem)", row["cst"], xml_item.origin + (xml_item.cst or xml_item.csosn), f'Origem {xml_item.origin} no XML e {row["cst"][0]} no Protheus. Origens 1, 2, 3 e 8 indicam conteúdo importado (alíquota interestadual de 4%).', item=row["item"])
    line = book.item(row)
    credits = (line["icms"] > settings.tolerance) if line is not None else _credits_icms(tes.get(row["tes"]))
    if document.crt not in {"1", "4"} and xml_item.cst and row["cst"][-2:] != xml_item.cst:
        if row["cst"][-2:] == "90" and (row["icms"] <= settings.tolerance or credits is False):
            result.suppress("suppressed.cst_090", LABEL_CST_090)
        elif row["cst"][-2:] == "60" and (_fuel(xml_item) or xml_item.cst in ST_CST):
            result.suppress("suppressed.cst_060", LABEL_CST_060)
        else:
            _hit(hits, row, document, "item.cst_mismatch", "CST diverge do documento", "Média", "CST", row["cst"], xml_item.origin + xml_item.cst, "Tributação lançada diferente da nota do fornecedor. Rever a TES.", item=row["item"])


def _presumed(result, row, xml_item, document, presumed_tes, booked, hits, settings):
    del result
    base = round(xml_item.amount - xml_item.discount, 2)
    expected = round(base * PRESUMED["rate"], 2)
    cap, revenue = _simple_band(xml_item.simple_rate, "II") if xml_item.simple_rate > 0 else (None, 0)
    if row["tes"] != presumed_tes:
        consumption = row["cfop"][1:] in CONSUMPTION_OR_ASSET
        prefix = f"Entrada como uso e consumo/ativo (CFOP {row['cfop']}): confirmar se o presumido alcança esse destino (Anexo 2, art. 15, § 25) antes de mudar a TES. " if consumption else ""
        _hit(hits, row, document, "simples.presumed_wrong_tes", "Indústria do Simples (SC) fora da TES de crédito presumido", "Média" if consumption else "Alta", "TES", 0.0, expected, prefix + f"Compra interna de indústria do Simples de SC (CFOP {xml_item.cfop}) tem direito ao crédito presumido de 7% (RICMS/SC, Anexo 2, art. 15, XXVI), que deve entrar pela TES {presumed_tes}. Lançada na TES {row['tes']}: o fornecedor não está cadastrado no Configurador de Tributos. Cadastrar e reprocessar. Crédito presumido esperado: R$ {_brl(expected)} (7% de R$ {_brl(base)}).", item=row["item"])
    elif revenue is None:
        _hit(hits, row, document, "simples.presumed_above_sublimite", "Crédito presumido com fornecedor acima do sublimite", "Alta", "pCredSN (%)", xml_item.simple_rate, round(cap, 2), f'Nota na TES {presumed_tes} (crédito presumido de 7%), mas o pCredSN de {xml_item.simple_rate:g}% passa do teto possível dentro do sublimite ({cap:.2f}%). Se o fornecedor ultrapassou o sublimite, não há direito ao presumido (COPAT 75/2022). Confirmar a situação do fornecedor antes de apropriar R$ {_brl(expected)}.', item=row["item"])
    if row["tes"] == presumed_tes and booked > settings.tolerance and abs(booked - expected) > settings.tolerance:
        _hit(hits, row, document, "simples.presumed_rate_mismatch", "Valor no item diferente do crédito presumido de 7%", "Média", "ICMS", booked, expected, f"O item na TES {presumed_tes} traz R$ {_brl(booked)}, mas 7% de R$ {_brl(base)} são R$ {_brl(expected)}. Conferir a regra do Configurador de Tributos.", item=row["item"])
    return expected, PRESUMED["rate"] * 100, abs(booked - expected) <= settings.tolerance


def _presumed_without_right(row, xml_item, document, presumed_tes, hits) -> None:
    if document.crt != "1":
        reason = "fornecedor não é do Simples"
    elif row["state"] != "SC":
        reason = f"fornecedor é de {row['state']}, não de SC"
    else:
        reason = f"CFOP {xml_item.cfop} não é de venda de produção própria (indústria)"
    _hit(hits, row, document, "simples.presumed_without_right", "TES de crédito presumido em nota sem direito", "Média", "TES", 0.0, 0.0, f"Item lançado na TES {presumed_tes} (crédito presumido de 7% de SC), mas {reason}. Rever a TES.", item=row["item"])


def _item_icms(result, row, xml_item, document, booked, reference, reference_rate, simple, tes, hits, settings) -> None:
    rates = f' Alíquota: Protheus {row["icms_rate"]:g}% × XML {reference_rate:g}%.'
    if booked > settings.tolerance and reference == 0:
        _depend(result, hits, row, document, row["item"], "item.icms_above_xml", "ICMS calculado sem destaque no XML", "ICMS", booked, reference, ("Simples sem crédito SN no item." if simple else f'Item sem ICMS no XML (CST {xml_item.cst}).') + rates, tes, None, {}, item_scope=True)
    elif booked > reference:
        _depend(result, hits, row, document, row["item"], "item.icms_above_xml", "ICMS calculado acima do XML", "ICMS", booked, reference, ("Simples: só vale o vCredICMSSN." if simple else "Acima do destacado.") + rates, tes, None, {}, item_scope=True)
    elif booked <= settings.tolerance:
        if row["cfop"][1:] in SUPPLY_SUFFIXES and not tes:
            _hit(hits, row, document, "item.highlighted_icms_not_credited", "ICMS do XML não creditado em insumo/revenda", "Média", "ICMS", booked, reference, f'CFOP {row["cfop"]} dá direito a crédito e o ICMS ficou zerado.', item=row["item"])
    else:
        _hit(hits, row, document, "header.icms_credit_short", "Crédito de ICMS a menor", "Média", "ICMS", booked, reference, "Abaixo do destacado." + rates, item=row["item"])


def _item_credit_lost(row, xml_item, document, reference, simple, eligible, tes, book, hits, settings) -> None:
    if eligible or reference <= settings.tolerance or row["cfop"][1:] not in SUPPLY_SUFFIXES:
        return
    line = book.item(row)
    without = (line["icms"] <= settings.tolerance and _credits_icms(tes.get(row["tes"])) is not True) if line is not None else (bool(tes) and _credits_icms(tes.get(row["tes"])) is False)
    if not without:
        return
    record = tes.get(row["tes"])
    if simple:
        _hit(hits, row, document, "item.simples_credit_not_taken", "Crédito do Simples não aproveitado (TES sem crédito)", "Média", "ICMS", 0.0, reference, f"Simples informou crédito de {xml_item.simple_rate:g}% (CSOSN {xml_item.csosn}) em CFOP {row['cfop']}, que dá direito a crédito. A TES {row['tes']} ({record.description if record else ''}) não credita.", item=row["item"])
    else:
        book_note = " O livro fiscal (SFT) também está sem crédito." if line is not None else ""
        _hit(hits, row, document, "item.highlighted_icms_not_credited", "ICMS destacado não creditado em insumo/revenda (TES sem crédito)", "Média", "ICMS", 0.0, reference, f"CFOP {row['cfop']} dá direito a crédito e a TES {row['tes']} não credita.{book_note}", item=row["item"])


def _item_rate_and_base(result, row, xml_item, document, booked, reference, simple, eligible, amounts_match, tes, book, hits, settings) -> None:
    del reference
    line = book.item(row)
    credits = (line["icms"] > settings.tolerance) if line is not None else _credits_icms(tes.get(row["tes"]))
    if not eligible and not simple and amounts_match and booked > settings.tolerance and abs(row["icms_rate"] - xml_item.icms_rate) > 0.01:
        if credits is False:
            result.suppress("suppressed.base_or_rate_without_credit", LABEL_RATE_OR_BASE)
        else:
            _hit(hits, row, document, "item.rate_or_base_mismatch", "Alíquota de ICMS divergente (valor confere)", "Média", "Alíq. ICMS", row["icms_rate"], xml_item.icms_rate, f'Valor confere, mas a alíquota gravada é {row["icms_rate"]:g}% e a do documento {xml_item.icms_rate:g}%. Vai assim para o C170 do SPED: corrigir.', item=row["item"])
    if not simple and amounts_match and booked > settings.tolerance and abs(row["icms_base"] - xml_item.icms_base) > settings.tolerance:
        if credits is False:
            result.suppress("suppressed.base_or_rate_without_credit", LABEL_RATE_OR_BASE)
        else:
            _hit(hits, row, document, "item.rate_or_base_mismatch", "Base de ICMS divergente (ICMS confere)", "Média", "Base ICMS", row["icms_base"], xml_item.icms_base, f'ICMS confere, mas a base escriturada (R$ {_brl(row["icms_base"])}) difere da do documento (R$ {_brl(xml_item.icms_base)}). Vai assim para o C170/C190: corrigir a base.', item=row["item"])


def _item_ipi(result, row, xml_item, document, tes, book, hits, settings) -> None:
    line = book.item(row)
    credits = (line["ipi"] > settings.tolerance) if line is not None else _credits_ipi(tes.get(row["tes"]))
    if abs(row["ipi"] - xml_item.ipi_amount) > settings.tolerance:
        if credits is False:
            result.suppress("suppressed.ipi_without_credit", LABEL_IPI_WITHOUT_CREDIT)
        elif row["ipi"] > settings.tolerance and abs(row["ipi"] - xml_item.other_amount) <= settings.tolerance:
            result.suppress("suppressed.ipi_without_credit", LABEL_IPI_TOTAL_OK)
        elif row["ipi"] < xml_item.ipi_amount:
            if credits:
                _hit(hits, row, document, "item.ipi_credit_mismatch", "Crédito de IPI abaixo do XML", "Média", "IPI", row["ipi"], xml_item.ipi_amount, f'A TES {row["tes"]} credita IPI e escriturou R$ {_brl(row["ipi"])}, mas o documento destaca R$ {_brl(xml_item.ipi_amount)} ({xml_item.ipi_rate:g}%). Crédito perdido: conferir base e alíquota de IPI.', item=row["item"])
            else:
                _hit(hits, row, document, "item.ipi_without_tes_decision", "IPI do XML não escriturado", "Alta", "IPI", row["ipi"], xml_item.ipi_amount, f'TES {row["tes"]} não calcula IPI. Alíquota no XML: {xml_item.ipi_rate:g}%.', item=row["item"])
        else:
            above = credits is True
            _hit(hits, row, document, "item.ipi_credit_mismatch" if above else "item.ipi_without_tes_decision", "Crédito de IPI acima do XML" if above else "IPI escriturado sem destaque no XML", "Alta", "IPI", row["ipi"], xml_item.ipi_amount, f'A TES {row["tes"]} credita IPI e escriturou mais do que o documento destaca: crédito indevido a estornar.' if above else "Rever a TES.", item=row["item"])
    elif credits is not False and row["ipi"] > settings.tolerance and abs(row["ipi_base"] - xml_item.ipi_base) > settings.tolerance:
        _hit(hits, row, document, "item.ipi_base_mismatch", "Base de IPI divergente", "Média", "Base IPI", row["ipi_base"], xml_item.ipi_base, f'IPI confere, mas a base escriturada (R$ {_brl(row["ipi_base"])}) difere da do documento (R$ {_brl(xml_item.ipi_base)}). Vai assim para o C170 do SPED: corrigir a base de IPI.', item=row["item"])


def _internal(result, row, xml_item, reference, check_cst, company_state, tes, book, hits, boosted, settings) -> None:
    suffix = row["cfop"][1:]
    record = tes.get(row["tes"])
    document = None
    if row["own_form"] != "S" and row["cfop"] and row["state"] and row["cfop"][0] != _state_digit(row["state"], company_state):
        _hit(hits, row, document, "coherence.cfop_vs_state", "CFOP de entrada incompatível com a UF do fornecedor", "Alta", "CFOP", row["cfop"], "UF " + row["state"], f'Fornecedor em {row["state"]} pede CFOP iniciado em {_state_digit(row["state"], company_state)}.', item=row["item"])
    line = book.item(row)
    consumption = bool(record and record.consumption_material == "Sim") or suffix in CONSUMPTION_OR_ASSET[:3]
    if line is not None:
        if consumption and line["ipi"] > settings.tolerance:
            _hit(hits, row, document, "coherence.ipi_on_consumption", "Crédito de IPI em material de uso e consumo", "Alta", "IPI", round(line["ipi"], 2), 0.0, f'O livro fiscal (SFT) traz R$ {_brl(line["ipi"])} de IPI creditado em material de consumo (TES {row["tes"]}, CFOP {row["cfop"]}). IPI só gera crédito em MP, PI e embalagem: estornar e ajustar a TES.', item=row["item"])
    elif record and _credits_ipi(record) and record.consumption_material == "Sim" and row["ipi"] > settings.tolerance:
        _hit(hits, row, document, "coherence.ipi_on_consumption", "Crédito de IPI em material de uso e consumo", "Alta", "IPI", row["ipi"], 0.0, f"TES {row['tes']} ({record.description}) é de material de consumo e credita IPI (livro {record.ipi_book}). IPI só gera crédito em MP, PI e embalagem: estornar e ajustar a TES.", item=row["item"])
    if suffix in {"556", "407"} and row["icms"] > settings.tolerance:
        _depend(result, hits, row, document, row["item"], "coherence.icms_on_consumption_cfop", "ICMS calculado em CFOP de uso e consumo", "ICMS", row["icms"], reference, f'CFOP {row["cfop"]} é uso e consumo, que não dá crédito.', tes, book, {}, item_scope=True, boosted=boosted)
    if check_cst and row["cst"][-2:] in {"40", "41", "50", "60", "61"} and row["icms"] > settings.tolerance and suffix not in {"556", "407"}:
        _depend(result, hits, row, document, row["item"], "coherence.icms_on_untaxed_cst", "ICMS calculado com CST sem tributação", "ICMS", row["icms"], 0.0, f'CST {row["cst"]} sem ICMS próprio e item com ICMS calculado.', tes, book, {}, item_scope=True, boosted=boosted)


def _fiscal_book(result, rows, tes, book, hits, boosted, settings) -> None:
    del result
    for row in rows:
        line = book.item(row)
        if line is None:
            _hit(hits, row, None, "fiscal_book.item_missing", "Item sem registro no livro fiscal (SFT)", "Média", "ICMS livro", row["icms"], 0.0, "Item classificado na SD1 sem linha correspondente na SFT: não vai para o SPED. Reprocessar os livros fiscais (MATA930) ou conferir o filtro da SFT.", item=row["item"])
            continue
        credits = _credits_icms(tes.get(row["tes"]))
        if credits is False and line["icms"] > settings.tolerance and (row["k"], row["item"]) not in boosted:
            _hit(hits, row, None, "fiscal_book.credit_against_tes", "Crédito no livro fiscal em TES que não credita", "Alta", "ICMS livro", round(line["icms"], 2), 0.0, f'A TES {row["tes"]} não credita ICMS, mas o livro fiscal (SFT) traz R$ {_brl(line["icms"])} de crédito: o livro diverge da TES (TES alterada depois do lançamento ou ajuste manual). Reprocessar o livro ou estornar.', item=row["item"])
        elif credits is True and row["icms"] > settings.tolerance and line["icms"] <= settings.tolerance:
            _hit(hits, row, None, "fiscal_book.credit_missing", "Crédito previsto na TES fora do livro fiscal", "Média", "ICMS livro", 0.0, row["icms"], f'A TES {row["tes"]} credita ICMS e o item calculou R$ {_brl(row["icms"])}, mas o livro fiscal (SFT) está sem crédito: crédito não aproveitado. Reprocessar o livro.', item=row["item"])
        elif line["icms"] > settings.tolerance and row["icms"] > settings.tolerance and abs(line["icms"] - row["icms"]) > settings.tolerance:
            _hit(hits, row, None, "fiscal_book.amount_mismatch", "ICMS do livro fiscal diferente do item", "Média", "ICMS livro", round(line["icms"], 2), row["icms"], "Crédito no livro (SFT) diferente do ICMS calculado na SD1. Reprocessar o livro ou conferir ajuste manual.", item=row["item"])


def _unusual_nature(rows, hits) -> None:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        nature = _nature(row["cfop"])
        if row["product"] and nature:
            grouped[row["product"]].append(row)
    for product, product_rows in grouped.items():
        counts = Counter(_nature(row["cfop"]) for row in product_rows)
        if len(counts) < 2:
            continue
        top, count = counts.most_common(1)[0]
        if count < 2 or list(counts.values()).count(count) > 1:
            continue
        usual = ", ".join(sorted({row["cfop"] for row in product_rows if _nature(row["cfop"]) == top}))
        for row in product_rows:
            if _nature(row["cfop"]) == top:
                continue
            _hit(hits, row, None, "item.unusual_cfop_nature", "Produto lançado com natureza de CFOP diferente do usual", "Média", "CFOP", row["cfop"], usual, f"O produto {product} entrou {count} vezes no período como {top} ({usual}) e nesta nota como {_nature(row['cfop'])} ({row['cfop']}). Conferir a destinação (uso e consumo × industrialização/revenda × ativo): muda CFOP, TES e crédito.", item=row["item"])


def _excluded(result, rows) -> None:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        if row["danfe"]:
            continue
        groups[( _excluded_kind(row), row["number"], row["series"], row["supplier"], row["store"])].append(row)
    for (kind, number, series, supplier, store), grouped in groups.items():
        result.excluded.append(ExcludedItem(kind, number, series, supplier, store, len(grouped), sum(item["total"] for item in grouped)))


def _depend(result, hits, row, document, item, rule_id, title, field, protheus_value, xml_value, action, tes, book, tes_by_document, item_scope=False, boosted=None) -> None:
    if item_scope:
        record_credit = _credits_icms(tes.get(row["tes"]))
        line = book.item(row) if book is not None else None
        if line is not None:
            if line["icms"] > 0.05:
                title = title.replace("ICMS calculado", "Crédito de ICMS")
                action = f"O livro fiscal (SFT) traz R$ {_brl(line['icms'])} de ICMS creditado neste item: vai para a apuração. Crédito indevido a estornar. " + action
                if record_credit is False:
                    action += f' A TES {row["tes"]} não credita: o livro diverge da TES (TES alterada depois do lançamento ou ajuste manual).'
                if boosted is not None:
                    boosted.add((row["k"], row["item"]))
                _hit(hits, row, document, rule_id, title, "Alta", field, round(line["icms"], 2), xml_value, action, item=item)
            else:
                result.suppress("suppressed.icms_without_credit", LABEL_ICMS_WITHOUT_CREDIT)
            return
        if record_credit is not None:
            if record_credit:
                record = tes.get(row["tes"])
                action = _tes_text(record) + " A TES credita: crédito indevido a estornar. " + action
                _hit(hits, row, document, rule_id, title.replace("ICMS calculado", "Crédito de ICMS"), "Alta", field, protheus_value, xml_value, action, item=item)
            else:
                result.suppress("suppressed.icms_without_credit", LABEL_ICMS_WITHOUT_CREDIT)
            return
        if record_credit is None and row["tes"] in tes and _icms_incoherent(tes[row["tes"]]):
            action += f" TES {row['tes']} com crédito e livro desencontrados ({'; '.join(_incoherent(tes[row['tes']]))}): só a SFT diz se foi para a apuração."
        _hit(hits, row, document, rule_id, title, "Depende da TES", field, protheus_value, xml_value, action, item=item)
        return
    credit = _note_credit(row, tes, book, tes_by_document)
    line = book.doc(row) if book is not None else None
    source = f"Livro fiscal (SFT) com R$ {_brl(line['icms'])} de ICMS" if line is not None else f'TES {tes_by_document.get(row["k"], "")}'
    if credit is True and line is not None:
        protheus_value = round(line["icms"], 2)
    if credit is True:
        _hit(hits, row, document, rule_id, title.replace("ICMS calculado", "Crédito de ICMS"), "Alta", field, protheus_value, xml_value, f"{source} credita ICMS: crédito indevido a estornar. " + action, item=item)
    elif credit is False:
        result.suppress("suppressed.icms_without_credit", LABEL_ICMS_WITHOUT_CREDIT)
    else:
        _hit(hits, row, document, rule_id, title, "Depende da TES", field, protheus_value, xml_value, action, item=item)


def _correct_keys(rows, documents, company_tax_id, tolerance, result) -> None:
    del result
    used = {row["access_key"] for row in rows}
    free: dict[int, list[XmlDocument]] = defaultdict(list)
    for key, document in documents.items():
        if key in used or document.cancelled:
            continue
        if document.issuer_tax_id == company_tax_id and document.direction == "Saída":
            continue
        free[document.number].append(document)
    for row in rows:
        if row["access_key"] in documents:
            continue
        number = _as_int(row["number"])
        if number is None:
            continue
        candidates = [document for document in free.get(number, []) if abs(document.total_amount - row["gross"]) <= tolerance]
        if len(candidates) > 1:
            candidates = [document for document in candidates if _series(document.series) == _series(row["series"])]
        if len(candidates) == 1:
            chosen = candidates[0]
            row["access_key"] = chosen.access_key
            row["fixed"] = True
            free[number].remove(chosen)


class _Book:
    def __init__(self, lines: list[FiscalBookLine] | None, branch: str):
        self.present = lines is not None
        self.items: dict[tuple[str, int], dict[str, float]] = {}
        self.documents: dict[str, dict[str, float]] = {}
        if not self.present:
            return
        for line in lines or []:
            if line.branch and line.branch != branch:
                continue
            if line.movement and line.movement.upper()[:1] not in {"E", ""}:
                continue
            if line.cancelled:
                continue
            key = _document_key(branch, line.number, line.series, line.supplier_code, line.supplier_store)
            slot = self.items.setdefault((key, _item_number(line.item)), {"icms": 0.0, "ipi": 0.0})
            slot["icms"] += line.icms_amount
            slot["ipi"] += line.ipi_amount
        for (key, _), values in self.items.items():
            document = self.documents.setdefault(key, {"icms": 0.0, "ipi": 0.0})
            document["icms"] += values["icms"]
            document["ipi"] += values["ipi"]

    def item(self, row) -> dict[str, float] | None:
        if not self.present:
            return None
        key = _document_key(row["branch"], row["number"], row["series"], row["supplier"], row["store"])
        return self.items.get((key, _item_number(row["item"])))

    def doc(self, row) -> dict[str, float] | None:
        if not self.present:
            return None
        return self.documents.get(_document_key(row["branch"], row["number"], row["series"], row["supplier"], row["store"]))


def _view(header: ProtheusHeader) -> dict:
    return {
        "branch": header.branch, "number": header.number, "series": header.series,
        "supplier": header.supplier_code, "store": header.supplier_store, "state": header.supplier_state,
        "name": header.supplier_name, "tax_id": _digits(header.supplier_tax_id), "species": (header.species or "").upper(),
        "own_form": header.own_form, "access_key": header.access_key or "", "original_key": header.access_key or "",
        "issue_date": header.issue_date, "fixed": False,
        "freight": header.freight_amount, "expense": header.expense_amount, "icms_base": header.icms_base,
        "icms": header.icms_amount, "ipi": header.ipi_amount, "goods": header.goods_amount, "gross": header.gross_amount,
        "discount": header.discount_amount, "st": header.st_amount,
        "k": f"{header.branch}|{header.number}|{header.series}|{header.supplier_code}|{header.supplier_store}",
    }


def _items(items: list[ProtheusItem], rows: list[dict], branch: str) -> list[dict]:
    by_key = {row["k"]: row for row in rows}
    built = []
    for item in items:
        if item.branch != branch:
            continue
        key = f"{branch}|{item.number}|{item.series}|{item.supplier_code}|{item.supplier_store}"
        header = by_key.get(key, {})
        built.append({
            "branch": branch, "number": item.number, "series": item.series, "supplier": item.supplier_code,
            "store": item.supplier_store, "item": item.item, "product": item.product_code, "cfop": item.cfop,
            "cst": item.tax_situation, "tes": item.tes, "total": item.total_amount, "icms_base": item.icms_base,
            "icms_rate": item.icms_rate, "icms": item.icms_amount, "ipi_base": item.ipi_base, "ipi": item.ipi_amount,
            "st": item.st_amount, "k": key, "access_key": header.get("access_key", ""),
            "name": header.get("name", ""), "state": header.get("state", ""), "own_form": header.get("own_form", ""),
            "species": header.get("species", ""), "danfe": header.get("danfe", False),
        })
    return built


def _tes_by_document(rows: list[dict]) -> dict[str, str]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["tes"]:
            grouped[row["k"]].add(row["tes"])
    return {key: ", ".join(sorted(values)) for key, values in grouped.items()}


def _note_credit(row, tes, book, tes_by_document):
    line = book.doc(row) if book is not None else None
    if line is not None:
        return line["icms"] > 0.05
    codes = [code for code in tes_by_document.get(row["k"], "").split(", ") if code]
    if not codes or not tes:
        return None
    decisions = [_credits_icms(tes.get(code)) for code in codes]
    if any(decision is True for decision in decisions):
        return True
    if any(decision is None for decision in decisions):
        return None
    return False


def _note_consumption(row, tes, tes_by_document) -> bool:
    codes = [code for code in tes_by_document.get(row["k"], "").split(", ") if code]
    return bool(codes) and bool(tes) and all(
        (record := tes.get(code)) is not None and (record.consumption_material == "Sim" or record.fiscal_code[1:] in CONSUMPTION_OR_ASSET)
        for code in codes
    )


def _cte_credit(row, lines, icms, tes, book):
    line = book.doc(row)
    if line is not None:
        return line["icms"] > 0.05, round(line["icms"], 2)
    codes = sorted({item["tes"] for item in lines if item["tes"]})
    if codes and tes:
        decisions = [_credits_icms(tes.get(code)) for code in codes]
        if any(decision is True for decision in decisions):
            return True, icms
        if any(decision is None for decision in decisions):
            return None, icms
        return False, icms
    return (False, icms) if icms <= 0.05 else (None, icms)


def _freight_right(document: XmlDocument, company_tax_id: str, root: str, nature_by_key, settings):
    if document.simples_national:
        return False, "Transportadora do Simples: o CT-e não destaca ICMS"
    if document.substituted:
        return None, "ICMS da prestação por substituição tributária (CST 60): conferir a regra"
    if document.icms_amount <= settings.tolerance:
        return False, f"Prestação sem ICMS no CT-e (CST {document.cst or '—'})"
    own = [key for key in document.linked_keys if key[6:14] == root]
    third = [key for key in document.linked_keys if key[6:14] != root]
    natures = set().union(*(nature_by_key.get(key, set()) for key in third)) if third else set()
    if own:
        return True, f"Frete de NF-e emitida pela própria empresa ({len(own)} nota(s): venda/transferência)"
    if "insumo/revenda" in natures:
        return True, "Frete de compra para industrialização/revenda"
    if natures and natures <= {"consumo", "ativo"}:
        return False, f"Frete de compra de {' e '.join(sorted(natures))} (sem crédito)"
    if third and not natures:
        return None, "A NF-e transportada não está na SD1 desta filial"
    return None, "CT-e sem NF-e vinculada"


def _xml_unmatched(document: XmlDocument, severity: str, reason: str, species: str) -> UnmatchedDocument:
    item = document.items[0] if document.items else None
    cfop = document.cfop or (item.cfop if item is not None else "")
    cst = document.cst or ((item.origin + item.cst) if item is not None and item.cst else "")
    issued = document.issued_at.date().isoformat() if document.issued_at is not None else ""
    return UnmatchedDocument(
        "xml", str(document.number), severity, reason, document.access_key, species,
        series=str(document.series or ""),
        party_name=document.issuer_name,
        party_tax_id=document.issuer_tax_id,
        party_state=document.issuer_state,
        issue_date=issued,
        amount=document.total_amount,
        icms_base=document.icms_base,
        icms_amount=document.icms_amount,
        ipi_amount=document.ipi_amount,
        cfop=cfop,
        cst=cst,
        nature=_nature(cfop),
    )


def _book_unmatched(row: dict, severity: str, reason: str) -> UnmatchedDocument:
    issued = row["issue_date"].isoformat() if row.get("issue_date") else ""
    return UnmatchedDocument(
        "protheus", row["number"], severity, reason, row["access_key"], row["species"],
        series=str(row.get("series") or ""),
        party_name=str(row.get("name") or ""),
        party_tax_id=str(row.get("tax_id") or ""),
        party_state=str(row.get("state") or ""),
        issue_date=issued,
        amount=row.get("gross"),
        icms_base=row.get("icms_base"),
        icms_amount=row.get("icms"),
        ipi_amount=row.get("ipi"),
    )


def _xml_situation(document: XmlDocument, company_tax_id: str, recent: datetime, *, transit_is_info: bool = False) -> tuple[str, str]:
    if document.cancelled or document.status_code in {"101", "135", "151", "155"}:
        return "Info", "Cancelada na SEFAZ: não deve ser escriturada."
    if document.issuer_tax_id == company_tax_id and document.direction == "Saída":
        return "Info", "Saída emitida pela própria filial: escritura na SF2, não na SF1."
    if document.issuer_tax_id == company_tax_id:
        return "Alta", "Entrada com formulário próprio autorizada e sem lançamento na SF1. Verificar se deveria ter sido lançada ou cancelada."
    if document.recipient_tax_id and document.recipient_tax_id != company_tax_id:
        return "Info", f"Destinatário é outro CNPJ ({document.recipient_tax_id}): não pertence a esta filial."
    reason = "Recebida de terceiro e ainda não escriturada na SF1."
    issued = document.issued_at
    if transit_is_info:
        cutoff = recent.date()
        if issued is not None and issued.date() >= cutoff:
            return "Info", f"{reason} Emissão recente: pode estar em trânsito."
    elif issued is not None and issued >= recent:
        reason += " Emissão recente: pode estar em trânsito."
        return "Média", reason
    if document.icms_amount > 0:
        reason += " Tem ICMS destacado."
    return "Média", reason


def _cte_situation(document: XmlDocument, company_tax_id: str, root: str) -> tuple[str, str]:
    if document.cancelled or document.status_code in {"101", "135"}:
        return "Info", "CT-e cancelado na SEFAZ: não deve ser escriturado."
    if document.taker_tax_id and document.taker_tax_id != company_tax_id:
        other = ", outra filial da empresa" if document.taker_tax_id[:8] == root else ""
        return "Info", f"A empresa não é a tomadora: o tomador é o {TAKER_ROLE.get(document.taker_role, document.taker_role)} ({_cnpj(document.taker_tax_id)}){other}. Quem paga o frete é que escritura."
    reason = "CT-e em que a empresa é a tomadora, ainda não escriturado na SF1."
    if document.icms_amount > 0:
        reason += f" ICMS de R$ {_brl(document.icms_amount)} no CT-e."
    return "Média", reason


def _hit(hits, row, document, rule_id, title, severity, field, protheus_value, xml_value, action, item="") -> None:
    hits.append({
        "rule_id": rule_id, "title": title, "severity": severity, "number": row["number"], "item": item,
        "field": field, "protheus_value": protheus_value, "xml_value": xml_value,
        "access_key": row.get("access_key", ""), "supplier": document.issuer_name if document is not None else row.get("name", ""),
        "action": action,
    })


def _occurrence(hit: dict) -> Occurrence:
    return Occurrence(
        rule_id=hit["rule_id"], title=hit["title"], severity=hit["severity"], document_number=str(hit["number"]),
        item=str(hit["item"]), field=hit["field"], protheus_value=_render(hit["protheus_value"]),
        xml_value=_render(hit["xml_value"]), access_key=hit["access_key"], why=WHY.get(hit["title"], hit["action"]),
        action=hit["action"],
    )


def _dates(row, document, hits, action: str) -> None:
    if row["issue_date"] is None or document.issued_at is None:
        return
    if row["issue_date"] != document.issued_at.date():
        _hit(hits, row, document, "header.issue_date_mismatch", "Data de emissão divergente", "Média", "Emissão", row["issue_date"].strftime("%d/%m/%Y"), document.issued_at.strftime("%d/%m/%Y"), action)


def _credits_icms(record: TesRecord | None) -> bool | None:
    if record is None or _icms_incoherent(record):
        return None
    return record.credits_icms == "Sim"


def _credits_ipi(record: TesRecord | None) -> bool | None:
    if record is None or any(text.startswith("IPI") for text in _incoherent(record)):
        return None
    return record.credits_ipi == "Sim"


def _icms_incoherent(record: TesRecord) -> bool:
    return any(text.startswith("ICMS") for text in _incoherent(record))


def _incoherent(record: TesRecord) -> list[str]:
    found = []
    if record.calculates_icms == "Sim":
        if record.credits_icms == "Sim" and record.icms_book != "Tributado":
            found.append(f'ICMS: credita, mas livro {record.icms_book or "vazio"}')
        if record.credits_icms == "Nao" and record.icms_book == "Tributado":
            found.append("ICMS: não credita, mas livro Tributado")
    if record.calculates_ipi == "Sim":
        if record.credits_ipi == "Sim" and record.ipi_book != "Tributado":
            found.append(f'IPI: credita, mas livro {record.ipi_book or "vazio"}')
        if record.credits_ipi == "Nao" and record.ipi_book == "Tributado":
            found.append("IPI: não credita, mas livro Tributado")
    return found


def _tes_text(record: TesRecord | None) -> str:
    if record is None:
        return ""
    return f"TES {record.code} ({record.description}): Calcula ICMS {record.calculates_icms}, Credita ICMS {record.credits_icms}, livro {record.icms_book}."


def _eligible(enabled: bool, issuer_state: str, crt: str, cfop: str) -> bool:
    return enabled and issuer_state == PRESUMED["state"] and crt == "1" and cfop[:1] == "5" and cfop[1:] in INDUSTRY_SUFFIXES


def _simple_band(rate: float, annex: str) -> tuple[float, float | None]:
    table = ANNEX[annex]
    percent = rate / 100
    cap = (table[-1][1] - table[-1][2] / table[-1][0]) * table[-1][3]
    if percent > cap + 0.00005:
        return cap * 100, None
    lower = 0
    for limit, nominal, deduction, share in table:
        floor = (nominal - deduction / lower) * share if lower else nominal * share
        ceiling = (nominal - deduction / limit) * share
        if percent <= ceiling + 0.00005:
            if deduction == 0 or percent <= floor:
                return cap * 100, (lower + limit) / 2 if deduction == 0 else lower
            return cap * 100, deduction / (nominal - percent / share)
        lower = limit
    return cap * 100, SUBLIMIT


def _fuel(item: XmlItem) -> bool:
    return item.ncm.startswith(FUEL_NCM) or item.cfop[1:] in FUEL_SUFFIXES or item.cst == "61"


def _nature(cfop: str) -> str:
    suffix = cfop[1:]
    return next((name for name, suffixes in NATURE.items() if suffix in suffixes), "")


def _excluded_kind(row) -> str:
    if row["species"] in EXCLUDED_BY_SPECIES:
        return EXCLUDED_BY_SPECIES[row["species"]]
    return EXCLUDED_BY_SUFFIX.get(row["cfop"][1:], OTHER_EXCLUDED)


def _simple_credit(document: XmlDocument) -> float:
    return round(sum(item.simple_credit for item in document.items), 2)


def _ipi_from_items(document: XmlDocument) -> float:
    return round(sum(item.ipi_amount for item in document.items), 2)


def _cst_list(document: XmlDocument) -> str:
    return ", ".join(sorted({item.cst or item.csosn for item in document.items}))


def _state_digit(state: str, company_state: str) -> str:
    return "3" if state == "EX" else ("1" if state == company_state else "2")


def _document_key(branch: str, number: str, series: str, supplier: str, store: str) -> str:
    return "|".join([branch, str(number).lstrip("0"), str(series).lstrip("0"), supplier, store])


def _check_digit(key: str) -> bool:
    if len(key) != 44 or not key.isdigit():
        return False
    total, weight = 0, 2
    for digit in reversed(key[:43]):
        total += int(digit) * weight
        weight = 2 if weight == 9 else weight + 1
    check = 11 - total % 11
    return (0 if check >= 10 else check) == int(key[43])


def _series(value: str) -> str:
    return (value or "").strip().upper().lstrip("0") or "0"


def _digits(value: str) -> str:
    return "".join(character for character in (value or "") if character.isdigit())


def _cnpj(value: str) -> str:
    digits = _digits(value)
    if len(digits) != 14:
        return digits
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def _as_int(value: str) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _item_number(value: str) -> int:
    parsed = _as_int(value)
    return parsed or 0


def _brl(value: float) -> str:
    return f"{value:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def _render(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{float(value):.2f}"
    return str(value).strip()
