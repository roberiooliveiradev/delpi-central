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
    EnrichmentSourceUnavailableError,
    RegistryAccessDeniedError,
    RegistryLimiterUnavailableError,
    RegistryRateLimitedError,
    RegistryResponseInvalidError,
    RegistryTaxIdInvalidError,
    RegistryTaxIdNotFoundError,
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
    if isinstance(exc, RegistryTaxIdNotFoundError):
        return jsonify(
            {"detail": str(exc), "code": "ENRICHMENT_REGISTRY_TAX_ID_NOT_FOUND"}
        ), 404
    if isinstance(exc, RegistryTaxIdInvalidError):
        return jsonify(
            {"detail": str(exc), "code": "ENRICHMENT_REGISTRY_INVALID_TAX_ID"}
        ), 422
    if isinstance(exc, RegistryRateLimitedError):
        response = jsonify(
            {"detail": str(exc), "code": "ENRICHMENT_RATE_LIMITED"}
        )
        if exc.retry_after:
            response.headers["Retry-After"] = str(exc.retry_after)
        return response, 429
    if isinstance(exc, RegistryLimiterUnavailableError):
        return jsonify(
            {"detail": str(exc), "code": "ENRICHMENT_RATE_LIMITER_UNAVAILABLE"}
        ), 503
    if isinstance(exc, RegistryResponseInvalidError):
        return jsonify(
            {"detail": str(exc), "code": "ENRICHMENT_REGISTRY_INVALID_RESPONSE"}
        ), 502
    if isinstance(exc, RegistryAccessDeniedError | EnrichmentSourceUnavailableError):
        return jsonify(
            {"detail": str(exc), "code": "ENRICHMENT_SOURCE_UNAVAILABLE"}
        ), 503
    if isinstance(exc, ValueError):
        return jsonify({"detail": str(exc), "code": "invalid_request"}), 422
    if isinstance(exc, DelpiApiGatewayError):
        return _gateway_error_response(exc)
    raise exc


_EXISTING_PAGE_SIZE_MAX = 50


def _existing_suppliers_minimal(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "supplier_code": item.get("supplier_code"),
        "supplier_store": item.get("supplier_store"),
        "supplier_name": item.get("supplier_name"),
        "state": item.get("state"),
        "blocked": item.get("blocked"),
    }


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
                _EXISTING_PAGE_SIZE_MAX,
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
                "items": [_existing_suppliers_minimal(i) for i in items],
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
