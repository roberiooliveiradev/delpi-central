"""Regressão GLPI #1567: valores do Financeiro, rateio e meta em Suprimentos."""
from decimal import Decimal

from app.application.services.supplies.freight_impact_service import (
    compose_freight_impact,
    freight_settings,
    to_financial_link,
)


def link(
    invoice: str,
    goods: float,
    cte: str,
    gross: float,
    *,
    in_filter: bool = True,
    branch: str = "01",
    freight_found: bool = True,
) -> dict:
    return {
        "branch": branch,
        "in_filter": in_filter,
        "invoice_found": True,
        "invoice_document": invoice,
        "invoice_series": "1",
        "supplier_code": "000001",
        "supplier_store": "01",
        "supplier_name": "Fornecedor",
        "invoice_goods_value": goods,
        "invoice_issue_date": "2026-11-03",
        "invoice_entry_date": "2026-11-04",
        "freight_found": freight_found,
        "freight_document": cte,
        "freight_series": "1",
        "carrier_code": "000002",
        "carrier_store": "01",
        "carrier_name": "Transportadora",
        "freight_gross_value": gross if freight_found else None,
        "freight_issue_date": "2026-11-05",
        "freight_document_type": "N",
        "freight_document_kind": "CTE",
        "freight_access_key": "A" * 44,
    }


def compose(links: list[dict], *, situation="all", branches=None):
    return compose_freight_impact(
        links,
        branches=branches or ["01"],
        date_from="2026-11-01",
        date_to="2026-11-30",
        situation=situation,
        page=1,
        page_size=25,
    )


def test_meta_matriz_e_filial_copiadas_da_configuracao_financeira():
    cfg = freight_settings()
    assert cfg["branchLimits"] == {"01": "3.25", "02": "4.25"}
    assert cfg["normalFreightKind"] == "CTE"


def test_rateio_fecha_com_nota_fora_do_filtro_e_multiplos_ctes():
    result = compose([
        link("NFA", 1000, "CT1", 300),
        link("NFB", 2000, "CT1", 300, in_filter=False),
        link("NFA", 1000, "CT2", 12),
        link("NFC", 1000, "CT3", 20),
    ])
    # CT1: 300 * 1000/3000 = 100; CT2: 12. Nenhuma duplicação.
    a = next(nf for nf in result["items"] if nf["invoice_document"] == "NFA")
    assert a["goods_value"] == "1000.00"
    assert a["freight_total"] == "112.00"
    assert a["freight_pct"] == "11.20"
    assert a["freight_limit"] == "3.25"
    assert a["situation"] == "above_limit"
    assert a["cte_count"] == 2
    assert [ct["allocated_value"] for ct in a["allocations"]] == ["100.00", "12.00"]
    assert a["allocations"][0]["allocation_base"] == "3000.00"
    assert a["allocations"][0]["linked_invoice_count"] == 2
    assert not any(nf["invoice_document"] == "NFB" for nf in result["items"])
    assert result["summary"]["purchases_total"] == "2000.00"
    assert result["summary"]["freight_total"] == "132.00"
    assert result["summary"]["freight_pct"] == "6.60"
    assert result["summary"]["above_limit_count"] == 1


def test_igual_ao_limite_nao_e_acima_e_meta_filial_02():
    # 42.50 de frete sobre 1000 = 4,25%, exatamente a meta.
    response = compose([link("002", 1000, "CT2", 42.5, branch="02")], branches=["02"])
    item = response["items"][0]
    assert item["freight_pct"] == "4.25"
    assert item["freight_limit"] == "4.25"
    assert item["situation"] == "normal"
    assert response["limits"]["02"] == "4.25"


def test_inconsistencia_nao_finge_frete_zero_nem_mascara_resumo():
    payload = compose([
        link("001", 1000, "CT1", 50),
        link("002", 1000, "CT2", 0, freight_found=False),
    ], situation="inconsistent")
    assert payload["summary"]["inconsistent_count"] == 1
    assert payload["summary"]["freight_total"] == "50.00"
    assert payload["summary"]["purchases_total"] == "1000.00"
    assert payload["total"] == 1
    item = payload["items"][0]
    assert item["invoice_document"] == "002"
    assert item["situation"] == "inconsistent"
    assert "cte_not_found" in item["reason_codes"]


def test_decimal_arredondamento_e_situacao_respeitam_financeiro():
    # Financeiro usa ROUND_HALF_UP e compara o percentual exibido.
    payload = compose([link("001", 1000, "CT3", 32.5)])
    assert payload["items"][0]["freight_pct"] == "3.25"
    assert payload["items"][0]["situation"] == "normal"
    assert to_financial_link(link("001", 1000, "CT3", 32.5)).goods_value == Decimal("1000.00")
    assert payload["method"] == "financial_freight_allocation_v1"


def test_situacao_invalida_falha_fechado():
    try:
        compose([link("001", 1000, "CT1", 50)], situation="undefined")
    except ValueError:
        pass
    else:
        raise AssertionError("situation must be validated before query")
