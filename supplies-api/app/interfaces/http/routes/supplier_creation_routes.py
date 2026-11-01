"""Supplier creation preview — CNPJ-assisted prefill (X4.UX-R1.S1).

Read-only composition: external registry (suggestions + provenance) and the
api-delpi exact ``tax_id`` duplicate check. Never persists — no supplier
POST/PUT, no review record, no mirror of the external payload.
"""

from __future__ import annotations

from typing import Any

from flask import Blueprint, g, jsonify, request

from app.application.security.supplies_permissions import can_use_operations
from app.application.services.supplier_creation_preview.preview_service import (
    SupplierCreationPreviewService,
)
from app.application.services.supplier_enrichment.contracts import (
    classify_registry_error,
)
from app.application.services.suppliers_dto import (
    project_existing_supplier_item,
    SUPPLIER_EXISTING_PAGE_SIZE_MAX,
)
from app.domain.supplier_creation.preview import is_valid_cnpj
from app.domain.supplier_enrichment.models import digits_only
from app.infrastructure.gateways.brasilapi_registry_provider import (
    registry_rate_limiter,
)
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.delpi_supplier_duplicate_search import (
    DelpiSupplierDuplicateSearch,
)
from app.infrastructure.gateways.supplier_enrichment_adapters import (
    company_registry_provider,
)
from app.interfaces.http.auth_decorators import require_policy
from app.interfaces.http.routes.suppliers_routes import (
    _access_token,
    _gateway_error_response,
)

creation_bp = Blueprint("supplier_creation", __name__)

_REQUEST_FIELDS = frozenset({"tax_id"})


def _service() -> SupplierCreationPreviewService:
    return SupplierCreationPreviewService(
        registry_provider=company_registry_provider(),
        duplicate_search=DelpiSupplierDuplicateSearch(),
    )


def _require_body(body: Any) -> str:
    if not isinstance(body, dict):
        raise ValueError("request body must be a JSON object")
    unknown = set(body) - _REQUEST_FIELDS
    if unknown:
        raise ValueError(
            "unexpected fields are not accepted: " + ", ".join(sorted(unknown))
        )
    digits = digits_only(body.get("tax_id"))
    if not is_valid_cnpj(digits):
        raise ValueError("tax_id must be a valid 14-digit CNPJ")
    return digits


def _error(exc: Exception):
    classified = classify_registry_error(exc)
    if classified is not None:
        status, code, retry_after = classified
        response = jsonify({"detail": str(exc), "code": code})
        if retry_after:
            response.headers["Retry-After"] = str(retry_after)
        return response, status
    if isinstance(exc, ValueError):
        return jsonify({"detail": str(exc), "code": "invalid_request"}), 422
    if isinstance(exc, DelpiApiGatewayError):
        return _gateway_error_response(exc)
    raise exc


@creation_bp.get("/suppliers/existing-suppliers")
@require_policy(can_use_operations)
def list_existing_suppliers():
    """operationId: list_existing_suppliers_by_tax_id — read-only paging.

    Paginates the exact ``tax_id`` canonical lookup in api-delpi so the MFE
    can list every existing record for a CNPJ without re-hitting the
    external registry. Same capability as the preview — no new permission.
    """
    try:
        digits = digits_only(request.args.get("tax_id"))
        if not is_valid_cnpj(digits):
            raise ValueError("tax_id must be a valid 14-digit CNPJ")
        try:
            page = max(1, int(request.args.get("page") or 1))
            page_size = min(
                SUPPLIER_EXISTING_PAGE_SIZE_MAX,
                max(1, int(request.args.get("page_size") or 10)),
            )
        except (TypeError, ValueError):
            raise ValueError("page and page_size must be integers") from None
        items, total = DelpiSupplierDuplicateSearch().search_by_tax_id(
            digits,
            access_token=_access_token(),
            page=page,
            page_size=page_size,
        )
        return jsonify(
            {
                "items": [
                    project_existing_supplier_item(i) for i in items
                ],
                "page": page,
                "page_size": page_size,
                "total": total,
            }
        ), 200
    except Exception as exc:
        return _error(exc)


@creation_bp.post("/suppliers/creation-preview")
@require_policy(can_use_operations)
def create_supplier_creation_preview():
    """operationId: create_supplier_creation_preview — draft-only preview.

    Returns suggestions with provenance and an honest duplicate-check status;
    performs no write of any kind.
    """
    try:
        tax_id = _require_body(request.get_json(silent=True) or {})
        registry_rate_limiter().acquire("actor", str(g.current_user.id))
        return jsonify(
            _service().preview(tax_id, access_token=_access_token())
        ), 200
    except Exception as exc:
        return _error(exc)
