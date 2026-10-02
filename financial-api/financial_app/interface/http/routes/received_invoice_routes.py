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
):
    try:
        data = build_received_invoices_service().list_received(
            resolve_user(request),
            invoice_number=invoiceNumber,
            value=value,
            supplier_cnpj=supplierCnpj,
            page=page,
            page_size=pageSize,
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
):
    try:
        payload, filename = build_received_invoices_service().download_danfe(
            resolve_user(request),
            document_id=document_id,
            access_key=accessKey,
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
