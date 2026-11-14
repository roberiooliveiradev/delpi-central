"""Corpus sintético. Cada regra da skill dispara aqui, e em nenhum lugar há dado real."""

from __future__ import annotations

from pathlib import Path

from controllership_finance_app.domain.entry_audit.models import (
    FiscalBookLine,
    ProtheusHeader,
    ProtheusItem,
    TesRecord,
    XmlDocument,
)
from controllership_finance_app.infrastructure.entry_audit.xml_reader import read_xml_paths

COMPANY = "11111111000191"
SUPPLIER = "22222222000191"
OTHER = "33333333000133"
NS = "http://www.portalfiscal.inf.br/nfe"
CT = "http://www.portalfiscal.inf.br/cte"

TES = [
    TesRecord("001", "Compra com credito", "Sim", "Sim", "Tributado", "Nao", "Nao", "Outros", "Nao", "Entrada", "101"),
    TesRecord("002", "Compra sem credito", "Sim", "Nao", "Outros", "Nao", "Nao", "Outros", "Nao", "Entrada", "101"),
    TesRecord("003", "Compra com IPI", "Sim", "Sim", "Tributado", "Sim", "Sim", "Tributado", "Nao", "Entrada", "101"),
    TesRecord("004", "Credito presumido", "Sim", "Sim", "Tributado", "Nao", "Nao", "Outros", "Nao", "Entrada", "101"),
    TesRecord("005", "Consumo com IPI", "Sim", "Nao", "Outros", "Sim", "Sim", "Tributado", "Sim", "Entrada", "556"),
    TesRecord("009", "TES incoerente", "Sim", "Sim", "Isento", "Nao", "Nao", "Outros", "Nao", "Entrada", "101"),
    TesRecord("036", "Frete com credito", "Sim", "Sim", "Tributado", "Nao", "Nao", "Outros", "Nao", "Entrada", "352"),
    TesRecord("037", "Frete sem credito", "Sim", "Nao", "Outros", "Nao", "Nao", "Outros", "Nao", "Entrada", "352"),
]


def access_key(model: str, number: int, cnpj: str = SUPPLIER, series: str = "001") -> str:
    body = f"422611{cnpj}{model}{series}{number:09d}100000001"
    total, weight = 0, 2
    for digit in reversed(body):
        total += int(digit) * weight
        weight = 2 if weight == 9 else weight + 1
    check = 11 - total % 11
    return body + str(0 if check >= 10 else check)


def invalid_key(model: str, number: int) -> str:
    key = access_key(model, number)
    last = str((int(key[-1]) + 1) % 10)
    return key[:-1] + last


def _base(**overrides) -> dict:
    data = dict(
        number=0, side="both", species="SPED", series="1", own="N", state="SC", supplier="000001", store="01",
        tax_id=SUPPLIER, emit=SUPPLIER, emit_name="Fornecedor Sintetico", dest=COMPANY, crt="3", tp="1",
        date="2026-11-12", issue="12/11/2026", received="12/11/2026", cstat="100",
        gross=100, goods=100, icms=12, base=100, ipi=0, ipi_base=0, discount=0, freight=0, expense=0, st=0,
        xml_total=100, xml_goods=100, xml_icms=12, xml_base=100, xml_ipi=0, xml_discount=0, xml_freight=0,
        xml_other=0, xml_st=0, xml_series="1",
        tes="001", cfop="1101", cst="000", item_total=100, item_icms=12, item_base=100, item_rate=12,
        item_ipi=0, item_ipi_base=0, item_st=0, product="", item_no="1",
        xml_cfop="5101", xml_cst="00", xml_origin="0", xml_csosn="", xml_ncm="84818099", xml_rate=12,
        xml_pcred=0, xml_vcred=0, xml_item_ipi=0, xml_item_base_ipi=0, xml_item_st=0, xml_item_discount=0,
        items=None, xml_items=None, key=None, model="55",
    )
    data.update(overrides)
    if not data["product"]:
        data["product"] = f"P{data['number']}"
    return data


def main_specs() -> list[dict]:
    common = dict(item_total=100, item_icms=12, gross=100, goods=100, icms=12, xml_total=100, xml_goods=100, xml_icms=12)
    specs = [
        _base(number=3101, gross=90, goods=70, icms=8.4, base=70, xml_total=70, xml_goods=70, xml_icms=8.4, xml_base=70, item_total=70, item_icms=8.4, item_base=70),
        _base(number=3102, tes="009", icms=10, item_icms=10, xml_icms=0, xml_base=0, item_base=0, item_rate=12),
        _base(number=3103, icms=2, item_icms=2, xml_icms=10),
        _base(number=3104, base=50, xml_base=100, item_base=100),
        _base(number=3105, ipi=0, xml_ipi=10, xml_item_ipi=10, gross=90, xml_total=100, item_ipi=0),
        _base(number=3106, series="9"),
        _base(number=3107, discount=5, xml_discount=0),
        _base(number=3108, freight=10, expense=0, xml_freight=0, xml_other=10),
        _base(number=3109, issue="11/11/2026"),
        _base(number=3110, item_total=80, xml_goods=100, goods=100),
        _base(number=3111, xml_cfop="6101"),
        _base(number=3112, xml_cfop="1101"),
        _base(number=3113, own="S", cfop="5101", xml_cfop="5102"),
        _base(number=3114, xml_cfop="5201"),
        _base(number=3115, xml_cfop="5653"),
        _base(number=3116, xml_cst="60", cst="000"),
        _base(number=3117, cfop="1401"),
        _base(number=3118, xml_origin="1"),
        _base(number=3119, cst="020"),
        _base(number=3120, tes="002", cst="090", icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=4.8),
        _base(number=3121, cst="060", xml_cst="00", xml_ncm="27101234", icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=0, xml_base=0),
        _base(number=3122, tes="002", crt="1", xml_csosn="101", xml_cst="", xml_pcred=1, xml_vcred=4, xml_cfop="5102", cfop="1102", icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=0, xml_base=0),
        _base(number=3124, tes="099", item_ipi=0, xml_item_ipi=5, xml_ipi=5, ipi=0, gross=95, xml_total=100),
        _base(number=3125, tes="003", item_ipi=2, ipi=2, xml_item_ipi=8, xml_ipi=8, gross=92, xml_total=100),
        _base(number=3126, tes="003", item_ipi=5, ipi=5, item_ipi_base=40, xml_item_ipi=5, xml_ipi=5, xml_item_base_ipi=80, gross=105, xml_total=105),
        _base(number=3127, item_st=1, st=1, xml_item_st=4, xml_st=4),
        _base(number=3128, item_rate=18),
        _base(number=3130, state="PR", emit_name="Fornecedor Parana"),
        _base(number=3131, tes="005", cfop="1556", xml_cfop="5556", item_ipi=3, ipi=3, xml_item_ipi=3, xml_ipi=3, icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=0, xml_base=0, gross=103, xml_total=103),
        _base(number=3132, tes="099", cfop="1556", xml_cfop="5556", icms=4, item_icms=4, xml_icms=0, xml_base=0),
        _base(number=3133, side="protheus", tes="099", cst="040", icms=5, item_icms=5),
        _base(number=3134, crt="1", xml_csosn="102", xml_cst="", xml_pcred=20, xml_cfop="5101", icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=0, xml_base=0),
        _base(number=3135, crt="1", xml_csosn="102", xml_cst="", xml_pcred=3.9, xml_cfop="5102", cfop="1102", icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=0, xml_base=0),
        _base(number=3136, crt="1", xml_csosn="101", xml_cst="", xml_pcred=0, icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=0, xml_base=0),
        _base(number=3137, crt="1", xml_csosn="101", xml_cst="", xml_pcred=1, xml_vcred=1, xml_cfop="5101", tes="001", icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=0, xml_base=0),
        _base(number=3138, crt="1", xml_csosn="101", xml_cst="", xml_pcred=4, xml_cfop="5101", tes="004", icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=0, xml_base=0),
        _base(number=3139, crt="1", xml_csosn="101", xml_cst="", xml_pcred=1, xml_cfop="5101", tes="004", icms=1, item_icms=1, item_rate=1, base=100, xml_icms=0, xml_base=0),
        _base(number=3140, tes="004", cfop="1102", xml_cfop="5102"),
        _base(number=3141, side="xml", icms=0, xml_icms=0, xml_base=0),
        _base(number=3142, side="xml", date="2026-11-01", xml_icms=6),
        _base(number=3143, side="xml", cstat="101"),
        _base(number=3144, side="xml", emit=COMPANY, emit_name="Empresa Sintetica", tp="1"),
        _base(number=3145, side="xml", emit=COMPANY, emit_name="Empresa Sintetica", tp="0"),
        _base(number=3146, side="xml", dest=OTHER),
        _base(number=3150, side="protheus", issue="01/10/2026"),
        _base(number=3151, side="protheus"),
        _base(number=3155, side="protheus", key="", species="SPED", items=[]),
        _base(number=3156, side="protheus", key=invalid_key("55", 3156), items=[]),
        _base(number=3157, side="protheus", key=access_key("55", 1), items=[]),
        _base(number=3158, side="protheus", series="7", items=[]),
        _base(number=3159, side="protheus", species="NFCE", items=[]),
        _base(number=3160, tax_id=OTHER),
        _base(number=3161, tes="002", icms=5, item_icms=5, xml_icms=0, xml_base=0, item_base=100),
        _base(number=3162, tes="002", item_rate=18, item_base=50, base=100, xml_base=100),
        _base(number=3163, tes="002", item_ipi=4, ipi=4, xml_item_ipi=1, xml_ipi=1),
        _base(number=3164, side="protheus", species="NFS", items="service"),
        _base(number=3167, model="57", species="CTE", gross=80, xml_total=50, item_total=50, item_icms=6, icms=6, base=50, xml_base=50, xml_icms=6, cfop="1352", tes="036", item_rate=12),
        _base(number=3168, model="57", species="CTE", cfop="2352", tes="036", icms=6, item_icms=6, base=50, item_base=50, item_rate=12, gross=50, xml_total=50, xml_icms=6, xml_base=50),
        _base(number=3169, model="57", species="CTE", tes="036", link=3180, icms=6, item_icms=6, base=50, item_base=50, item_rate=12, gross=50, xml_total=50, xml_icms=6, xml_base=50),
        _base(number=3170, model="57", species="CTE", tes="037", link=3181, icms=0, item_icms=0, item_rate=0, item_base=0, base=0, gross=50, xml_total=50, xml_icms=6, xml_base=50),
        _base(number=3171, model="57", species="CTE", tes="036", link=3181, icms=10, item_icms=10, base=50, item_base=50, item_rate=12, gross=50, xml_total=50, xml_icms=6, xml_base=50),
        _base(number=3172, model="57", species="CTE", tes="036", link=3181, icms=6, item_icms=6, item_rate=18, base=50, item_base=50, gross=50, xml_total=50, xml_icms=6, xml_base=50, xml_rate=12),
        _base(number=3173, model="57", species="CTE", tes="036", link=3181, cst="020", icms=6, item_icms=6, base=50, item_base=50, item_rate=12, gross=50, xml_total=50, xml_icms=6, xml_base=50),
        _base(number=3174, model="57", species="CTE", tes="037", link=3180, cst="000", icms=0, item_icms=0, item_rate=0, item_base=0, base=0, gross=50, xml_total=50, xml_icms=0, xml_base=0),
        _base(number=3175, model="57", species="CTE", tes="009", link=3180, icms=6, item_icms=6, base=50, item_base=50, item_rate=12, gross=50, xml_total=50, xml_icms=6, xml_base=50),
        _base(number=3176, model="57", species="CTE", tes="036", taker=OTHER, icms=6, item_icms=6, base=50, item_base=50, item_rate=12, gross=50, xml_total=50, xml_icms=6, xml_base=50),
        _base(number=3180, cfop="1556", xml_cfop="5556", icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=0, xml_base=0),
        _base(number=3181),
        _base(number=3182, side="xml", model="57", species="CTE", cstat="101"),
        _base(number=3183, side="xml", model="57", species="CTE", taker=OTHER),
        _base(number=3184, side="xml", model="57", species="CTE", taker=COMPANY),
        _base(number=3185, side="protheus", model="57", species="CTE", issue="01/09/2026", items=[]),
        _base(number=3186, side="protheus", model="57", species="CTE", items=[]),
        _base(number=3154, side="protheus", key=access_key("55", 2), gross=80, goods=80, icms=0, items=[]),
        _base(number=3154, side="xml", gross=80, goods=80, xml_total=80, xml_goods=80, xml_icms=0, xml_base=0),
    ]
    specs.append(_base(number=3129, items=[
        dict(item_no="1", cfop="1101", product="WIDGET", total=10, icms=0, base=0, rate=0),
        dict(item_no="2", cfop="1101", product="WIDGET", total=10, icms=0, base=0, rate=0),
        dict(item_no="3", cfop="1556", product="WIDGET", total=10, icms=0, base=0, rate=0),
    ], xml_items=[
        dict(n=1, cfop="5101", amount=10, icms=0, base=0),
        dict(n=2, cfop="5101", amount=10, icms=0, base=0),
        dict(n=3, cfop="5556", amount=10, icms=0, base=0),
    ], gross=30, goods=30, icms=0, base=0, xml_total=30, xml_goods=30, xml_icms=0, xml_base=0))
    specs.append(_base(number=3165, items=[
        dict(item_no="1", total=40, icms=0, base=0, rate=0),
        dict(item_no="2", total=60, icms=0, base=0, rate=0),
    ], xml_items=[dict(n=1, amount=100, icms=0, base=0)], icms=0, item_icms=0, xml_icms=0, xml_base=0, base=0))
    return specs


def header_only_spec() -> list[dict]:
    return [_base(number=3190, icms=0, base=100, xml_icms=12, xml_base=100, items=[])]


def book_specs() -> list[dict]:
    clean = dict(icms=12, item_icms=12, xml_icms=12)
    return [
        _base(number=5001, **clean),
        _base(number=5002, tes="002", icms=0, item_icms=0, item_rate=0, item_base=0, base=0, xml_icms=0, xml_base=0),
        _base(number=5003, **clean),
        _base(number=5004, **clean),
        _base(number=5009, side="protheus", species="NFS", key="", items="service"),
    ]


def book_lines() -> list[FiscalBookLine]:
    return [
        FiscalBookLine("5002", "1", "000001", "01", "1", icms_amount=5, branch="01"),
        FiscalBookLine("5003", "1", "000001", "01", "1", icms_amount=0, branch="01"),
        FiscalBookLine("5004", "1", "000001", "01", "1", icms_amount=8, branch="01"),
    ]


def write_corpus(root: Path, specs: list[dict], *, with_items: bool = True, with_book: bool = False) -> tuple[list[ProtheusHeader], list[ProtheusItem], dict[str, XmlDocument], dict[str, XmlDocument]]:
    xml_dir = root / "xml"
    xml_dir.mkdir(parents=True, exist_ok=True)
    headers, item_rows = [], []
    for spec in specs:
        key = _spec_key(spec)
        if spec["side"] in {"both", "protheus"}:
            headers.append(_header(spec, key))
            item_rows.extend(_item_rows(spec))
        if spec["side"] in {"both", "xml"}:
            path = xml_dir / f"{spec['number']}-{spec['side']}-{spec['model']}.xml"
            path.write_text(_xml(spec, key), encoding="utf-8")
    _write_sf1(root / "sf1.csv", [spec for spec in specs if spec["side"] in {"both", "protheus"}])
    if with_items:
        _write_sd1(root / "sd1.csv", [spec for spec in specs if spec["side"] in {"both", "protheus"}])
    _write_sf4(root / "sf4.csv")
    if with_book:
        _write_sft(root / "sft.csv")
    invoices, ctes, _ignored = read_xml_paths([xml_dir])
    return headers, item_rows, invoices, ctes


def _spec_key(spec: dict) -> str:
    if spec.get("key") is not None:
        return spec["key"]
    cnpj = spec["emit"]
    if spec["model"] == "57":
        cnpj = SUPPLIER
    return access_key(spec["model"], spec["number"], cnpj)


def _header(spec: dict, key: str) -> ProtheusHeader:
    return ProtheusHeader(
        branch="01", number=str(spec["number"]), series=spec["series"], supplier_code=spec["supplier"],
        supplier_store=spec["store"], supplier_name=spec["emit_name"], supplier_state=spec["state"],
        supplier_tax_id=spec["tax_id"], species=spec["species"], own_form=spec["own"], access_key=key,
        issue_date=_br_date(spec["issue"]), received_date=_br_date(spec["received"]),
        freight_amount=spec["freight"], expense_amount=spec["expense"], icms_base=spec["base"],
        icms_amount=spec["icms"], ipi_base=spec["ipi_base"], ipi_amount=spec["ipi"], goods_amount=spec["goods"],
        gross_amount=spec["gross"], discount_amount=spec["discount"], st_base=0, st_amount=spec["st"],
        insurance_amount=0,
    )


def _item_rows(spec: dict) -> list[ProtheusItem]:
    if spec["items"] == []:
        return []
    rows = spec["items"] if isinstance(spec["items"], list) else [dict(
        item_no=spec["item_no"], cfop=spec["cfop"], product=spec["product"], total=spec["item_total"],
        icms=spec["item_icms"], base=spec["item_base"], rate=spec["item_rate"], ipi=spec["item_ipi"],
        ipi_base=spec["item_ipi_base"], st=spec["item_st"], cst=spec["cst"], tes=spec["tes"],
    )]
    if spec["items"] == "service":
        rows = [dict(item_no="1", cfop="1933", product=spec["product"], total=spec["item_total"], icms=0, base=0, rate=0, ipi=0, ipi_base=0, st=0, cst="000", tes="001")]
    built = []
    for row in rows:
        built.append(ProtheusItem(
            branch="01", number=str(spec["number"]), series=spec["series"], supplier_code=spec["supplier"],
            supplier_store=spec["store"], item=str(row["item_no"]), product_code=row.get("product", spec["product"]),
            cfop=row.get("cfop", spec["cfop"]), tax_situation=row.get("cst", spec["cst"]), tes=row.get("tes", spec["tes"]),
            total_amount=row.get("total", spec["item_total"]), icms_base=row.get("base", spec["item_base"]),
            icms_rate=row.get("rate", spec["item_rate"]), icms_amount=row.get("icms", spec["item_icms"]),
            ipi_base=row.get("ipi_base", spec["item_ipi_base"]), ipi_rate=0, ipi_amount=row.get("ipi", spec["item_ipi"]),
            st_amount=row.get("st", spec["item_st"]),
        ))
    return built


def _xml(spec: dict, key: str) -> str:
    if spec["model"] == "57":
        return _cte_xml(spec, key)
    items = spec["xml_items"] or [dict(
        n=1, cfop=spec["xml_cfop"], amount=spec["xml_goods"],
        icms=spec["xml_icms"], base=spec["xml_base"], cst=spec["xml_cst"], origin=spec["xml_origin"],
        csosn=spec["xml_csosn"], ncm=spec["xml_ncm"], rate=spec["xml_rate"], pcred=spec["xml_pcred"],
        vcred=spec["xml_vcred"], ipi=spec["xml_item_ipi"], ipi_base=spec["xml_item_base_ipi"],
        st=spec["xml_item_st"], discount=spec["xml_item_discount"],
    )]
    body = "".join(_det(item) for item in items)
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><nfeProc xmlns="{NS}" versao="4.00"><NFe><infNFe Id="NFe{key}" versao="4.00">'
        f'<ide><cUF>42</cUF><mod>55</mod><serie>{spec["xml_series"]}</serie><nNF>{spec["number"]}</nNF>'
        f'<dhEmi>{spec["date"]}T10:00:00-03:00</dhEmi><tpNF>{spec["tp"]}</tpNF></ide>'
        f'<emit><CNPJ>{spec["emit"]}</CNPJ><xNome>{spec["emit_name"]}</xNome><enderEmit><UF>{spec["state"]}</UF></enderEmit><CRT>{spec["crt"]}</CRT></emit>'
        f'<dest><CNPJ>{spec["dest"]}</CNPJ><enderDest><UF>SC</UF></enderDest></dest>{body}'
        f'<total><ICMSTot><vBC>{spec["xml_base"]:.2f}</vBC><vICMS>{spec["xml_icms"]:.2f}</vICMS><vBCST>0.00</vBCST>'
        f'<vST>{spec["xml_st"]:.2f}</vST><vProd>{spec["xml_goods"]:.2f}</vProd><vFrete>{spec["xml_freight"]:.2f}</vFrete>'
        f'<vSeg>0.00</vSeg><vDesc>{spec["xml_discount"]:.2f}</vDesc><vIPI>{spec["xml_ipi"]:.2f}</vIPI><vOutro>{spec["xml_other"]:.2f}</vOutro>'
        f'<vNF>{spec["xml_total"]:.2f}</vNF></ICMSTot></total></infNFe></NFe>'
        f'<protNFe><infProt><chNFe>{key}</chNFe><cStat>{spec["cstat"]}</cStat></infProt></protNFe></nfeProc>'
    )


def _det(item: dict) -> str:
    if item.get("csosn"):
        tax = f'<ICMSSN101><orig>{item.get("origin", "0")}</orig><CSOSN>{item["csosn"]}</CSOSN><pCredSN>{item.get("pcred", 0):.2f}</pCredSN><vCredICMSSN>{item.get("vcred", 0):.2f}</vCredICMSSN></ICMSSN101>'
    else:
        tax = (
            f'<ICMS00><orig>{item.get("origin", "0")}</orig><CST>{item.get("cst", "00")}</CST><vBC>{item.get("base", 0):.2f}</vBC>'
            f'<pICMS>{item.get("rate", 0):.2f}</pICMS><vICMS>{item.get("icms", 0):.2f}</vICMS><vICMSST>{item.get("st", 0):.2f}</vICMSST></ICMS00>'
        )
    ipi = f'<IPI><IPITrib><CST>00</CST><vBC>{item.get("ipi_base", 0):.2f}</vBC><pIPI>0.00</pIPI><vIPI>{item.get("ipi", 0):.2f}</vIPI></IPITrib></IPI>' if item.get("ipi") else ""
    return (
        f'<det nItem="{item.get("n", 1)}"><prod><cProd>P</cProd><xProd>Peca</xProd><NCM>{item.get("ncm", "84818099")}</NCM>'
        f'<CFOP>{item.get("cfop", "5101")}</CFOP><vProd>{item.get("amount", 0):.2f}</vProd><vDesc>{item.get("discount", 0):.2f}</vDesc></prod>'
        f'<imposto><ICMS>{tax}</ICMS>{ipi}</imposto></det>'
    )


def _cte_xml(spec: dict, key: str) -> str:
    taker = spec.get("taker") or COMPANY
    link = spec.get("link")
    linked = f'<infCTeNorm><infDoc><infNFe><chave>{access_key("55", link)}</chave></infNFe></infDoc></infCTeNorm>' if link else "<infCTeNorm/>"
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><cteProc xmlns="{CT}" versao="4.00"><CTe><infCte Id="CTe{key}" versao="4.00">'
        f'<ide><mod>57</mod><serie>{spec["xml_series"]}</serie><nCT>{spec["number"]}</nCT><dhEmi>{spec["date"]}T11:00:00-03:00</dhEmi>'
        f'<CFOP>5352</CFOP><UFIni>SC</UFIni><UFFim>SC</UFFim><toma3><toma>3</toma></toma3></ide>'
        f'<emit><CNPJ>{SUPPLIER}</CNPJ><xNome>Transportadora Sintetica</xNome><enderEmit><UF>SC</UF></enderEmit><CRT>3</CRT></emit>'
        f'<dest><CNPJ>{taker}</CNPJ><enderDest><UF>SC</UF></enderDest></dest>'
        f'<vPrest><vTPrest>{spec["xml_total"]:.2f}</vTPrest></vPrest>'
        f'<imp><ICMS><ICMS00><CST>{spec["xml_cst"]}</CST><vBC>{spec["xml_base"]:.2f}</vBC><pICMS>{spec["xml_rate"]:.2f}</pICMS><vICMS>{spec["xml_icms"]:.2f}</vICMS></ICMS00></ICMS></imp>'
        f'{linked}</infCte></CTe><protCTe><infProt><cStat>{spec["cstat"]}</cStat></infProt></protCTe></cteProc>'
    )


def _write_sf1(path: Path, specs: list[dict]) -> None:
    rows = []
    for spec in specs:
        key = _spec_key(spec)
        rows.append(["01", str(spec["number"]), spec["series"], spec["supplier"], spec["store"], spec["state"], spec["emit_name"], spec["tax_id"], "N", spec["own"], spec["species"], key, spec["issue"], spec["received"], _n(spec["freight"]), _n(spec["expense"]), _n(spec["base"]), _n(spec["icms"]), _n(spec["ipi_base"]), _n(spec["ipi"]), _n(spec["goods"]), _n(spec["gross"]), _n(spec["discount"]), "0", _n(spec["st"]), "0"])
    _csv(path, ["Filial", "Numero", "Serie", "Fornecedor", "Loja", "Estado", "Nome Forn.", "CNPJ", "Tipo da Nota", "Form. Prop.", "Espec.Docum.", "Chave NFe", "DT Emissao", "Dt. Receb.", "Vlr.Frete", "Vlr.Despesas", "Base p/ICMS", "Vlr.ICMS", "Base p/IPI", "Vlr.IPI", "Vlr.Mercad", "Vlr.Bruto", "Descontos", "Base ICM Sol", "ICMS Solid.", "Vlr.Seguro"], rows)


def _write_sd1(path: Path, specs: list[dict]) -> None:
    rows = []
    for spec in specs:
        for item in _item_rows(spec):
            rows.append(["01", item.number, item.series, item.supplier_code, item.supplier_store, item.cfop, item.tax_situation, item.tes, item.item, item.product_code, "1", _n(item.total_amount), _n(item.total_amount), _n(item.icms_base), _n(item.icms_rate), _n(item.icms_amount), _n(item.ipi_base), "0", _n(item.ipi_amount), _n(item.st_amount), "0", spec["issue"]])
    _csv(path, ["Filial", "Documento", "Serie", "Forn/Cliente", "Loja", "Cod. Fiscal", "Sit.Tribut.", "Tipo Entrada", "Item NF", "Produto", "Quantidade", "Vlr.Unitario", "Vlr.Total", "Base Icms", "Aliq. ICMS", "Vlr.ICMS", "Vlr.Base IPI", "Aliq. IPI", "Vlr.IPI", "ICMS Solid.", "Desconto", "DT Digitacao"], rows)


def _write_sf4(path: Path) -> None:
    rows = [[ "01", record.code, record.description, record.calculates_icms, record.credits_icms, record.icms_book, record.calculates_ipi, record.credits_ipi, record.ipi_book, record.consumption_material, record.tes_type, record.fiscal_code] for record in TES]
    _csv(path, ["Filial", "Cod. do Tipo", "Txt Padrao", "Calcula ICMS", "Cred. ICMS ?", "L.Fisc. ICMS", "Calcula IPI?", "Credita IPI?", "L.Fiscal IPI", "Mat.Consumo", "Tipo do TES", "Cod. Fiscal"], rows)


def _write_sft(path: Path) -> None:
    rows = []
    for line in book_lines():
        rows.append(["01", "E", line.number, line.series, line.supplier_code, line.supplier_store, line.item, _n(line.icms_amount), _n(line.ipi_amount), ""])
    _csv(path, ["Filial", "Tipo Movim.", "Nota Fiscal", "Serie", "Cli/For", "Loja", "Item", "Valor ICMS", "Valor IPI", "Dt. Cancel."], rows)


def _csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    lines = [";".join(header)] + [";".join(row) for row in rows]
    path.write_text("\n".join(lines), encoding="latin-1")


def _n(value: float) -> str:
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def _br_date(value: str):
    day, month, year = value.split("/")
    from datetime import date
    return date(int(year), int(month), int(day))
