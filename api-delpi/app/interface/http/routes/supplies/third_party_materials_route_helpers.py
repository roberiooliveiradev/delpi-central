from __future__ import annotations

from typing import Optional

from fastapi import Query

from app.application.dto.third_party_materials.constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    EXPORT_FORMAT_CSV,
    EXPORT_FORMAT_VALUES,
    MAX_PAGE_SIZE,
)
from app.application.dto.third_party_materials.query_request import (
    ThirdPartyMaterialsQueryRequest,
)
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_REQUIRED,
    THIRD_PARTY_MATERIALS_STATUS_QUERY,
)


def build_query_request(
    *,
    branch: str,
    product: Optional[str] = None,
    customer_reference: Optional[str] = None,
    partner_code: Optional[str] = None,
    partner_store: Optional[str] = None,
    receipt_number: Optional[str] = None,
    return_number: Optional[str] = None,
    issued_from: Optional[str] = None,
    issued_to: Optional[str] = None,
    status: Optional[str] = None,
    only_with_balance: bool = False,
    include_test_products: bool = False,
    page: int = DEFAULT_PAGE,
    page_size: int = DEFAULT_PAGE_SIZE,
    export_format: str = EXPORT_FORMAT_CSV,
) -> ThirdPartyMaterialsQueryRequest:
    return ThirdPartyMaterialsQueryRequest.from_query(
        branch=branch,
        product=product,
        customer_reference=customer_reference,
        partner_code=partner_code,
        partner_store=partner_store,
        receipt_number=receipt_number,
        return_number=return_number,
        issued_from=issued_from,
        issued_to=issued_to,
        status=status,
        only_with_balance=only_with_balance,
        include_test_products=include_test_products,
        page=page,
        page_size=page_size,
        export_format=export_format,
    )


def BRANCH_QUERY():
    return BRANCH_QUERY_REQUIRED()


def PRODUCT_QUERY():
    return Query(None, description="Product code (SB1/SB6).")


def CUSTOMER_REFERENCE_QUERY():
    return Query(
        None,
        description="Customer reference (SB1.B1_REFEREN / Ref. Cliente). Prefix match.",
    )


def PARTNER_CODE_QUERY():
    return Query(None, description="Customer code (SA1).")


def PARTNER_STORE_QUERY():
    return Query(None, description="Customer store (SA1 loja).")


def RECEIPT_NUMBER_QUERY():
    return Query(None, description="Inbound receipt invoice number.")


def RETURN_NUMBER_QUERY():
    return Query(None, description="Return invoice number.")


def ISSUED_FROM_QUERY():
    return Query(None, description="Shipment issue date from (YYYY-MM-DD, inclusive).")


def ISSUED_TO_QUERY():
    return Query(None, description="Shipment issue date to (YYYY-MM-DD, inclusive).")


def STATUS_QUERY():
    return THIRD_PARTY_MATERIALS_STATUS_QUERY()


def ONLY_WITH_BALANCE_QUERY():
    return Query(False, description="When true, only shipments with pending balance.")


def INCLUDE_TEST_PRODUCTS_QUERY():
    return Query(False, description="When true, include configured test product codes.")


def PAGE_QUERY():
    return Query(DEFAULT_PAGE, ge=1, description="Page number (minimum 1).")


def PAGE_SIZE_QUERY():
    return Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Page size (maximum {MAX_PAGE_SIZE}).",
    )


def EXPORT_FORMAT_QUERY():
    return Query(
        EXPORT_FORMAT_CSV,
        description="Export format: csv or xlsx.",
        enum=list(EXPORT_FORMAT_VALUES),
        pattern="^(csv|xlsx)$",
    )
