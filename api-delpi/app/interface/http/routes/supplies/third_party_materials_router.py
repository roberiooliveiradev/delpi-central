"""Rotas — materiais de terceiros / beneficiamento."""

from __future__ import annotations

from fastapi import APIRouter
from app.interface.http.pagination_query import PAGE_SIZE_QUERY
from fastapi.responses import StreamingResponse

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    THIRD_PARTY_MATERIALS_EXPORT_PERMISSIONS,
    THIRD_PARTY_MATERIALS_READ_PERMISSIONS,
)
from app.composition.third_party_materials_composer import (
    build_export_third_party_materials_returns_use_case,
    build_get_third_party_materials_shipment_use_case,
    build_get_third_party_materials_summary_use_case,
    build_list_third_party_materials_shipments_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response, not_found_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.supplies.third_party_materials_branch_access import (
    branch_access_error,
)
from app.interface.http.routes.supplies.third_party_materials_route_helpers import (
    BRANCH_QUERY,
    CUSTOMER_REFERENCE_QUERY,
    EXPORT_FORMAT_QUERY,
    INCLUDE_TEST_PRODUCTS_QUERY,
    ISSUED_FROM_QUERY,
    ISSUED_TO_QUERY,
    ONLY_WITH_BALANCE_QUERY,
    PAGE_QUERY,
        PARTNER_CODE_QUERY,
    PARTNER_STORE_QUERY,
    PRODUCT_QUERY,
    RECEIPT_NUMBER_QUERY,
    RETURN_NUMBER_QUERY,
    STATUS_QUERY,
    build_query_request,
)
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/third-party-materials",
    tags=["Suprimentos — Materiais de terceiros"],
)

_SHIPMENT_FIELDS = {
    "shipment_recno": {"label": "Recno da remessa", "type": "integer"},
    "shipment_id": {"label": "Identidade da remessa", "type": "string"},
    "branch": {"label": "Filial", "type": "string"},
    "received_quantity": {"label": "Qtd. recebida", "type": "number"},
    "returned_quantity": {"label": "Qtd. devolvida", "type": "number"},
    "pending_balance": {"label": "Saldo a entregar", "type": "number"},
    "status": {"label": "Status", "type": "string"},
}

_SUMMARY_FIELDS = {
    "total_shipments": {"label": "Remessas", "type": "integer"},
    "open_shipments": {"label": "Remessas abertas", "type": "integer"},
    "partial_shipments": {"label": "Remessas parciais", "type": "integer"},
    "no_return_shipments": {"label": "Sem retorno", "type": "integer"},
    "pending_balance": {"label": "Saldo pendente", "type": "number"},
}


def _handle_db_error(context: str, exc: Exception):
    if isinstance(exc, DatabaseConnectionError):
        log_error(f"Erro de banco ao {context}: {exc}")
        return error_response(
            f"Erro de conexão com o banco ao {context}.",
            status_code=503,
        )
    log_error(f"Erro ao {context}: {exc}")
    return error_response(f"Erro interno ao {context}.", status_code=500)


@router.get(
    "/shipments",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_third_party_materials_shipments",
        path="/supplies/third-party-materials/shipments",
    ),
)
@require_any_permission(THIRD_PARTY_MATERIALS_READ_PERMISSIONS)
def get_supplies_third_party_materials_shipments(
    branch: str = BRANCH_QUERY(),
    product: str | None = PRODUCT_QUERY(),
    customer_reference: str | None = CUSTOMER_REFERENCE_QUERY(),
    partner_code: str | None = PARTNER_CODE_QUERY(),
    partner_store: str | None = PARTNER_STORE_QUERY(),
    receipt_number: str | None = RECEIPT_NUMBER_QUERY(),
    return_number: str | None = RETURN_NUMBER_QUERY(),
    issued_from: str | None = ISSUED_FROM_QUERY(),
    issued_to: str | None = ISSUED_TO_QUERY(),
    status: str | None = STATUS_QUERY(),
    only_with_balance: bool = ONLY_WITH_BALANCE_QUERY(),
    include_test_products: bool = INCLUDE_TEST_PRODUCTS_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = PAGE_SIZE_QUERY("page_20_100"),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error
    try:
        request = build_query_request(
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
        )
        result = build_list_third_party_materials_shipments_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_third_party_materials_shipments",
            message="Remessas de materiais de terceiros listadas com sucesso.",
            fields=_SHIPMENT_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao listar remessas de materiais de terceiros: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        return _handle_db_error("listar remessas de materiais de terceiros", exc)


@router.get(
    "/shipments/{shipment_recno}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_third_party_materials_shipment",
        path="/supplies/third-party-materials/shipments/{shipment_recno}",
    ),
)
@require_any_permission(THIRD_PARTY_MATERIALS_READ_PERMISSIONS)
def get_supplies_third_party_materials_shipment(
    shipment_recno: int,
    branch: str = BRANCH_QUERY(),
    include_test_products: bool = INCLUDE_TEST_PRODUCTS_QUERY(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error
    try:
        result = build_get_third_party_materials_shipment_use_case().execute(
            shipment_recno=shipment_recno,
            branch=branch,
            include_test_products=include_test_products,
        )
        if result is None:
            return not_found_response("Remessa não encontrada.")
        return api_delpi_success(
            result,
            operation_id="get_supplies_third_party_materials_shipment",
            message="Remessa de materiais de terceiros carregada com sucesso.",
            fields=_SHIPMENT_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar remessa de materiais de terceiros: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        return _handle_db_error("carregar remessa de materiais de terceiros", exc)


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_supplies_third_party_materials_summary",
        path="/supplies/third-party-materials/summary",
    ),
)
@require_any_permission(THIRD_PARTY_MATERIALS_READ_PERMISSIONS)
def get_supplies_third_party_materials_summary(
    branch: str = BRANCH_QUERY(),
    product: str | None = PRODUCT_QUERY(),
    customer_reference: str | None = CUSTOMER_REFERENCE_QUERY(),
    partner_code: str | None = PARTNER_CODE_QUERY(),
    partner_store: str | None = PARTNER_STORE_QUERY(),
    receipt_number: str | None = RECEIPT_NUMBER_QUERY(),
    return_number: str | None = RETURN_NUMBER_QUERY(),
    issued_from: str | None = ISSUED_FROM_QUERY(),
    issued_to: str | None = ISSUED_TO_QUERY(),
    status: str | None = STATUS_QUERY(),
    only_with_balance: bool = ONLY_WITH_BALANCE_QUERY(),
    include_test_products: bool = INCLUDE_TEST_PRODUCTS_QUERY(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error
    try:
        request = build_query_request(
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
        )
        result = build_get_third_party_materials_summary_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="get_supplies_third_party_materials_summary",
            message="Resumo de materiais de terceiros carregado com sucesso.",
            fields=_SUMMARY_FIELDS,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao resumir materiais de terceiros: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        return _handle_db_error("resumir materiais de terceiros", exc)


@router.get(
    "/returns/export",
    **OpenApiAgentMetadataBuilder.from_contract(
        "export_supplies_third_party_materials_returns",
        path="/supplies/third-party-materials/returns/export",
    ),
)
@require_any_permission(THIRD_PARTY_MATERIALS_EXPORT_PERMISSIONS)
def export_supplies_third_party_materials_returns(
    branch: str = BRANCH_QUERY(),
    product: str | None = PRODUCT_QUERY(),
    customer_reference: str | None = CUSTOMER_REFERENCE_QUERY(),
    partner_code: str | None = PARTNER_CODE_QUERY(),
    partner_store: str | None = PARTNER_STORE_QUERY(),
    receipt_number: str | None = RECEIPT_NUMBER_QUERY(),
    return_number: str | None = RETURN_NUMBER_QUERY(),
    issued_from: str | None = ISSUED_FROM_QUERY(),
    issued_to: str | None = ISSUED_TO_QUERY(),
    status: str | None = STATUS_QUERY(),
    only_with_balance: bool = ONLY_WITH_BALANCE_QUERY(),
    include_test_products: bool = INCLUDE_TEST_PRODUCTS_QUERY(),
    export_format: str = EXPORT_FORMAT_QUERY(),
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error
    try:
        request = build_query_request(
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
            export_format=export_format,
        )
        result = build_export_third_party_materials_returns_use_case().execute(request)
        return StreamingResponse(
            result["stream"],
            media_type=result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"',
                "X-Exported-Count": str(result["exported_count"]),
                "X-Export-Notice": (
                    "Saldo da remessa se repete em cada linha de retorno."
                ),
            },
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao exportar retornos de materiais de terceiros: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        return _handle_db_error("exportar retornos de materiais de terceiros", exc)
