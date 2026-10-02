from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from financial_app.composition.financial_composer import build_received_invoices_service
from financial_app.core.responses import ok
from financial_app.interface.http.auth_http import resolve_user
from financial_app.interface.http.error_responses import domain_error_response

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("/received")
def list_received_invoices(
    request: Request,
    invoiceNumber: str | None = Query(None),
    value: str | None = Query(None),
    supplierCnpj: str | None = Query(None),
    page: int = Query(1),
    pageSize: int = Query(25),
    documentType: str | None = Query(None),
):
    try:
        data = build_received_invoices_service().list_received(
            resolve_user(request),
            invoice_number=invoiceNumber,
            value=value,
            supplier_cnpj=supplierCnpj,
            page=page,
            page_size=pageSize,
            document_type=documentType,
        )
    except Exception as exc:
        mapped = domain_error_response(exc)
        if mapped is not None:
            return mapped
        raise
    return ok(data, message="Notas fiscais de entrada carregadas.")


@router.get("/received/{document_id}/danfe")
def download_received_invoice_danfe(
    request: Request,
    document_id: str,
    accessKey: str = Query(""),
    branch: str = Query(""),
):
    try:
        payload, filename = build_received_invoices_service().download_danfe(
            resolve_user(request),
            document_id=document_id,
            access_key=accessKey,
            branch_code=branch,
        )
    except Exception as exc:
        mapped = domain_error_response(exc)
        if mapped is not None:
            return mapped
        raise
    return Response(
        content=payload,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/received/{document_id}/xml/{variant}")
def download_received_nfse_xml(
    request: Request,
    document_id: str,
    variant: str,
    branch: str = Query(""),
    documentType: str = Query("nfse"),
):
    if (documentType or "").strip().lower() != "nfse":
        from financial_app.domain.errors import InvalidReceivedInvoiceQuery

        mapped = domain_error_response(
            InvalidReceivedInvoiceQuery("O download de XML está disponível para NFS-e.")
        )
        return mapped
    try:
        payload, filename = build_received_invoices_service().download_nfse_xml(
            resolve_user(request),
            document_id=document_id,
            variant=variant,
            branch_code=branch,
        )
    except Exception as exc:
        mapped = domain_error_response(exc)
        if mapped is not None:
            return mapped
        raise
    return Response(
        content=payload,
        media_type="text/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/received/{document_id}/detail")
def received_nfse_detail(
    request: Request,
    document_id: str,
    branch: str = Query(""),
    documentType: str = Query("nfse"),
):
    if (documentType or "").strip().lower() != "nfse":
        from financial_app.domain.errors import InvalidReceivedInvoiceQuery

        return domain_error_response(
            InvalidReceivedInvoiceQuery("O detalhe estruturado está disponível para NFS-e.")
        )
    try:
        data = build_received_invoices_service().nfse_standard_detail(
            resolve_user(request),
            document_id=document_id,
            branch_code=branch,
        )
    except Exception as exc:
        mapped = domain_error_response(exc)
        if mapped is not None:
            return mapped
        raise
    return ok(data, message="Dados da NFS-e carregados.")
