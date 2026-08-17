"""BFF propostas-documento (ADY) — RBAC commercial; proxy api-delpi."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_PROPOSALS_EXPORT_PERMISSIONS,
    COMMERCIAL_PROPOSALS_VIEW_PERMISSIONS,
)
from commercial_app.composition.commercial_composer import build_delpi_commercial_gateway
from commercial_app.core.responses import fail, ok
from commercial_app.interface.http.routes.totvs_bff_helpers import unwrap_gateway_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposal-documents", tags=["Proposal documents BFF"])


@router.get("/", operation_id="bff_list_proposal_documents")
@require_any_permission(*COMMERCIAL_PROPOSALS_VIEW_PERMISSIONS)
def list_proposal_documents(
    _request: Request,
    limit: int = Query(default=100, ge=1, le=500),
):
    try:
        payload = build_delpi_commercial_gateway().get_commercial_proposal_document(
            "",
            params={"limit": limit},
        )
        return ok(
            unwrap_gateway_data(payload),
            message="Propostas documento carregadas.",
            operation_id="bff_list_proposal_documents",
        )
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id="bff_list_proposal_documents")
    except Exception:
        logger.exception("bff_list_proposal_documents_failed")
        return fail(
            "Erro interno ao listar propostas documento.",
            500,
            operation_id="bff_list_proposal_documents",
        )


@router.get("/{proposta_interna}", operation_id="bff_get_proposal_document")
@require_any_permission(*COMMERCIAL_PROPOSALS_VIEW_PERMISSIONS)
def get_proposal_document(_request: Request, proposta_interna: str):
    try:
        payload = build_delpi_commercial_gateway().get_commercial_proposal_document(
            f"/{proposta_interna.strip()}",
        )
        return ok(
            unwrap_gateway_data(payload),
            message="Proposta documento carregada.",
            operation_id="bff_get_proposal_document",
        )
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id="bff_get_proposal_document")
    except Exception:
        logger.exception("bff_get_proposal_document_failed")
        return fail(
            "Erro interno ao carregar proposta documento.",
            500,
            operation_id="bff_get_proposal_document",
        )


def _pdf_response(content: bytes, filename: str | None) -> Response:
    headers = {}
    if filename:
        headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return Response(content=content, media_type="application/pdf", headers=headers)


@router.get("/{proposta_interna}/pdf", operation_id="bff_get_proposal_document_pdf")
@require_any_permission(*COMMERCIAL_PROPOSALS_EXPORT_PERMISSIONS)
def get_proposal_document_pdf(_request: Request, proposta_interna: str):
    try:
        content, filename = (
            build_delpi_commercial_gateway().get_commercial_proposal_document_pdf(
                proposta_interna
            )
        )
        return _pdf_response(content, filename)
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id="bff_get_proposal_document_pdf")
    except Exception:
        logger.exception("bff_get_proposal_document_pdf_failed")
        return fail(
            "Erro interno ao exportar PDF.",
            500,
            operation_id="bff_get_proposal_document_pdf",
        )


@router.post("/{proposta_interna}/pdf", operation_id="bff_post_proposal_document_pdf")
@require_any_permission(*COMMERCIAL_PROPOSALS_EXPORT_PERMISSIONS)
async def post_proposal_document_pdf(request: Request, proposta_interna: str):
    try:
        body = await request.json()
        if not isinstance(body, dict):
            body = {}
        content, filename = (
            build_delpi_commercial_gateway().post_commercial_proposal_document_pdf(
                proposta_interna, payload=body
            )
        )
        return _pdf_response(content, filename)
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id="bff_post_proposal_document_pdf")
    except Exception:
        logger.exception("bff_post_proposal_document_pdf_failed")
        return fail(
            "Erro interno ao exportar PDF.",
            500,
            operation_id="bff_post_proposal_document_pdf",
        )
