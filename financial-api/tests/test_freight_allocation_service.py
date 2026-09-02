"""Os 14 casos obrigatórios do rateio de frete."""

from __future__ import annotations

from decimal import Decimal

from financial_app.domain.services.freight_allocation_service import (
    REASON_BRANCH_WITHOUT_LIMIT,
    REASON_CTE_GROSS_VALUE_NOT_POSITIVE,
    REASON_CTE_NOT_FOUND,
    REASON_CTE_WITHOUT_VALID_BASE,
    REASON_DUPLICATED_LINK,
    REASON_NF_GOODS_VALUE_NOT_POSITIVE,
    REASON_NF_NOT_FOUND,
    REASON_SPECIAL_OR_UNKNOWN_CTE,
    SITUATION_ABOVE_LIMIT,
    SITUATION_INCONSISTENT,
    SITUATION_NORMAL,
    FreightAllocationService,
    FreightLink,
)

BRANCH_LIMITS = {"01": Decimal("3.25"), "02": Decimal("4.25")}
SPECIAL_KINDS = ("CTEOS", "CTM", "NFS", "CA")


def link(
    *,
    branch: str = "01",
    invoice_document: str = "000000001",
    goods_value: str | None = "1000.00",
    freight_document: str = "000000900",
    freight_gross_value: str | None = "32.50",
    in_filter: bool = True,
    invoice_found: bool = True,
    freight_found: bool = True,
    freight_document_type: str = "N",
    freight_document_kind: str = "CTE",
    supplier_code: str = "001992",
    invoice_series: str = "1",
) -> FreightLink:
    return FreightLink(
        branch=branch,
        in_filter=in_filter,
        invoice_found=invoice_found,
        invoice_document=invoice_document,
        invoice_series=invoice_series,
        supplier_code=supplier_code,
        supplier_store="03",
        supplier_name="FORNECEDOR X",
        goods_value=Decimal(goods_value) if goods_value is not None else None,
        invoice_issue_date="2026-03-10",
        invoice_entry_date="2026-03-12",
        freight_found=freight_found,
        freight_document=freight_document,
        freight_series="1",
        carrier_code="003686",
        carrier_store="01",
        carrier_name="TRANSPORTADORA Y",
        freight_gross_value=(
            Decimal(freight_gross_value) if freight_gross_value is not None else None
        ),
        freight_issue_date="2026-03-11",
        freight_document_type=freight_document_type,
        freight_document_kind=freight_document_kind,
    )


def allocate(links, *, branch_limits=None):
    return FreightAllocationService().allocate(
        links,
        branch_limits=branch_limits if branch_limits is not None else BRANCH_LIMITS,
        special_freight_kinds=SPECIAL_KINDS,
    )


def reason_codes(result) -> set[str]:
    return {item.reason_code for item in result.inconsistencies}


# 1 -------------------------------------------------------------------------
def test_freight_document_with_a_single_invoice_allocates_the_whole_gross() -> None:
    result = allocate([link(goods_value="1000.00", freight_gross_value="32.50")])

    invoice = result.invoices[0]
    assert invoice.freight_total == Decimal("32.50")
    assert invoice.freight_percent == Decimal("3.25")
    assert invoice.situation == SITUATION_NORMAL
    assert not result.inconsistencies


# 2 -------------------------------------------------------------------------
def test_freight_document_with_several_invoices_splits_by_goods_value() -> None:
    result = allocate(
        [
            link(invoice_document="000000001", goods_value="1000.00"),
            link(invoice_document="000000002", goods_value="3000.00"),
        ]
    )

    by_document = {item.invoice_document: item for item in result.invoices}
    assert by_document["000000001"].freight_total == Decimal("8.13")
    assert by_document["000000002"].freight_total == Decimal("24.37")
    assert sum(item.freight_total for item in result.invoices) == Decimal("32.50")


# 3 -------------------------------------------------------------------------
def test_invoice_with_several_freight_documents_sums_every_allocation() -> None:
    result = allocate(
        [
            link(freight_document="000000900", freight_gross_value="20.00"),
            link(freight_document="000000901", freight_gross_value="12.50"),
        ]
    )

    invoice = result.invoices[0]
    assert len(invoice.allocations) == 2
    assert invoice.freight_total == Decimal("32.50")
    assert invoice.freight_percent == Decimal("3.25")


# 4 -------------------------------------------------------------------------
def test_allocation_closes_exactly_on_the_freight_gross_value() -> None:
    """Igualdade exata em Decimal: nenhum centavo pode evaporar no rateio."""
    result = allocate(
        [
            link(invoice_document="000000001", goods_value="333.33"),
            link(invoice_document="000000002", goods_value="333.33"),
            link(invoice_document="000000003", goods_value="333.34"),
        ]
    )

    allocated = sum(item.freight_total for item in result.invoices)
    assert allocated == Decimal("32.50")


# 5 -------------------------------------------------------------------------
def test_residual_lands_on_the_invoice_with_the_largest_goods_value() -> None:
    result = allocate(
        [
            link(invoice_document="000000001", goods_value="100.00"),
            link(invoice_document="000000002", goods_value="100.00"),
            link(invoice_document="000000003", goods_value="100.00"),
            link(invoice_document="000000004", goods_value="700.00"),
        ]
    )

    by_document = {item.invoice_document: item for item in result.invoices}
    even_share = (Decimal("32.50") * Decimal("100.00") / Decimal("1000.00")).quantize(
        Decimal("0.01")
    )
    assert by_document["000000001"].freight_total == even_share
    assert sum(item.freight_total for item in result.invoices) == Decimal("32.50")
    assert by_document["000000004"].freight_total == Decimal("32.50") - even_share * 3


# 6 -------------------------------------------------------------------------
def test_percentage_equal_to_the_limit_does_not_raise_an_alert() -> None:
    result = allocate([link(goods_value="1000.00", freight_gross_value="32.50")])

    assert result.invoices[0].freight_percent == Decimal("3.25")
    assert result.invoices[0].situation == SITUATION_NORMAL


# 7 -------------------------------------------------------------------------
def test_percentage_above_the_limit_raises_an_alert() -> None:
    result = allocate([link(goods_value="1000.00", freight_gross_value="33.00")])

    assert result.invoices[0].freight_percent == Decimal("3.30")
    assert result.invoices[0].situation == SITUATION_ABOVE_LIMIT


def test_alert_follows_the_percentage_the_screen_shows() -> None:
    """3,251% exibe 3,25% e não é destacado — a tela não se contradiz."""
    result = allocate([link(goods_value="1000.00", freight_gross_value="32.51")])

    assert result.invoices[0].freight_percent == Decimal("3.25")
    assert result.invoices[0].situation == SITUATION_NORMAL


# 8 -------------------------------------------------------------------------
def test_branch_01_uses_the_three_and_a_quarter_limit() -> None:
    inside = allocate([link(branch="01", freight_gross_value="32.00")])
    outside = allocate([link(branch="01", freight_gross_value="40.00")])

    assert inside.invoices[0].freight_limit == Decimal("3.25")
    assert inside.invoices[0].situation == SITUATION_NORMAL
    assert outside.invoices[0].situation == SITUATION_ABOVE_LIMIT


# 9 -------------------------------------------------------------------------
def test_branch_02_uses_the_four_and_a_quarter_limit() -> None:
    inside = allocate([link(branch="02", freight_gross_value="42.00")])
    outside = allocate([link(branch="02", freight_gross_value="43.00")])

    assert inside.invoices[0].freight_limit == Decimal("4.25")
    assert inside.invoices[0].freight_percent == Decimal("4.20")
    assert inside.invoices[0].situation == SITUATION_NORMAL
    assert outside.invoices[0].freight_percent == Decimal("4.30")
    assert outside.invoices[0].situation == SITUATION_ABOVE_LIMIT


# 10 ------------------------------------------------------------------------
def test_invoice_without_goods_value_is_flagged_instead_of_divided_by_zero() -> None:
    result = allocate([link(goods_value="0.00")])

    invoice = result.invoices[0]
    assert invoice.freight_percent is None
    assert invoice.situation == SITUATION_INCONSISTENT
    assert REASON_NF_GOODS_VALUE_NOT_POSITIVE in reason_codes(result)
    assert REASON_CTE_WITHOUT_VALID_BASE in reason_codes(result)


# 11 ------------------------------------------------------------------------
def test_duplicated_link_is_counted_once_and_reported() -> None:
    result = allocate([link(), link()])

    assert len(result.invoices) == 1
    assert result.invoices[0].freight_total == Decimal("32.50")
    assert REASON_DUPLICATED_LINK in reason_codes(result)
    assert result.invoices[0].situation == SITUATION_INCONSISTENT


# 12 ------------------------------------------------------------------------
def test_missing_invoice_or_freight_document_is_reported_not_hidden() -> None:
    orphan_invoice = allocate(
        [link(invoice_found=False, goods_value=None, invoice_document="")]
    )
    assert orphan_invoice.invoices == []
    assert REASON_NF_NOT_FOUND in reason_codes(orphan_invoice)

    orphan_freight = allocate(
        [link(freight_found=False, freight_gross_value=None)]
    )
    assert REASON_CTE_NOT_FOUND in reason_codes(orphan_freight)
    assert orphan_freight.invoices[0].situation == SITUATION_INCONSISTENT
    assert orphan_freight.invoices[0].freight_total == Decimal("0")


# 13 ------------------------------------------------------------------------
def test_logically_deleted_document_arrives_as_not_found() -> None:
    """D_E_L_E_T_ é filtrado no SQL, então o vínculo chega sem o documento."""
    result = allocate([link(invoice_found=False, goods_value=None)])

    assert result.invoices == []
    assert reason_codes(result) == {REASON_NF_NOT_FOUND, REASON_CTE_WITHOUT_VALID_BASE}


# 14 ------------------------------------------------------------------------
def test_out_of_filter_invoice_feeds_the_base_without_entering_the_grid() -> None:
    """Fecho da base: a NF fora do filtro divide o CT-e, mas não é listada."""
    result = allocate(
        [
            link(invoice_document="000000001", goods_value="1000.00", in_filter=True),
            link(invoice_document="000000002", goods_value="1000.00", in_filter=False),
        ]
    )

    assert [item.invoice_document for item in result.invoices] == ["000000001"]
    assert result.invoices[0].freight_total == Decimal("16.25")
    assert result.invoices[0].allocations[0].allocation_base == Decimal("2000.00")
    assert result.invoices[0].allocations[0].linked_invoice_count == 2


# extras ------------------------------------------------------------------
def test_freight_without_gross_value_is_flagged() -> None:
    result = allocate([link(freight_gross_value="0.00")])

    assert REASON_CTE_GROSS_VALUE_NOT_POSITIVE in reason_codes(result)
    assert result.invoices[0].situation == SITUATION_INCONSISTENT


def test_special_freight_kind_is_not_allocated() -> None:
    result = allocate([link(freight_document_kind="CTEOS")])

    assert REASON_SPECIAL_OR_UNKNOWN_CTE in reason_codes(result)
    assert result.invoices[0].freight_total == Decimal("0")


def test_branch_without_configured_limit_is_flagged() -> None:
    result = allocate([link(branch="09")])

    assert REASON_BRANCH_WITHOUT_LIMIT in reason_codes(result)
    assert result.invoices[0].freight_limit is None
    assert result.invoices[0].situation == SITUATION_INCONSISTENT
