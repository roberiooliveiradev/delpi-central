"""SURI MCP tool bridge — parity with the Flask BFF authorization path.

Every handler re-derives the ``EffectiveUser`` from the canonical
``delpi_auth`` context (already JWT-validated, RBAC-loaded by the
transport middleware) and re-applies the exact policies the HTTP routes
use: ``can_use_operations``, ``require_unit(s)`` and the same
``DelpiApiGateway`` call. Nothing here grants, weakens or duplicates
business authorization.
"""

from __future__ import annotations

import hashlib
import json
import re
import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from delpi_mcp.avatar_image import (
    approved_avatar_path,
    avatar_filename,
    avatar_mime,
    build_avatar_delivery,
)
from delpi_mcp.errors import kind_for_http_status, mcp_tool_result
from delpi_mcp.identity import require_mcp_context
from mcp.types import CallToolResult
from pydantic import BaseModel, ValidationError

from app.application.security.supplies_permissions import (
    can_administer,
    can_export_purchase_requests,
    can_use_analytics,
    can_use_market_intelligence,
    can_use_operations,
    can_enter_shell,
    can_use_purchase_requests,
    has_canonical_access,
    has_canonical_manage,
)
from app.application.services.authorization_service import AuthorizationService
from app.application.services.requester_identity_service import (
    RequesterIdentityService,
)
from app.application.services.inventory_stock_balances_service import (
    InventoryStockBalancesService,
)
from app.application.services.late_deliveries_composition_service import (
    LateDeliveriesCompositionService,
)
from app.application.services.safety_stock_service import (
    SafetyStockService,
)
from app.application.services.market_intelligence_service import (
    MarketDataNotFoundError,
    MarketIntelligenceService,
)
from app.application.services.capability_resolution_service import (
    CapabilityResolutionService,
)
from app.application.services.preferences_service import PreferencesService
from app.application.services.user_profile_service import UserProfileService
from app.application.services.comex_analysis_service import (
    ComexAnalysisService,
    ComexConflictError,
    ComexForbiddenError,
    ComexNotFoundError,
    ComexValidationError,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.application.services.otd_aggregate_service import OtdAggregateService
from app.application.services.otd_series_service import OtdSeriesService
from app.application.services.procurement_diagnostic_service import (
    ProcurementDiagnosticService,
)
from app.application.services.overview_composition_service import (
    OverviewCompositionService,
    normalize_overview_branches,
)
from app.application.services.supplier_creation_preview.preview_service import (
    SupplierCreationPreviewService,
)
from app.application.services.supplier_enrichment.contracts import (
    classify_registry_error,
)
from app.application.services.suppliers_dto import (
    normalize_operation_id,
    normalize_postal_code,
    normalize_supplier_id,
    project_detail,
    project_existing_supplier_item,
    project_integration_status,
    project_list_envelope,
    project_operation,
    project_postal_lookup,
    SUPPLIER_CATALOG_KINDS,
    SUPPLIER_CATALOG_LIMIT_MAX,
    SUPPLIER_EXISTING_PAGE_SIZE_MAX,
)
from app.domain.entities import EffectiveUser
from app.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CoreApiUnavailableError,
)
from app.domain.supplier_creation.preview import is_valid_cnpj
from app.domain.supplier_enrichment.models import digits_only
from app.infrastructure.gateways.brasilapi_registry_provider import (
    registry_rate_limiter,
)
from app.infrastructure.gateways.delpi_api_gateway import (
    DelpiApiGateway,
    DelpiApiGatewayError,
)
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.infrastructure.gateways.delpi_s2s_gateway import DelpiS2SApiGateway
from app.infrastructure.gateways.delpi_supplier_duplicate_search import (
    DelpiSupplierDuplicateSearch,
)
from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGateway,
    PurchaseRequestsGatewayError,
)
from app.infrastructure.gateways.supplier_enrichment_adapters import (
    company_registry_provider,
)
from app.interfaces.mcp import (
    comex_execute,
    enrichment_execute,
    knowledge,
    personal_execute,
    supplier_execute,
)
from app.interfaces.mcp.branding import (
    SURI_ACRONYM,
    SURI_FULL_NAME,
    SURI_MISSION,
)
from app.interfaces.mcp.constants import (
    PROCUREMENT_DIAGNOSTIC_FILTER_KEYS,
    ANALYSIS_KINDS,
    CATALOG_VERSION,
    CONTEXT_ACTIONS,
    DEFAULT_KNOWLEDGE_LIMIT,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SAMPLE_SIZE,
    EXECUTE_ACTIONS_BY_ENTITY,
    EXECUTE_ENTITIES,
    KNOWLEDGE_ACTIONS,
    MAX_EXECUTE_OPERATIONS,
    MAX_KNOWLEDGE_LIMIT,
    MAX_PAGE_SIZE,
    MAX_SAMPLE_SIZE,
    PO_ANALYZE_FILTER_KEYS,
    PO_EXPORT_FILTER_KEYS,
    PO_GET_IDENTITY_KEYS,
    PO_SEARCH_FILTER_KEYS,
    POSTAL_CODE_IDENTITY_KEYS,
    PR_COST_CENTERS_FILTER_KEYS,
    PR_DETAIL_FILTER_KEYS,
    PR_EXPORT_FILTER_KEYS,
    PR_GET_IDENTITY_KEYS,
    PR_REQUESTERS_FILTER_KEYS,
    PR_SEARCH_FILTER_KEYS,
    PR_SUMMARY_FILTER_KEYS,
DELIVERIES_LATE_FILTER_KEYS,
    INVENTORY_ITEMS_FILTER_KEYS,
    INVENTORY_SUMMARY_FILTER_KEYS,
    SESSION_CAPABILITIES_KEYS,
    SESSION_PREFERENCES_KEYS,
    USERS_IDENTITY_KEYS,
    USERS_PROFILE_KEYS,
    USERS_PHOTO_KEYS,
    USERS_RELATED_KEYS,
    COMEX_IDENTITY_KEYS,
    COMEX_NCM_LIST_KEYS,
    COMEX_PRODUCTS_KEYS,
    COMEX_VIEWS_KEYS,
    CONSUMPTION_COMPARISON_FILTER_KEYS,
    CONSUMPTION_DATE_TYPES,
    CONSUMPTION_IDENTITY_KEYS,
    CONSUMPTION_SEARCH_FILTER_KEYS,
    MARKET_COMMON_KEYS,
    MARKET_FILTERS_KEYS,
    MARKET_FX_KEYS,
    MARKET_IMPORT_SERIES_KEYS,
    MARKET_MONTHLY_KEYS,
    MARKET_PRODUCER_PRICE_KEYS,
    MARKET_QUOTE_KEYS,
    MARKET_SERIES_KEYS,
    OTD_AGGREGATE_FILTER_KEYS,
    OTD_SERIES_FILTER_KEYS,
    OVERVIEW_SUMMARY_FILTER_KEYS,
    SAFETY_STOCK_FILTERS_FILTER_KEYS,
    SAFETY_STOCK_ITEM_IDENTITY_KEYS,
    SAFETY_STOCK_ITEMS_FILTER_KEYS,
    SAFETY_STOCK_SUMMARY_FILTER_KEYS,
    READ_ACTIONS_BY_ENTITY,
    READ_ENTITIES,
    SEMANTIC_CAPABILITIES,
    SUPPLIER_CATALOG_FILTER_KEYS,
    SUPPLIER_GET_IDENTITY_KEYS,
    SUPPLIER_OPERATION_IDENTITY_KEYS,
    SUPPLIER_PREVIEW_FILTER_KEYS,
    SUPPLIER_SEARCH_FILTER_KEYS,
    SUPPLIER_TAX_ID_FILTER_KEYS,
    SUPPLIER_WRITE_OPERATION_KEYS,
    TOOL_CLASS,
)
from app.interfaces.mcp.oauth_contract import mcp_www_authenticate_meta

logger = logging.getLogger("supplies-api.suri_mcp")

_GATEWAY = DelpiApiGateway()
_AUTHZ = AuthorizationService()

_ERROR_KIND_BY_CODE = {
    "unauthenticated": "unauthenticated",
    "forbidden": "forbidden",
    "not_found": "not_found",
    "conflict": "conflict",
    "business_rule": "business_rule",
    "validation": "validation",
    "upstream": "upstream",
    "internal": "internal",
    "provider_unreachable": "upstream",
    "provider_error": "upstream",
    "ENRICHMENT_REGISTRY_TAX_ID_NOT_FOUND": "not_found",
    "ENRICHMENT_REGISTRY_INVALID_TAX_ID": "validation",
    "ENRICHMENT_RATE_LIMITED": "conflict",
    "ENRICHMENT_RATE_LIMITER_UNAVAILABLE": "upstream",
    "ENRICHMENT_REGISTRY_INVALID_RESPONSE": "upstream",
    "ENRICHMENT_SOURCE_UNAVAILABLE": "upstream",
}


def _ok(data: Any, message: str = "ok", meta: dict | None = None) -> CallToolResult:
    return mcp_tool_result(
        {"success": True, "message": message, "data": data},
        is_error=False,
        meta=meta,
    )


def _error(
    message: str,
    *,
    status_code: int = 400,
    data: dict | None = None,
    error_code: str | None = None,
) -> CallToolResult:
    err_data = dict(data or {})
    if error_code:
        err_data.setdefault("error_code", error_code)
        err_data.setdefault(
            "error_kind",
            _ERROR_KIND_BY_CODE.get(error_code, "client"),
        )
    payload: dict = {
        "success": False,
        "message": message,
        "data": err_data,
        "status_code": status_code,
    }
    # Owner-declared typed recoverability (delpi_mcp contract): argument
    # validation rejections are repairable by the caller.
    if error_code == "validation":
        payload["code"] = "ARGUMENT_VALIDATION"
        payload["recoverable"] = True
    meta = None
    if status_code == 401:
        meta = mcp_www_authenticate_meta(
            error="invalid_token",
            error_description="Authentication required",
        )
    return mcp_tool_result(
        payload,
        is_error=True,
        meta=meta,
    )


def handle_tool_error(exc: Exception) -> CallToolResult:
    if isinstance(exc, AuthenticationError):
        return _error(
            "Authentication required.", status_code=401, error_code="unauthenticated"
        )
    if isinstance(exc, ValidationError):
        return _error(
            "Invalid tool arguments",
            status_code=422,
            error_code="validation",
        )
    if isinstance(exc, AuthorizationError):
        return _error("Forbidden", status_code=403, error_code="forbidden")
    if isinstance(exc, CoreApiUnavailableError):
        return _error(
            "Authorization service unavailable",
            status_code=503,
            error_code="upstream",
        )
    if isinstance(exc, DelpiApiGatewayError):
        status = exc.status_code or 502
        if status == 404:
            return _error("Not Found", status_code=404, error_code="not_found")
        if status < 500:
            return _error(
                "api-delpi client error",
                status_code=status,
                error_code="validation",
            )
        return _error("api-delpi unavailable", status_code=502, error_code="upstream")
    if isinstance(exc, PurchaseRequestsGatewayError):
        status = exc.status_code or 502
        if status == 401:
            return _error(
                "Authentication required.",
                status_code=401,
                error_code="unauthenticated",
            )
        if status == 403:
            return _error("Forbidden", status_code=403, error_code="forbidden")
        if status == 404:
            message = "Not Found"
            if isinstance(exc.payload, dict) and exc.payload.get("message"):
                message = str(exc.payload["message"])
            return _error(message, status_code=404, error_code="not_found")
        if status < 500:
            detail = "purchase-requests-api client error"
            if isinstance(exc.payload, dict) and exc.payload.get("message"):
                detail = str(exc.payload["message"])
            return _error(detail, status_code=status, error_code="validation")
        return _error(
            "purchase-requests-api unavailable",
            status_code=502,
            error_code="upstream",
        )
    if isinstance(exc, PermissionError):
        msg = str(exc) or "Unauthorized"
        if msg == "Unauthorized":
            return _error(
                "Authentication required.",
                status_code=401,
                error_code="unauthenticated",
            )
        return _error("Forbidden", status_code=403, error_code="forbidden")
    logger.exception("suri_tool_error type=%s", type(exc).__name__)
    return _error("Erro interno da SURI.", status_code=500, error_code="internal")


def _effective_user() -> EffectiveUser:
    """Map the transport-validated delpi_auth context to EffectiveUser.

    The upstream middleware already validated JWT + audience + scopes and
    loaded RBAC via Core ``/me`` — identical source as the Flask
    ``resolve_effective_user`` path. Service principals were already
    rejected at transport; ``principal_type`` is re-checked in depth.
    """
    context = require_mcp_context()
    user_ns = context.user
    if getattr(user_ns, "principal_type", "user") != "user":
        raise AuthorizationError("Forbidden")
    token = str(getattr(user_ns, "access_token", None) or "").strip()
    if not token:
        auth = context.authorization or ""
        token = auth.split(" ", 1)[1].strip() if auth.startswith("Bearer ") else ""
    if not token:
        raise AuthenticationError("Unauthorized")
    return EffectiveUser(
        id=str(getattr(user_ns, "id", "") or ""),
        email=str(getattr(user_ns, "email", "") or ""),
        name=getattr(user_ns, "name", None),
        permissions={
            str(code)
            for code in (getattr(user_ns, "permissions", None) or [])
            if code
        },
        is_superadmin=bool(getattr(user_ns, "is_superadmin", False)),
        access_token=token,
    )


def _operations_user() -> EffectiveUser:
    user = _effective_user()
    if not can_use_operations(user):
        raise AuthorizationError("Forbidden")
    return user


def _clean_branches(branch: Any) -> list[str]:
    if isinstance(branch, str):
        raw = [branch]
    elif isinstance(branch, (list, tuple)):
        raw = list(branch)
    else:
        raw = []
    return [str(item).strip() for item in raw if str(item or "").strip()]


def _filter_params(
    *,
    order_number: str | None,
    product_code: str | None,
    supplier_code: str | None,
    expected_delivery_from: str | None,
    expected_delivery_to: str | None,
    sort_by: str | None,
    sort_dir: str | None,
    late_only: bool,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for key, value in (
        ("order_number", order_number),
        ("product_code", product_code),
        ("supplier_code", supplier_code),
        ("expected_delivery_from", expected_delivery_from),
        ("expected_delivery_to", expected_delivery_to),
        ("sort_by", sort_by),
        ("sort_dir", sort_dir),
    ):
        text = str(value or "").strip()
        if text:
            params[key] = text
    if late_only:
        params["late_only"] = "true"
    return params


def _fetch_purchase_orders(
    user: EffectiveUser,
    *,
    branches: list[str],
    params: dict[str, Any],
) -> dict[str, Any]:
    merged = {"branch": branches, **params}
    payload = _GATEWAY.get(
        "/supplies/purchase-orders",
        access_token=user.access_token or "",
        params=merged,
    )
    data = unwrap_delpi_envelope(payload)
    if not isinstance(data, dict):
        return {"items": [], "total": 0}
    return data


# -- READ / DISCOVERY -----------------------------------------------------


def tool_get_my_context() -> CallToolResult:
    user = _effective_user()
    return _ok(
        {
            "subject": user.id,
            "display_name": user.name or user.email or None,
            "capabilities": {
                "access": has_canonical_access(user),
                "manage": has_canonical_manage(user),
            },
            "allowed_units": _AUTHZ.allowed_units(user),
            "mcp": {"name": "supplies", "catalog_version": CATALOG_VERSION},
        }
    )


def _avatar_asset() -> tuple[Any, Any]:
    """Approved avatar path from the canonical ficha — None when not
    approved or missing (safe fail: no URL/bytes for unapproved assets)."""
    from app.persona.suri_profile import get_suri_profile

    profile = get_suri_profile()
    path = approved_avatar_path(
        profile, Path(__file__).resolve().parents[3]
    )
    return profile, path


def avatar_distribution() -> dict[str, Any] | None:
    """Owner-local HTTPS discovery metadata for the official avatar
    (AVATAR-INLINE-MCP-V1 — same additive key pattern as TÉO/EVA)."""
    profile, path = _avatar_asset()
    if path is None:
        return None
    base = (Settings.PUBLIC_BASE_URL or "").rstrip("/")
    if not base:
        return None
    return {
        "kind": "public_https",
        "url": (
            f"{base}{Settings.ROOT_PATH}/public/characters/"
            f"{profile.identity.character_id}/avatar/{avatar_filename(profile)}"
        ),
        "mime_type": avatar_mime(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def tool_get_avatar() -> CallToolResult:
    """Approved official avatar as MCP ImageContent — narrative asset only,
    never AuthZ (AVATAR-INLINE-MCP-V1)."""
    try:
        _effective_user()
        profile, _ = _avatar_asset()
        delivery = build_avatar_delivery(
            profile, Path(__file__).resolve().parents[3]
        )
        if delivery.data is None:
            return _error(
                "Avatar oficial não aprovado/publicado para este especialista.",
                status_code=404,
                error_code="not_found",
            )
        if delivery.too_large:
            return _ok(
                delivery.data,
                "Avatar excede o limite inline — metadata only.",
            )
        return mcp_tool_result(
            delivery.data,
            is_error=False,
            text=(
                f"Avatar oficial de {delivery.display_name} "
                f"({delivery.data['mime_type']}, "
                f"{delivery.data['bytes']} bytes) — imagem entregue como "
                "bloco image."
            ),
            images=[delivery.image],
        )
    except Exception as exc:
        return handle_tool_error(exc)


def tool_get_catalog() -> CallToolResult:
    _effective_user()
    mcp: dict[str, Any] = {
        "name": "supplies",
        "persona": SURI_FULL_NAME,
        "acronym": SURI_ACRONYM,
        "mission": SURI_MISSION,
        "catalog_version": CATALOG_VERSION,
    }
    distribution = avatar_distribution()
    if distribution:
        mcp["avatar_distribution"] = distribution
    return _ok(
        {
            "mcp": mcp,
            "tools": [
                {"name": name, "tool_class": TOOL_CLASS[name]}
                for name in sorted(TOOL_CLASS)
            ],
            "capabilities": SEMANTIC_CAPABILITIES,
            "limits": {
                "max_page_size": MAX_PAGE_SIZE,
                "max_sample_size": MAX_SAMPLE_SIZE,
                "max_knowledge_limit": MAX_KNOWLEDGE_LIMIT,
                "operational_units": ["01", "02"],
            },
            "directives": [
                "Tool metadata describes semantics; it never authorizes.",
                "READ operations are read-only and mirror the "
                "authorized Portal BFF contracts. Governed write "
                "operations are available only through execute, for "
                "explicitly registered entity/action pairs.",
                "Analysis is deterministic and labeled FACT/CALCULATION/"
                "RECOMMENDATION — recommendations never execute.",
            ],
        }
    )


def tool_list_purchase_orders(
    branch: list[str],
    order_number: str | None = None,
    product_code: str | None = None,
    supplier_code: str | None = None,
    expected_delivery_from: str | None = None,
    expected_delivery_to: str | None = None,
    late_only: bool = False,
    sort_by: str | None = None,
    sort_dir: str | None = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> CallToolResult:
    user = _operations_user()
    branches = _clean_branches(branch)
    _AUTHZ.require_units(user, branches)
    params = _filter_params(
        order_number=order_number,
        product_code=product_code,
        supplier_code=supplier_code,
        expected_delivery_from=expected_delivery_from,
        expected_delivery_to=expected_delivery_to,
        sort_by=sort_by,
        sort_dir=sort_dir,
        late_only=late_only,
    )
    params["page"] = str(max(1, int(page or 1)))
    params["page_size"] = str(
        min(MAX_PAGE_SIZE, max(1, int(page_size or DEFAULT_PAGE_SIZE)))
    )
    data = _fetch_purchase_orders(user, branches=branches, params=params)
    return _ok(data, meta={"delpi/source": "bff:/purchase-orders"})


def tool_get_purchase_order(
    branch: str, order_number: str
) -> CallToolResult:
    user = _operations_user()
    normalized_branch = (branch or "").strip()
    normalized_number = (order_number or "").strip()
    if not normalized_branch or not normalized_number:
        return _error(
            "Invalid purchase order identity",
            status_code=422,
            error_code="validation",
        )
    _AUTHZ.require_unit(user, normalized_branch)
    payload = _GATEWAY.get(
        f"/supplies/purchase-orders/{normalized_branch}/{normalized_number}",
        access_token=user.access_token or "",
    )
    data = unwrap_delpi_envelope(payload)
    if not isinstance(data, dict):
        return _error("Not Found", status_code=404, error_code="not_found")
    return _ok(data, meta={"delpi/source": "bff:/purchase-orders/{branch}/{number}"})


def tool_export_purchase_orders(filters: dict) -> CallToolResult:
    """Filtered open-order dataset — DECISION-G1 export contract.

    Same canonical upstream the BFF XLSX route consumes
    (``/supplies/purchase-orders/export``, no pagination). The MCP
    returns the JSON rows plus artifact metadata; file materialization
    stays Portal-side — no binary/base64/arbitrary link is produced.
    """
    user = _operations_user()
    branches = _clean_branches(filters.get("branch"))
    _AUTHZ.require_units(user, branches)
    params = _filter_params(
        order_number=filters.get("order_number"),
        product_code=filters.get("product_code"),
        supplier_code=filters.get("supplier_code"),
        expected_delivery_from=filters.get("expected_delivery_from"),
        expected_delivery_to=filters.get("expected_delivery_to"),
        sort_by=filters.get("sort_by"),
        sort_dir=filters.get("sort_dir"),
        late_only=bool(filters.get("late_only") or False),
    )
    merged = {"branch": branches, **params}
    payload = _GATEWAY.get(
        "/supplies/purchase-orders/export",
        access_token=user.access_token or "",
        params=merged,
    )
    data = unwrap_delpi_envelope(payload)
    items = data.get("items") if isinstance(data, dict) else []
    if not isinstance(items, list):
        items = []
    return _ok(
        {
            "items": items,
            "export": {
                "format": "json",
                "row_count": len(items),
                "portal_file_formats": ["xlsx"],
            },
        },
        meta={"delpi/source": "bff:/purchase-orders/export"},
    )


# -- PURCHASE REQUESTS READ (rev.5) ----------------------------------------
#
# Same owner chain as the Flask purchase_requests routes:
# PurchaseRequestsGateway (Bearer + internal service identity) →
# purchase-requests-api, with the canonical RequesterIdentityService
# enrichment on list/requesters/detail. No SC create/approve/cancel is
# exposed — the Portal does not offer that workflow through this surface.

_DELIVERIES_SERVICE = LateDeliveriesCompositionService()
_SAFETY_STOCK_SERVICE = SafetyStockService()
_OVERVIEW_SERVICE = OverviewCompositionService()
_OTD_AGG_SERVICE = OtdAggregateService()
_OTD_SERIES_SERVICE = OtdSeriesService()
_PROC_DIAG_SERVICE = ProcurementDiagnosticService()
_MARKET_SERVICE = MarketIntelligenceService()
_COMEX_SERVICE = ComexAnalysisService()
_CAPABILITY_SERVICE = CapabilityResolutionService()
_PREFERENCES_SERVICE = PreferencesService()
_USER_PROFILE_SERVICE = UserProfileService()
_INVENTORY_SERVICE = InventoryStockBalancesService()

_PR_GATEWAY = PurchaseRequestsGateway()
_PR_REQUESTER_IDENTITY = RequesterIdentityService()


def _pr_user() -> EffectiveUser:
    user = _effective_user()
    if not can_use_purchase_requests(user):
        raise AuthorizationError("Forbidden")
    return user


def _pr_export_user() -> EffectiveUser:
    user = _effective_user()
    if not can_export_purchase_requests(user):
        raise AuthorizationError("Forbidden")
    return user


def _pr_query_string(filters: dict, *, drop: frozenset[str]) -> str:
    """Encode the closed filter payload as the owner query string —
    list values become repeated keys, exactly like the BFF forwarding."""
    pairs: list[tuple[str, str]] = []
    for key in sorted(filters):
        if key in drop:
            continue
        value = filters[key]
        if value is None:
            continue
        if isinstance(value, (list, tuple)):
            for item in value:
                text = str(item or "").strip()
                if text:
                    pairs.append((key, text))
        else:
            text = str(value).strip()
            if text:
                pairs.append((key, text))
    return urlencode(pairs, doseq=True)


def _unwrap_pr_data(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload.get("data")
    return payload


def tool_list_purchase_requests(filters: dict) -> CallToolResult:
    user = _pr_user()
    branches = _clean_branches(filters.get("branch"))
    _AUTHZ.require_units(user, branches)
    bounded = dict(filters)
    bounded["page"] = max(1, int(bounded.get("page") or 1))
    bounded["page_size"] = min(
        MAX_PAGE_SIZE, max(1, int(bounded.get("page_size") or DEFAULT_PAGE_SIZE))
    )
    payload = _PR_GATEWAY.list_purchase_requests(
        access_token=user.access_token or "",
        query_string=_pr_query_string(bounded, drop=frozenset()) or None,
    )
    data = _PR_REQUESTER_IDENTITY.enrich_payload(
        _unwrap_pr_data(payload), access_token=user.access_token or ""
    )
    return _ok(data, meta={"delpi/source": "bff:/purchase-requests"})


def tool_purchase_request_summary(filters: dict) -> CallToolResult:
    user = _pr_user()
    branches = _clean_branches(filters.get("branch"))
    _AUTHZ.require_units(user, branches)
    payload = _PR_GATEWAY.get_summary(
        access_token=user.access_token or "",
        query_string=_pr_query_string(filters, drop=frozenset()) or None,
    )
    return _ok(
        _unwrap_pr_data(payload),
        meta={"delpi/source": "bff:/purchase-requests/summary"},
    )


def tool_purchase_request_requesters(filters: dict) -> CallToolResult:
    user = _pr_user()
    branches = _clean_branches(filters.get("branch"))
    _AUTHZ.require_units(user, branches)
    payload = _PR_GATEWAY.list_requesters(
        access_token=user.access_token or "",
        query_string=_pr_query_string(filters, drop=frozenset()) or None,
    )
    data = _PR_REQUESTER_IDENTITY.enrich_payload(
        _unwrap_pr_data(payload), access_token=user.access_token or ""
    )
    return _ok(
        data,
        meta={"delpi/source": "bff:/purchase-requests/requesters"},
    )


def tool_purchase_request_cost_centers(filters: dict) -> CallToolResult:
    user = _pr_user()
    branches = _clean_branches(filters.get("branch"))
    _AUTHZ.require_units(user, branches)
    payload = _PR_GATEWAY.list_cost_centers(
        access_token=user.access_token or "",
        query_string=_pr_query_string(filters, drop=frozenset()) or None,
    )
    return _ok(
        _unwrap_pr_data(payload),
        meta={"delpi/source": "bff:/purchase-requests/cost-centers"},
    )


def tool_get_purchase_request(
    identity: dict, context_filters: dict
) -> CallToolResult:
    user = _pr_user()
    branch = str(identity.get("branch") or "").strip()
    request_number = str(identity.get("request_number") or "").strip()
    if not branch or not request_number:
        return _error(
            "Invalid purchase request identity",
            status_code=422,
            error_code="validation",
        )
    _AUTHZ.require_unit(user, branch)
    payload = _PR_GATEWAY.get_purchase_request(
        access_token=user.access_token or "",
        branch=branch,
        request_number=request_number,
        query_string=_pr_query_string(context_filters, drop=frozenset())
        or None,
    )
    data = _PR_REQUESTER_IDENTITY.enrich_payload(
        _unwrap_pr_data(payload), access_token=user.access_token or ""
    )
    return _ok(
        data,
        meta={"delpi/source": "bff:/purchase-requests/{branch}/{number}"},
    )


def tool_export_purchase_requests(filters: dict) -> CallToolResult:
    """Filtered SC dataset — DECISION-G1 export contract.

    Mirrors the BFF export route: ``can_export_purchase_requests`` +
    unit scope + non-empty branch; pagination and format keys are never
    forwarded. Returns the canonical JSON rows plus artifact metadata —
    CSV/XLSX materialization stays Portal-side.
    """
    user = _pr_export_user()
    branches = _clean_branches(filters.get("branch"))
    if not branches:
        raise AuthorizationError("Forbidden")
    _AUTHZ.require_units(user, branches)
    payload = _PR_GATEWAY.export_purchase_requests(
        access_token=user.access_token or "",
        query_string=_pr_query_string(filters, drop=frozenset()) or None,
    )
    data = _unwrap_pr_data(payload)
    items = data.get("items") if isinstance(data, dict) else []
    if not isinstance(items, list):
        items = []
    return _ok(
        {
            "items": items,
            "export": {
                "format": "json",
                "row_count": len(items),
                "portal_file_formats": ["csv", "xlsx"],
            },
        },
        meta={"delpi/source": "bff:/purchase-requests/export"},
    )


# -- SUPPLIERS READ (rev.4) -------------------------------------------------
#
# Same owner contract as the Flask suppliers routes: the S2S gateway
# authenticates the technical identity with per-operation scopes while the
# caller's own Bearer token is forwarded for actor binding upstream. Every
# projection reuses the canonical suppliers_dto helpers — no parallel
# schema and no invented cadastral fields.

_S2S_GATEWAY = DelpiS2SApiGateway()


def _admin_user() -> EffectiveUser:
    user = _effective_user()
    if not can_administer(user):
        raise AuthorizationError("Forbidden")
    return user


def _supplier_catalog_params(payload: dict) -> dict:
    params = {
        key: str(payload[key]).strip()
        for key in ("query", "state", "code")
        if str(payload.get(key) or "").strip()
    }
    limit = payload.get("limit")
    if limit is not None:
        try:
            params["limit"] = str(
                max(1, min(int(limit), SUPPLIER_CATALOG_LIMIT_MAX))
            )
        except (TypeError, ValueError):
            raise ValueError("invalid 'limit'") from None
    return params


def tool_search_suppliers(filters: dict) -> CallToolResult:
    user = _operations_user()
    params: dict[str, Any] = {}
    for key in ("query", "state", "sort_by", "sort_dir"):
        text = str(filters.get(key) or "").strip()
        if text:
            params[key] = text
    if filters.get("blocked") is not None:
        params["blocked"] = "true" if bool(filters["blocked"]) else "false"
    params["page"] = str(max(1, int(filters.get("page") or 1)))
    params["page_size"] = str(
        min(MAX_PAGE_SIZE, max(1, int(filters.get("page_size") or DEFAULT_PAGE_SIZE)))
    )
    payload = _S2S_GATEWAY.get(
        "/supplies/suppliers",
        access_token=user.access_token or "",
        params=params,
    )
    data = unwrap_delpi_envelope(payload)
    return _ok(
        project_list_envelope(data),
        meta={"delpi/source": "bff:/suppliers"},
    )


def tool_get_supplier(identity: dict) -> CallToolResult:
    user = _operations_user()
    try:
        supplier_id = normalize_supplier_id(
            identity.get("supplier_code"), identity.get("supplier_store")
        )
    except ValueError as exc:
        return _error(str(exc), status_code=422, error_code="validation")
    payload = _S2S_GATEWAY.get(
        f"/integrations/protheus/suppliers/{supplier_id}",
        access_token=user.access_token or "",
    )
    data = unwrap_delpi_envelope(payload)
    return _ok(
        project_detail(data),
        meta={"delpi/source": "bff:/suppliers/{code}/{store}"},
    )


def tool_supplier_catalogs(filters: dict) -> CallToolResult:
    user = _operations_user()
    kind = str(filters.get("kind") or "").strip().lower()
    if kind not in SUPPLIER_CATALOG_KINDS:
        return _invalid(
            f"Unknown supplier catalog: {kind!r}. "
            f"Allowed: {sorted(SUPPLIER_CATALOG_KINDS)}"
        )
    try:
        params = _supplier_catalog_params(filters)
    except ValueError as exc:
        return _error(str(exc), status_code=422, error_code="validation")
    payload = _S2S_GATEWAY.get(
        f"/supplies/supplier-catalogs/{kind}",
        access_token=user.access_token or "",
        params=params,
    )
    return _ok(
        unwrap_delpi_envelope(payload),
        meta={"delpi/source": f"bff:/suppliers/catalogs/{kind}"},
    )


def _tax_id_pages(filters: dict) -> tuple[str, int, int] | CallToolResult:
    digits = digits_only(filters.get("tax_id"))
    if not is_valid_cnpj(digits):
        return _invalid("tax_id must be a valid 14-digit CNPJ")
    try:
        page = max(1, int(filters.get("page") or 1))
        page_size = min(
            SUPPLIER_EXISTING_PAGE_SIZE_MAX,
            max(1, int(filters.get("page_size") or 10)),
        )
    except (TypeError, ValueError):
        return _invalid("page and page_size must be integers")
    return digits, page, page_size


def tool_supplier_search_by_tax_id(filters: dict) -> CallToolResult:
    user = _operations_user()
    parsed = _tax_id_pages(filters)
    if not isinstance(parsed, tuple):
        return parsed
    digits, page, page_size = parsed
    items, total = DelpiSupplierDuplicateSearch().search_by_tax_id(
        digits,
        access_token=user.access_token or "",
        page=page,
        page_size=page_size,
    )
    return _ok(
        {
            "items": [project_existing_supplier_item(i) for i in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        },
        meta={"delpi/source": "bff:/suppliers/existing-suppliers"},
    )


def tool_supplier_existing(filters: dict) -> CallToolResult:
    user = _operations_user()
    parsed = _tax_id_pages(filters)
    if not isinstance(parsed, tuple):
        return parsed
    digits, page, page_size = parsed
    items, total = DelpiSupplierDuplicateSearch().search_by_tax_id(
        digits,
        access_token=user.access_token or "",
        page=page,
        page_size=page_size,
    )
    return _ok(
        {
            "exists": bool(total),
            "total": total,
            "matches": [
                project_existing_supplier_item(i) for i in items[:10]
            ],
        },
        meta={"delpi/source": "bff:/suppliers/existing-suppliers"},
    )


def tool_supplier_operation(identity: dict) -> CallToolResult:
    user = _operations_user()
    try:
        operation_id = normalize_operation_id(identity.get("operation_id"))
    except ValueError as exc:
        return _error(str(exc), status_code=422, error_code="validation")
    payload = _S2S_GATEWAY.get(
        f"/integrations/operations/{operation_id}",
        access_token=user.access_token or "",
    )
    return _ok(
        project_operation(unwrap_delpi_envelope(payload)),
        meta={"delpi/source": "bff:/suppliers/operations/{id}"},
    )


def tool_suppliers_integration_status() -> CallToolResult:
    user = _admin_user()
    payload = _S2S_GATEWAY.get(
        "/integrations/protheus/status",
        access_token=user.access_token or "",
    )
    return _ok(
        project_integration_status(unwrap_delpi_envelope(payload)),
        meta={"delpi/source": "bff:/suppliers/integration-status"},
    )


def tool_postal_code_lookup(identity: dict) -> CallToolResult:
    user = _operations_user()
    try:
        digits = normalize_postal_code(identity.get("postal_code"))
    except ValueError as exc:
        return _error(str(exc), status_code=422, error_code="validation")
    try:
        payload = _S2S_GATEWAY.get(
            f"/addresses/postal-codes/{digits}",
            access_token=user.access_token or "",
        )
    except DelpiApiGatewayError as exc:
        if exc.status_code is None or exc.status_code == 504:
            return _error(
                "Postal address provider unreachable",
                status_code=504,
                error_code="provider_unreachable",
            )
        if exc.status_code == 400:
            return _error("CEP inválido", status_code=422, error_code="validation")
        if exc.status_code in (401, 403):
            raise
        return _error(
            "Postal address provider error",
            status_code=502,
            error_code="provider_error",
        )
    data = unwrap_delpi_envelope(payload) or {}
    return _ok(
        project_postal_lookup(data, digits),
        meta={"delpi/source": "bff:/suppliers/postal-codes/{cep}"},
    )


def tool_analyze_supplier_creation_preview(filters: dict) -> CallToolResult:
    """Registry-assisted pre-registration analysis — strictly read-only.

    Reuses the canonical preview service: external registry suggestions
    with provenance + exact SA2 duplicate check + missing-field report.
    Provider states surface honestly (unavailable → ENRICHMENT_SOURCE_
    UNAVAILABLE, never fabricated cadastral data). ``write_enabled``
    is always false — analysis never writes.
    """
    user = _operations_user()
    digits = digits_only(filters.get("tax_id"))
    if not is_valid_cnpj(digits):
        return _invalid("tax_id must be a valid 14-digit CNPJ")
    service = SupplierCreationPreviewService(
        registry_provider=company_registry_provider(),
        duplicate_search=DelpiSupplierDuplicateSearch(),
    )
    try:
        registry_rate_limiter().acquire("actor", str(user.id))
        data = service.preview(digits, access_token=user.access_token or "")
    except Exception as exc:
        classified = classify_registry_error(exc)
        if classified is None:
            raise
        status, code, retry_after = classified
        err_data = {"retry_after": retry_after} if retry_after else None
        return _error(str(exc), status_code=status, data=err_data, error_code=code)
    return _ok(
        data,
        meta={"delpi/source": "bff:/suppliers/creation-preview"},
    )


# -- KNOWLEDGE (S5) --------------------------------------------------------


def _knowledge_user() -> EffectiveUser:
    user = _effective_user()
    if not has_canonical_access(user):
        raise AuthorizationError("Forbidden")
    return user


def tool_search_supplies_knowledge(
    query: str | None = None,
    topic: str | None = None,
    kind: str | None = None,
    limit: int = 8,
) -> CallToolResult:
    _knowledge_user()
    return _ok(
        knowledge.search_knowledge(
            query=query, topic=topic, kind=kind, limit=limit
        )
    )


def tool_get_knowledge_item(knowledge_id: str) -> CallToolResult:
    _knowledge_user()
    item = knowledge.get_knowledge_item(knowledge_id)
    if item is None:
        return _error("Not Found", status_code=404, error_code="not_found")
    return _ok(item)


def tool_list_knowledge_sources() -> CallToolResult:
    _knowledge_user()
    return _ok(knowledge.list_knowledge_sources())


# -- ANALYSIS (S6) ---------------------------------------------------------


def tool_analyze_purchase_orders(
    branch: list[str],
    order_number: str | None = None,
    product_code: str | None = None,
    supplier_code: str | None = None,
    expected_delivery_from: str | None = None,
    expected_delivery_to: str | None = None,
    late_only: bool = False,
    sample_size: int = 50,
) -> CallToolResult:
    """Deterministic analysis over the governed READ — never a new rule.

    ``summary`` comes from the owner contract (FACT); calculations are
    reproducible derivations over the fetched sample (CALCULATION);
    recommendations are guidance text (RECOMMENDATION), never actions.
    """
    user = _operations_user()
    branches = _clean_branches(branch)
    _AUTHZ.require_units(user, branches)
    params = _filter_params(
        order_number=order_number,
        product_code=product_code,
        supplier_code=supplier_code,
        expected_delivery_from=expected_delivery_from,
        expected_delivery_to=expected_delivery_to,
        sort_by=None,
        sort_dir=None,
        late_only=late_only,
    )
    capped = max(1, min(int(sample_size or 50), MAX_SAMPLE_SIZE))
    params["page"] = "1"
    params["page_size"] = str(capped)
    data = _fetch_purchase_orders(user, branches=branches, params=params)
    items = data.get("items") if isinstance(data.get("items"), list) else []
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}

    facts = [
        {"label": "total_lines", "value": int(summary.get("total_lines") or 0)},
        {
            "label": "total_open_value",
            "value": round(float(summary.get("total_open_value") or 0.0), 2),
        },
        {"label": "late_lines", "value": int(summary.get("late_lines") or 0)},
        {"label": "on_time_lines", "value": int(summary.get("on_time_lines") or 0)},
        {"label": "no_date_lines", "value": int(summary.get("no_date_lines") or 0)},
    ]

    sample_total = len(items)
    sample_late = sum(
        1 for it in items if it.get("delivery_status") == "late"
    )
    sample_no_date = sum(
        1 for it in items if it.get("delivery_status") == "no_date"
    )
    sample_open_value = round(
        sum(float(it.get("open_value") or 0.0) for it in items), 2
    )
    by_branch: dict[str, int] = {}
    for it in items:
        b = str(it.get("branch") or "")
        by_branch[b] = by_branch.get(b, 0) + 1
    calculations = [
        {"label": "sample_size", "value": sample_total},
        {
            "label": "sample_late_share_pct",
            "value": round(sample_late * 100.0 / sample_total, 2)
            if sample_total
            else 0.0,
        },
        {"label": "sample_no_date_lines", "value": sample_no_date},
        {"label": "sample_open_value", "value": sample_open_value},
        {
            "label": "sample_lines_by_branch",
            "value": dict(sorted(by_branch.items())),
        },
        {
            "label": "sample_truncated",
            "value": bool(int(data.get("total") or 0) > sample_total),
        },
        {
            "label": "population_total_lines",
            "value": int(data.get("total") or 0),
        },
        {
            "label": "interpretation",
            "value": (
                "sample_* metrics describe ONLY the fetched sample — "
                "they are NOT population shares; population_* and the "
                "summary facts describe the full filtered universe."
            ),
        },
    ]

    recommendations: list[dict[str, Any]] = []
    if sample_late:
        recommendations.append(
            {
                "label": "prioritize_late_lines",
                "detail": (
                    f"{sample_late} linha(s) atrasada(s) na amostra — "
                    "vale abrir a lista de pedidos filtrada por atraso no "
                    "Portal para encaminhar com os fornecedores."
                ),
            }
        )
    if sample_no_date:
        recommendations.append(
            {
                "label": "review_missing_dates",
                "detail": (
                    f"{sample_no_date} linha(s) sem data prevista — "
                    "revisar o cadastro da entrega no pedido de compra."
                ),
            }
        )
    if not sample_total:
        recommendations.append(
            {
                "label": "no_open_lines",
                "detail": (
                    "Nenhuma linha em aberto no filtro atual — verifique "
                    "se o escopo de unidade e os filtros estão corretos."
                ),
            }
        )

    input_hash = hashlib.sha256(
        json.dumps(
            {
                "branches": branches,
                "params": params,
                "total": data.get("total"),
            },
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()

    return _ok(
        {
            "facts": facts,
            "calculations": calculations,
            "recommendations": recommendations,
            "input_hash": input_hash,
            "sample": {
                "requested": capped,
                "returned": sample_total,
                "total": int(data.get("total") or 0),
            },
        },
        meta={"delpi/source": "bff:/purchase-orders"},
    )


# -- SEMANTIC DISPATCH (contract freeze rev.3) ------------------------------
#
# Public surface = 5 tools. Every accepted (entity, action, analysis)
# combination must map to an implemented, authorized handler above —
# closed enums, closed filter vocabularies, no arbitrary fields.


def _invalid(message: str) -> CallToolResult:
    return _error(message, status_code=422, error_code="validation")


def _unknown_keys(payload: dict, allowed: frozenset[str]) -> set[str]:
    return {str(k) for k in payload} - set(allowed)


def _payload_dict(value: Any) -> dict:
    """Normalize a typed filter model or plain dict to a dict."""
    if value is None:
        return {}
    if isinstance(value, BaseModel):
        return value.model_dump(exclude_none=True, exclude_unset=True)
    if isinstance(value, dict):
        return dict(value)
    return {}


def tool_get_context(action: str = "context") -> CallToolResult:
    """``action=context`` → caller identity/capabilities;
    ``action=catalog`` → semantic capability catalog."""
    normalized = str(action or "").strip() or "context"
    if normalized == "context":
        return tool_get_my_context()
    if normalized == "catalog":
        return tool_get_catalog()
    return _invalid(
        f"Unknown get_context action: {normalized!r}. "
        f"Allowed: {sorted(CONTEXT_ACTIONS)}"
    )


def tool_read(
    entity: str,
    action: str,
    filters: dict | BaseModel | None = None,
    identity: dict | BaseModel | None = None,
) -> CallToolResult:
    """Semantic READ — closed ``(entity, action)`` registry (rev.4)."""
    normalized_entity = str(entity or "").strip()
    if normalized_entity not in READ_ENTITIES:
        return _invalid(
            f"Unknown read entity: {normalized_entity!r}. "
            f"Allowed: {sorted(READ_ENTITIES)}"
        )
    normalized_action = str(action or "").strip()
    allowed = READ_ACTIONS_BY_ENTITY[normalized_entity]
    if normalized_action not in allowed:
        return _invalid(
            f"Unknown read action for {normalized_entity}: "
            f"{normalized_action!r}. Allowed: {sorted(allowed)}"
        )
    filter_payload = _payload_dict(filters)
    identity_payload = _payload_dict(identity)

    if normalized_entity == "suppliers":
        return _dispatch_suppliers_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "purchase_requests":
        return _dispatch_purchase_requests_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "postal_codes":
        return _dispatch_postal_read(
            normalized_action, filter_payload, identity_payload
        )

    if normalized_entity == "deliveries":
        return _dispatch_deliveries_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "inventory":
        return _dispatch_inventory_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "safety_stock":
        return _dispatch_safety_stock_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "otd":
        return _dispatch_otd_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "consumption":
        return _dispatch_consumption_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "market":
        return _dispatch_market_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "comex":
        return _dispatch_comex_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "session":
        return _dispatch_session_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "users":
        return _dispatch_users_read(
            normalized_action, filter_payload, identity_payload
        )
    if normalized_entity == "avatar":
        return tool_get_avatar()

    if normalized_action == "search":
        if identity_payload:
            return _invalid(
                "read action=search does not accept 'identity' — "
                "use action=get for single records."
            )
        unknown = _unknown_keys(filter_payload, PO_SEARCH_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown purchase_orders filters: {sorted(unknown)}. "
                f"Allowed: {sorted(PO_SEARCH_FILTER_KEYS)}"
            )
        return tool_list_purchase_orders(
            branch=filter_payload.get("branch"),
            order_number=filter_payload.get("order_number"),
            product_code=filter_payload.get("product_code"),
            supplier_code=filter_payload.get("supplier_code"),
            expected_delivery_from=filter_payload.get(
                "expected_delivery_from"
            ),
            expected_delivery_to=filter_payload.get("expected_delivery_to"),
            late_only=bool(filter_payload.get("late_only") or False),
            sort_by=filter_payload.get("sort_by"),
            sort_dir=filter_payload.get("sort_dir"),
            page=int(filter_payload.get("page") or 1),
            page_size=int(
                filter_payload.get("page_size") or DEFAULT_PAGE_SIZE
            ),
        )

    if normalized_action == "get":
        if filter_payload:
            return _invalid(
                "read action=get does not accept 'filters' — "
                "use 'identity' {branch, order_number}."
            )
        unknown = _unknown_keys(identity_payload, PO_GET_IDENTITY_KEYS)
        if unknown:
            return _invalid(
                f"Unknown purchase_orders identity keys: {sorted(unknown)}. "
                f"Allowed: {sorted(PO_GET_IDENTITY_KEYS)}"
            )
        return tool_get_purchase_order(
            branch=str(identity_payload.get("branch") or ""),
            order_number=str(identity_payload.get("order_number") or ""),
        )

    if normalized_action == "export":
        if identity_payload:
            return _invalid(
                "read action=export does not accept 'identity' — "
                "use 'filters' for the export scope."
            )
        unknown = _unknown_keys(filter_payload, PO_EXPORT_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown purchase_orders export filters: {sorted(unknown)}. "
                f"Allowed: {sorted(PO_EXPORT_FILTER_KEYS)}"
            )
        return tool_export_purchase_orders(filter_payload)

    return _invalid(
        f"Unknown read action for {normalized_entity}: "
        f"{normalized_action!r}. "
        f"Allowed: {sorted(READ_ACTIONS_BY_ENTITY[normalized_entity])}"
    )


def _dispatch_purchase_requests_read(
    action: str, filter_payload: dict, identity_payload: dict
) -> CallToolResult:
    """Per-action SC dispatch — each action owns a closed vocabulary
    mirroring the purchase-requests-api query contracts."""
    if action == "search":
        if identity_payload:
            return _invalid(
                "read action=search does not accept 'identity' — "
                "use action=get for a single request."
            )
        unknown = _unknown_keys(filter_payload, PR_SEARCH_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown purchase_requests filters: {sorted(unknown)}. "
                f"Allowed: {sorted(PR_SEARCH_FILTER_KEYS)}"
            )
        return tool_list_purchase_requests(filter_payload)

    if action == "summary":
        if identity_payload:
            return _invalid(
                "read action=summary does not accept 'identity'."
            )
        unknown = _unknown_keys(filter_payload, PR_SUMMARY_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown purchase_requests summary filters: "
                f"{sorted(unknown)}. "
                f"Allowed: {sorted(PR_SUMMARY_FILTER_KEYS)}"
            )
        return tool_purchase_request_summary(filter_payload)

    if action == "requesters":
        if identity_payload:
            return _invalid(
                "read action=requesters does not accept 'identity'."
            )
        unknown = _unknown_keys(filter_payload, PR_REQUESTERS_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown purchase_requests requesters filters: "
                f"{sorted(unknown)}. "
                f"Allowed: {sorted(PR_REQUESTERS_FILTER_KEYS)}"
            )
        return tool_purchase_request_requesters(filter_payload)

    if action == "cost_centers":
        if identity_payload:
            return _invalid(
                "read action=cost_centers does not accept 'identity'."
            )
        unknown = _unknown_keys(filter_payload, PR_COST_CENTERS_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown purchase_requests cost_centers filters: "
                f"{sorted(unknown)}. "
                f"Allowed: {sorted(PR_COST_CENTERS_FILTER_KEYS)}"
            )
        return tool_purchase_request_cost_centers(filter_payload)

    if action == "get":
        unknown = _unknown_keys(identity_payload, PR_GET_IDENTITY_KEYS)
        if unknown:
            return _invalid(
                f"Unknown purchase_requests identity keys: "
                f"{sorted(unknown)}. "
                f"Allowed: {sorted(PR_GET_IDENTITY_KEYS)}"
            )
        unknown = _unknown_keys(filter_payload, PR_DETAIL_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown purchase_requests detail context filters: "
                f"{sorted(unknown)}. "
                f"Allowed: {sorted(PR_DETAIL_FILTER_KEYS)}"
            )
        return tool_get_purchase_request(identity_payload, filter_payload)

    if action == "export":
        if identity_payload:
            return _invalid(
                "read action=export does not accept 'identity' — "
                "use 'filters' for the export scope."
            )
        unknown = _unknown_keys(filter_payload, PR_EXPORT_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown purchase_requests export filters: "
                f"{sorted(unknown)}. "
                f"Allowed: {sorted(PR_EXPORT_FILTER_KEYS)}"
            )
        return tool_export_purchase_requests(filter_payload)

    return _invalid(f"Unknown purchase_requests read action: {action!r}.")


def _dispatch_suppliers_read(
    action: str, filter_payload: dict, identity_payload: dict
) -> CallToolResult:
    """Per-action suppliers dispatch — filters/identity contracts frozen
    per action; unknown keys are rejected before any upstream call."""
    if action == "search":
        if identity_payload:
            return _invalid(
                "read action=search does not accept 'identity' — "
                "use action=get for a supplier record."
            )
        unknown = _unknown_keys(filter_payload, SUPPLIER_SEARCH_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown suppliers filters: {sorted(unknown)}. "
                f"Allowed: {sorted(SUPPLIER_SEARCH_FILTER_KEYS)}"
            )
        return tool_search_suppliers(filter_payload)

    if action == "get":
        if filter_payload:
            return _invalid(
                "read action=get does not accept 'filters' — "
                "use 'identity' {supplier_code, supplier_store}."
            )
        unknown = _unknown_keys(identity_payload, SUPPLIER_GET_IDENTITY_KEYS)
        if unknown:
            return _invalid(
                f"Unknown suppliers identity keys: {sorted(unknown)}. "
                f"Allowed: {sorted(SUPPLIER_GET_IDENTITY_KEYS)}"
            )
        return tool_get_supplier(identity_payload)

    if action == "catalogs":
        if identity_payload:
            return _invalid(
                "read action=catalogs does not accept 'identity' — "
                "use 'filters' {kind, ...}."
            )
        unknown = _unknown_keys(filter_payload, SUPPLIER_CATALOG_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown suppliers catalog filters: {sorted(unknown)}. "
                f"Allowed: {sorted(SUPPLIER_CATALOG_FILTER_KEYS)}"
            )
        return tool_supplier_catalogs(filter_payload)

    if action in ("search_by_tax_id", "existing"):
        if identity_payload:
            return _invalid(
                f"read action={action} does not accept 'identity' — "
                "use 'filters' {tax_id, ...}."
            )
        unknown = _unknown_keys(filter_payload, SUPPLIER_TAX_ID_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown suppliers tax_id filters: {sorted(unknown)}. "
                f"Allowed: {sorted(SUPPLIER_TAX_ID_FILTER_KEYS)}"
            )
        if action == "existing":
            return tool_supplier_existing(filter_payload)
        return tool_supplier_search_by_tax_id(filter_payload)

    if action == "operations":
        if filter_payload:
            return _invalid(
                "read action=operations does not accept 'filters' — "
                "use 'identity' {operation_id}."
            )
        unknown = _unknown_keys(
            identity_payload, SUPPLIER_OPERATION_IDENTITY_KEYS
        )
        if unknown:
            return _invalid(
                f"Unknown suppliers operation keys: {sorted(unknown)}. "
                f"Allowed: {sorted(SUPPLIER_OPERATION_IDENTITY_KEYS)}"
            )
        return tool_supplier_operation(identity_payload)

    if action == "integration_status":
        if filter_payload or identity_payload:
            return _invalid(
                "read action=integration_status accepts no parameters."
            )
        return tool_suppliers_integration_status()

    return _invalid(f"Unknown suppliers read action: {action!r}.")


def _dispatch_postal_read(
    action: str, filter_payload: dict, identity_payload: dict
) -> CallToolResult:
    if filter_payload:
        return _invalid(
            "read action=lookup does not accept 'filters' — "
            "use 'identity' {postal_code}."
        )
    unknown = _unknown_keys(identity_payload, POSTAL_CODE_IDENTITY_KEYS)
    if unknown:
        return _invalid(
            f"Unknown postal_codes identity keys: {sorted(unknown)}. "
            f"Allowed: {sorted(POSTAL_CODE_IDENTITY_KEYS)}"
        )
    return tool_postal_code_lookup(identity_payload)


def tool_analyze(
    analysis: str,
    filters: dict | BaseModel | None = None,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
) -> CallToolResult:
    """Semantic ANALYSIS — ``purchase_orders_summary`` and the read-only
    ``supplier_creation_preview`` (rev.4)."""
    normalized = str(analysis or "").strip()
    if normalized not in ANALYSIS_KINDS:
        return _invalid(
            f"Unknown analysis: {normalized!r}. "
            f"Allowed: {sorted(ANALYSIS_KINDS)}"
        )
    filter_payload = _payload_dict(filters)
    if normalized == "procurement_diagnostic":
        unknown = _unknown_keys(
            filter_payload, PROCUREMENT_DIAGNOSTIC_FILTER_KEYS
        )
        if unknown:
            return _invalid(
                f"Unknown procurement_diagnostic filters: "
                f"{sorted(unknown)}. "
                f"Allowed: {sorted(PROCUREMENT_DIAGNOSTIC_FILTER_KEYS)}"
            )
        return tool_procurement_diagnostic(filter_payload)
    if normalized == "overview_summary":
        unknown = _unknown_keys(filter_payload, OVERVIEW_SUMMARY_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown overview_summary filters: {sorted(unknown)}. "
                f"Allowed: {sorted(OVERVIEW_SUMMARY_FILTER_KEYS)}"
            )
        return tool_analyze_overview_summary(filter_payload)
    if normalized == "supplier_creation_preview":
        unknown = _unknown_keys(filter_payload, SUPPLIER_PREVIEW_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown supplier_creation_preview filters: "
                f"{sorted(unknown)}. "
                f"Allowed: {sorted(SUPPLIER_PREVIEW_FILTER_KEYS)}"
            )
        return tool_analyze_supplier_creation_preview(filter_payload)
    unknown = _unknown_keys(filter_payload, PO_ANALYZE_FILTER_KEYS)
    if unknown:
        return _invalid(
            f"Unknown purchase_orders filters: {sorted(unknown)}. "
            f"Allowed: {sorted(PO_ANALYZE_FILTER_KEYS)}"
        )
    return tool_analyze_purchase_orders(
        branch=filter_payload.get("branch"),
        order_number=filter_payload.get("order_number"),
        product_code=filter_payload.get("product_code"),
        supplier_code=filter_payload.get("supplier_code"),
        expected_delivery_from=filter_payload.get("expected_delivery_from"),
        expected_delivery_to=filter_payload.get("expected_delivery_to"),
        late_only=bool(filter_payload.get("late_only") or False),
        sample_size=int(sample_size or DEFAULT_SAMPLE_SIZE),
    )


def tool_knowledge(
    action: str,
    query: str | None = None,
    topic: str | None = None,
    kind: str | None = None,
    knowledge_id: str | None = None,
    limit: int = DEFAULT_KNOWLEDGE_LIMIT,
) -> CallToolResult:
    """Semantic knowledge surface — search/get/sources over the corpus."""
    normalized = str(action or "").strip()
    if normalized == "search":
        if knowledge_id is not None:
            return _invalid(
                "knowledge action=search does not accept 'knowledge_id'."
            )
        return tool_search_supplies_knowledge(
            query=query, topic=topic, kind=kind, limit=limit
        )
    if normalized == "get":
        if query is not None or topic is not None or kind is not None:
            return _invalid(
                "knowledge action=get accepts only 'knowledge_id'."
            )
        if not (knowledge_id or "").strip():
            return _invalid(
                "knowledge action=get requires 'knowledge_id'."
            )
        return tool_get_knowledge_item(knowledge_id)
    if normalized == "sources":
        if query is not None or topic is not None or kind is not None or knowledge_id is not None:
            return _invalid(
                "knowledge action=sources accepts no parameters."
            )
        return tool_list_knowledge_sources()
    return _invalid(
        f"Unknown knowledge action: {normalized!r}. "
        f"Allowed: {sorted(KNOWLEDGE_ACTIONS)}"
    )


# -- EXECUTE (governed writes — rev.3) -------------------------------------


def tool_execute(
    entity: str,
    action: str,
    operations: list | None = None,
) -> CallToolResult:
    """Semantic EXECUTE — closed ``(entity, action)`` registry.

    ``suppliers.create``/``suppliers.update`` delegate to the canonical
    BFF path (``DelpiS2SApiGateway`` + owner DTO contracts). There is no
    generic executor, no arbitrary URL/method and no service-account
    substitution: the caller's own Bearer token authorizes every op.
    """
    normalized_entity = str(entity or "").strip()
    if normalized_entity not in EXECUTE_ENTITIES:
        return _invalid(
            f"Unknown execute entity: {normalized_entity!r}. "
            f"Allowed: {sorted(EXECUTE_ENTITIES)}"
        )
    normalized_action = str(action or "").strip()
    allowed = EXECUTE_ACTIONS_BY_ENTITY[normalized_entity]
    if normalized_action not in allowed:
        return _invalid(
            f"Unknown execute action for {normalized_entity}: "
            f"{normalized_action!r}. Allowed: {sorted(allowed)}"
        )
    # Authorization first — same order as the BFF decorators: the policy
    # runs before any payload handling, on the caller's own identity.
    ops_in = operations or []
    if not isinstance(ops_in, list) or not ops_in:
        return _invalid("execute requires a non-empty 'operations' list.")
    if len(ops_in) > MAX_EXECUTE_OPERATIONS:
        return _invalid(
            f"execute accepts at most {MAX_EXECUTE_OPERATIONS} operations "
            f"per call (received {len(ops_in)})."
        )
    ops = [_payload_dict(item) for item in ops_in]
    if normalized_entity in {"session", "users"}:
        user = _operations_user()
        allowed_keys = personal_execute.PERSONAL_WRITE_KEYS_BY_ACTION[
            normalized_action
        ]
        for index, item in enumerate(ops):
            unknown = _unknown_keys(item, allowed_keys)
            if unknown:
                return _invalid(
                    f"Unknown {normalized_action} operation keys at "
                    f"index {index}: {sorted(unknown)}. Allowed: "
                    f"{sorted(allowed_keys)}"
                )
        data = personal_execute.execute_personal_write(
            user, entity=normalized_entity, action=normalized_action,
            operations=ops,
        )
        return _ok(
            data,
            meta={
                "delpi/source":
                    f"bff:/{normalized_entity}[{normalized_action}]"
            },
        )
    if normalized_entity == "enrichment":
        user = _operations_user()
        allowed_keys = enrichment_execute.ENRICHMENT_WRITE_KEYS_BY_ACTION[
            normalized_action
        ]
        for index, item in enumerate(ops):
            unknown = _unknown_keys(item, allowed_keys)
            if unknown:
                return _invalid(
                    f"Unknown enrichment {normalized_action} operation "
                    f"keys at index {index}: {sorted(unknown)}. "
                    f"Allowed: {sorted(allowed_keys)}"
                )
        data = enrichment_execute.execute_enrichment_write(
            user, action=normalized_action, operations=ops
        )
        return _ok(
            data,
            meta={"delpi/source": f"bff:/enrichment[{normalized_action}]"},
        )
    if normalized_entity == "comex":
        user = _market_user()
        allowed_keys = comex_execute.COMEX_WRITE_KEYS_BY_ACTION[
            normalized_action
        ]
        for index, item in enumerate(ops):
            unknown = _unknown_keys(item, allowed_keys)
            if unknown:
                return _invalid(
                    f"Unknown comex {normalized_action} operation keys at "
                    f"index {index}: {sorted(unknown)}. Allowed: "
                    f"{sorted(allowed_keys)}"
                )
        data = comex_execute.execute_comex_write(
            user, action=normalized_action, operations=ops
        )
        return _ok(
            data,
            meta={"delpi/source": f"bff:/comex[{normalized_action}]"},
        )
    user = _operations_user()
    for index, item in enumerate(ops):
        unknown = _unknown_keys(item, SUPPLIER_WRITE_OPERATION_KEYS)
        if unknown:
            return _invalid(
                f"Unknown operation keys at index {index}: "
                f"{sorted(unknown)}. Allowed: "
                f"{sorted(SUPPLIER_WRITE_OPERATION_KEYS)}"
            )
    data = supplier_execute.execute_supplier_write(
        user, action=normalized_action, operations=ops
    )
    return _ok(
        data,
        meta={"delpi/source": f"bff:/suppliers[{normalized_action}]"},
    )

def _dispatch_deliveries_read(
    action: str, filters: dict, identity: dict
) -> CallToolResult:
    if identity:
        return _invalid("read(deliveries) does not accept 'identity'.")
    unknown = _unknown_keys(filters, DELIVERIES_LATE_FILTER_KEYS)
    if unknown:
        return _invalid(
            f"Unknown deliveries filters: {sorted(unknown)}. "
            f"Allowed: {sorted(DELIVERIES_LATE_FILTER_KEYS)}"
        )
    return tool_deliveries_late(filters)


def _dispatch_inventory_read(
    action: str, filters: dict, identity: dict
) -> CallToolResult:
    if identity:
        return _invalid("read(inventory) does not accept 'identity'.")
    if action == "summary":
        unknown = _unknown_keys(filters, INVENTORY_SUMMARY_FILTER_KEYS)
        if unknown:
            return _invalid(
                f"Unknown inventory summary filters: {sorted(unknown)}. "
                f"Allowed: {sorted(INVENTORY_SUMMARY_FILTER_KEYS)}"
            )
        return tool_inventory_summary(filters)
    unknown = _unknown_keys(filters, INVENTORY_ITEMS_FILTER_KEYS)
    if unknown:
        return _invalid(
            f"Unknown inventory items filters: {sorted(unknown)}. "
            f"Allowed: {sorted(INVENTORY_ITEMS_FILTER_KEYS)}"
        )
    return tool_inventory_items(filters)


def tool_deliveries_late(filters: dict) -> CallToolResult:
    """read(deliveries,late) — same compose call as GET /deliveries/late."""
    user = _operations_user()
    try:
        payload = _DELIVERIES_SERVICE.compose(
            user,
            branches=_clean_branches(filters.get("branch")),
            status=filters.get("status"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            page=filters.get("page"),
            page_size=filters.get("page_size"),
            sort_by=filters.get("sort_by"),
            sort_dir=filters.get("sort_dir"),
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(payload, meta={"delpi/source": "bff:/deliveries/late"})


def tool_inventory_summary(filters: dict) -> CallToolResult:
    """read(inventory,summary) — same call as /stock-balances/summary."""
    user = _operations_user()
    try:
        payload = _INVENTORY_SERVICE.get_summary(
            user,
            branches=_clean_branches(filters.get("branch")),
            warehouse=filters.get("warehouse"),
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(
        payload, meta={"delpi/source": "bff:/inventory/stock-balances/summary"}
    )


def tool_inventory_items(filters: dict) -> CallToolResult:
    """read(inventory,items) — same call as /stock-balances/items."""
    user = _operations_user()
    try:
        payload = _INVENTORY_SERVICE.list_items(
            user,
            branches=_clean_branches(filters.get("branch")),
            warehouse=filters.get("warehouse"),
            page=filters.get("page"),
            page_size=filters.get("page_size"),
            sort=filters.get("sort"),
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(
        payload, meta={"delpi/source": "bff:/inventory/stock-balances/items"}
    )

_SAFETY_ACTION_KEYS = {
    "filters": SAFETY_STOCK_FILTERS_FILTER_KEYS,
    "summary": SAFETY_STOCK_SUMMARY_FILTER_KEYS,
    "items": SAFETY_STOCK_ITEMS_FILTER_KEYS,
}


def _dispatch_safety_stock_read(
    action: str, filters: dict, identity: dict
) -> CallToolResult:
    if action in {"details", "suppliers"}:
        if filters:
            return _invalid(
                f"read(safety_stock,{action}) accepts no 'filters' — "
                "use identity {code, branch}."
            )
        unknown = _unknown_keys(identity, SAFETY_STOCK_ITEM_IDENTITY_KEYS)
        if unknown:
            return _invalid(
                f"Unknown safety_stock identity keys: {sorted(unknown)}. "
                f"Allowed: {sorted(SAFETY_STOCK_ITEM_IDENTITY_KEYS)}"
            )
        code = str(identity.get("code") or "").strip()
        if not code:
            return _invalid("safety_stock identity requires 'code'.")
        if action == "details":
            return tool_safety_stock_item_details(
                code, identity.get("branch")
            )
        return tool_safety_stock_item_suppliers(code, identity.get("branch"))
    if identity:
        return _invalid(
            f"read(safety_stock,{action}) does not accept 'identity'."
        )
    allowed = _SAFETY_ACTION_KEYS[action]
    unknown = _unknown_keys(filters, allowed)
    if unknown:
        return _invalid(
            f"Unknown safety_stock {action} filters: {sorted(unknown)}. "
            f"Allowed: {sorted(allowed)}"
        )
    if action == "filters":
        return tool_safety_stock_filters(filters)
    if action == "summary":
        return tool_safety_stock_summary(filters)
    return tool_safety_stock_items(filters)


def tool_safety_stock_filters(filters: dict) -> CallToolResult:
    user = _operations_user()
    try:
        payload = _SAFETY_STOCK_SERVICE.get_filters(
            user,
            branch=filters.get("branch"),
            include_blocked=filters.get("includeBlocked"),
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(payload, meta={"delpi/source": "bff:/safety-stock/filters"})


def tool_safety_stock_summary(filters: dict) -> CallToolResult:
    user = _operations_user()
    try:
        payload = _SAFETY_STOCK_SERVICE.get_summary(
            user,
            branch=filters.get("branch"),
            include_blocked=filters.get("includeBlocked"),
            product_group=filters.get("productGroup"),
            unit=filters.get("unit"),
            search=filters.get("search"),
            status=filters.get("status"),
            include_without_safety_stock=filters.get(
                "includeWithoutSafetyStock"
            ),
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(payload, meta={"delpi/source": "bff:/safety-stock/summary"})


def tool_safety_stock_items(filters: dict) -> CallToolResult:
    user = _operations_user()
    try:
        payload = _SAFETY_STOCK_SERVICE.list_items(
            user,
            branch=filters.get("branch"),
            page=filters.get("page"),
            page_size=filters.get("page_size"),
            sort_by=filters.get("sortBy"),
            sort_direction=filters.get("sortDirection"),
            include_blocked=filters.get("includeBlocked"),
            product_group=filters.get("productGroup"),
            unit=filters.get("unit"),
            search=filters.get("search"),
            status=filters.get("status"),
            include_without_safety_stock=filters.get(
                "includeWithoutSafetyStock"
            ),
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(payload, meta={"delpi/source": "bff:/safety-stock/items"})


def tool_safety_stock_item_details(code, branch) -> CallToolResult:
    user = _operations_user()
    try:
        payload = _SAFETY_STOCK_SERVICE.get_item_details(
            user, code=code, branch=branch
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(
        payload, meta={"delpi/source": "bff:/safety-stock/items/{code}/details"}
    )


def tool_safety_stock_item_suppliers(code, branch) -> CallToolResult:
    user = _operations_user()
    try:
        payload = _SAFETY_STOCK_SERVICE.get_item_suppliers(
            user, code=code, branch=branch
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(
        payload,
        meta={"delpi/source": "bff:/safety-stock/items/{code}/suppliers"},
    )


def _analytics_user() -> EffectiveUser:
    user = _effective_user()
    if not can_use_analytics(user):
        raise AuthorizationError("Forbidden")
    return user


def _dispatch_otd_read(
    action: str, filters: dict, identity: dict
) -> CallToolResult:
    if identity:
        return _invalid(f"read(otd,{action}) does not accept 'identity'.")
    allowed = (
        OTD_AGGREGATE_FILTER_KEYS
        if action == "aggregate"
        else OTD_SERIES_FILTER_KEYS
    )
    unknown = _unknown_keys(filters, allowed)
    if unknown:
        return _invalid(
            f"Unknown otd {action} filters: {sorted(unknown)}. "
            f"Allowed: {sorted(allowed)}"
        )
    if action == "aggregate":
        return tool_otd_aggregate(filters)
    return tool_otd_series(filters)


def tool_otd_aggregate(filters: dict) -> CallToolResult:
    """read(otd,aggregate) — same compose call as GET /analytics/otd."""
    user = _analytics_user()
    branch = filters.get("branch")
    if branch is not None and not isinstance(branch, str):
        return _invalid(
            "read(otd,aggregate) filter 'branch' must be a single branch "
            "string ('01', '02' or 'all'), not a list — use "
            "read(otd,series) for multi-branch OTD."
        )
    try:
        payload = _OTD_AGG_SERVICE.compose(
            user,
            branch=branch,
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(payload, meta={"delpi/source": "bff:/analytics/otd"})


def tool_otd_series(filters: dict) -> CallToolResult:
    """read(otd,series) — same compose call as GET /analytics/otd/series."""
    user = _analytics_user()
    try:
        branches = normalize_overview_branches(
            _clean_branches(filters.get("branch"))
        )
    except ValueError as exc:
        return _invalid(str(exc))
    series_branch = branches[0] if len(branches) == 1 else None
    try:
        payload = _OTD_SERIES_SERVICE.compose(
            user,
            branch=series_branch,
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            granularity=filters.get("granularity"),
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(payload, meta={"delpi/source": "bff:/analytics/otd/series"})


def tool_procurement_diagnostic(filters: dict) -> CallToolResult:
    """analyze(procurement_diagnostic) — bounded multi-entity compose."""
    user = _analytics_user()
    try:
        payload = _PROC_DIAG_SERVICE.compose(
            user,
            branch=filters.get("branch"),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            include_sections=filters.get("include_sections"),
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(
        payload, meta={"delpi/source": "bff:multi[diagnostic]"}
    )


def tool_analyze_overview_summary(filters: dict) -> CallToolResult:
    """analyze(overview_summary) — same compose as GET /analytics/overview.

    Partial producer failures stay visible in the payload's own
    partialFailures semantics — never coerced to zeros or full success.
    """
    user = _analytics_user()
    try:
        payload = _OVERVIEW_SERVICE.compose(
            user,
            branches=_clean_branches(filters.get("branch")),
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
        )
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(payload, meta={"delpi/source": "bff:/analytics/overview"})

_PRODUCTION_ORDER_RE = re.compile(r"^[0-9A-Z]{11}$")


def _dispatch_consumption_read(
    action: str, filters: dict, identity: dict
) -> CallToolResult:
    if action == "get":
        if filters:
            return _invalid(
                "read(consumption,get) accepts no 'filters' — "
                "use identity {unit, production_order}."
            )
        unknown = _unknown_keys(identity, CONSUMPTION_IDENTITY_KEYS)
        if unknown:
            return _invalid(
                f"Unknown consumption identity keys: {sorted(unknown)}. "
                f"Allowed: {sorted(CONSUMPTION_IDENTITY_KEYS)}"
            )
        return tool_consumption_get(identity)
    if identity:
        return _invalid(
            f"read(consumption,{action}) does not accept 'identity'."
        )
    allowed = (
        CONSUMPTION_SEARCH_FILTER_KEYS
        if action == "search"
        else CONSUMPTION_COMPARISON_FILTER_KEYS
    )
    unknown = _unknown_keys(filters, allowed)
    if unknown:
        return _invalid(
            f"Unknown consumption {action} filters: {sorted(unknown)}. "
            f"Allowed: {sorted(allowed)}"
        )
    if action == "search":
        return tool_consumption_search(filters)
    return tool_consumption_comparison(filters)


def _consumption_unit(user: EffectiveUser, filters: dict) -> str | CallToolResult:
    unit = str(filters.get("unit") or "").strip()
    if not unit:
        return _invalid("consumption requires 'unit' (01|02).")
    try:
        _AUTHZ.require_units(user, [unit])
    except AuthorizationError as exc:
        return _invalid(str(exc))
    return unit


def tool_consumption_search(filters: dict) -> CallToolResult:
    """read(consumption,search) — GET /consumption-audit/orders."""
    user = _operations_user()
    unit = _consumption_unit(user, filters)
    if not isinstance(unit, str):
        return unit
    search = (filters.get("search") or "").strip().upper()
    if search and not re.match(r"^[0-9A-Z]{1,11}$", search):
        return _invalid("invalid parameter: search")
    date_type = (filters.get("date_type") or "emission").strip()
    if date_type not in CONSUMPTION_DATE_TYPES:
        return _invalid("invalid parameter: date_type")
    ps = filters.get("period_start")
    pe = filters.get("period_end")
    if ps and pe and str(ps) > str(pe):
        return _invalid("invalid parameter: period")
    params: dict[str, Any] = {"branch": unit}
    for key in (
        "search", "product", "date_type", "period_start", "period_end",
        "status", "work_center", "operation", "page", "page_size",
    ):
        value = filters.get(key)
        if value is None:
            continue
        params[key] = value
    if search:
        params["search"] = search
    payload = _S2S_GATEWAY.get(
        "/supplies/consumption-audit/orders",
        access_token=user.access_token or "",
        params=params,
    )
    data = unwrap_delpi_envelope(payload)
    return _ok(data, meta={"delpi/source": "bff:/consumption-audit/orders"})


def tool_consumption_get(identity: dict) -> CallToolResult:
    """read(consumption,get) — /consumption-audit/orders/{op}."""
    user = _operations_user()
    op = str(identity.get("production_order") or "").strip().upper()
    if not _PRODUCTION_ORDER_RE.match(op):
        return _invalid(
            "production_order must be the 11-position order key"
        )
    unit = _consumption_unit(user, identity)
    if not isinstance(unit, str):
        return unit
    payload = _S2S_GATEWAY.get(
        f"/supplies/consumption-audit/orders/{op}",
        access_token=user.access_token or "",
        params={"branch": unit},
    )
    data = unwrap_delpi_envelope(payload)
    return _ok(
        data, meta={"delpi/source": "bff:/consumption-audit/orders/{op}"}
    )


def tool_consumption_comparison(filters: dict) -> CallToolResult:
    """read(consumption,comparison) — 2..10 distinct 11-position keys."""
    user = _operations_user()
    unit = _consumption_unit(user, filters)
    if not isinstance(unit, str):
        return unit
    orders = [
        str(op).strip().upper()
        for op in (filters.get("orders") or [])
        if str(op).strip()
    ]
    unique = list(dict.fromkeys(orders))
    if not 2 <= len(unique) <= 10:
        return _invalid(
            "orders must contain between 2 and 10 distinct keys"
        )
    if any(not _PRODUCTION_ORDER_RE.match(op) for op in unique):
        return _invalid(
            "each order must be the 11-position order key"
        )
    payload = _S2S_GATEWAY.get(
        "/supplies/consumption-audit/comparison",
        access_token=user.access_token or "",
        params={"branch": unit, "orders": ",".join(unique)},
    )
    data = unwrap_delpi_envelope(payload)
    return _ok(
        data, meta={"delpi/source": "bff:/consumption-audit/comparison"}
    )


def _market_user() -> EffectiveUser:
    user = _effective_user()
    if not can_use_market_intelligence(user):
        raise AuthorizationError("Forbidden")
    return user


_MARKET_ACTION_KEYS = {
    "filters": MARKET_FILTERS_KEYS,
    "summary": MARKET_COMMON_KEYS,
    "series": MARKET_SERIES_KEYS,
    "import_series": MARKET_IMPORT_SERIES_KEYS,
    "producer_price_series": MARKET_PRODUCER_PRICE_KEYS,
    "fx_series": MARKET_FX_KEYS,
    "quote_series": MARKET_QUOTE_KEYS,
    "quote_compare": MARKET_QUOTE_KEYS,
    "monthly_averages": MARKET_MONTHLY_KEYS,
}


def _dispatch_market_read(
    action: str, filters: dict, identity: dict
) -> CallToolResult:
    if identity:
        return _invalid(f"read(market,{action}) does not accept 'identity'.")
    allowed = _MARKET_ACTION_KEYS[action]
    unknown = _unknown_keys(filters, allowed)
    if unknown:
        return _invalid(
            f"Unknown market {action} filters: {sorted(unknown)}. "
            f"Allowed: {sorted(allowed)}"
        )
    return tool_market_read(action, filters)


def tool_market_read(action: str, filters: dict) -> CallToolResult:
    user = _market_user()
    svc = _MARKET_SERVICE
    try:
        if action == "filters":
            payload = svc.get_filters()
        elif action == "summary":
            payload = svc.get_summary(
                instrument_code=filters.get("instrument"),
                currency=filters.get("currency"),
                fx_kind=filters.get("fx_kind"),
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
            )
        elif action == "series":
            payload = svc.list_series(
                instrument_code=filters.get("instrument"),
                currency=filters.get("currency"),
                granularity=filters.get("granularity"),
                fx_kind=filters.get("fx_kind"),
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
            )
        elif action == "import_series":
            payload = svc.list_import_series(
                ncm_code=filters.get("ncm"),
                granularity=filters.get("granularity"),
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
                country_code=filters.get("country_code"),
                state_code=filters.get("state_code"),
            )
        elif action == "producer_price_series":
            payload = svc.list_producer_price_series(
                series_id=filters.get("series_id"),
                granularity=filters.get("granularity"),
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
            )
        elif action == "fx_series":
            payload = svc.list_fx_series(
                fx_kind=filters.get("fx_kind"),
                granularity=filters.get("granularity"),
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
            )
        elif action == "quote_series":
            payload = svc.list_quotes_series(
                instruments=filters.get("instruments"),
                granularity=filters.get("granularity"),
                currency=filters.get("currency"),
                fx_kind=filters.get("fx_kind"),
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
            )
        elif action == "quote_compare":
            payload = svc.list_quotes_compare(
                instruments=filters.get("instruments"),
                granularity=filters.get("granularity"),
                currency=filters.get("currency"),
                fx_kind=filters.get("fx_kind"),
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
            )
        else:
            payload = svc.list_monthly_averages(
                instrument_code=filters.get("instrument"),
                currency=filters.get("currency"),
                fx_kind=filters.get("fx_kind"),
                date_from=filters.get("date_from"),
                date_to=filters.get("date_to"),
                page=filters.get("page"),
                page_size=filters.get("page_size"),
            )
    except MarketDataNotFoundError as exc:
        return _invalid(str(exc))
    except ValueError as exc:
        return _invalid(str(exc))
    return _ok(
        payload, meta={"delpi/source": "bff:/market-intelligence/" + action}
    )


def _dispatch_comex_read(
    action: str, filters: dict, identity: dict
) -> CallToolResult:
    if action in {"ncm_governance_get", "view_get"}:
        if filters:
            return _invalid(
                f"read(comex,{action}) accepts no 'filters' — "
                "use identity."
            )
        unknown = _unknown_keys(identity, COMEX_IDENTITY_KEYS)
        if unknown:
            return _invalid(
                f"Unknown comex identity keys: {sorted(unknown)}. "
                f"Allowed: {sorted(COMEX_IDENTITY_KEYS)}"
            )
        if action == "ncm_governance_get":
            return tool_comex_governance_get(identity)
        return tool_comex_view_get(identity)
    if identity:
        return _invalid(
            f"read(comex,{action}) does not accept 'identity'."
        )
    allowed = (
        COMEX_PRODUCTS_KEYS
        if action == "products_search"
        else COMEX_NCM_LIST_KEYS
        if action == "ncm_governance"
        else COMEX_VIEWS_KEYS
    )
    unknown = _unknown_keys(filters, allowed)
    if unknown:
        return _invalid(
            f"Unknown comex {action} filters: {sorted(unknown)}. "
            f"Allowed: {sorted(allowed)}"
        )
    if action == "products_search":
        return tool_comex_products_search(filters)
    if action == "ncm_governance":
        return tool_comex_governance_list(filters)
    return tool_comex_views()


def tool_comex_products_search(filters: dict) -> CallToolResult:
    user = _market_user()
    try:
        payload = _COMEX_SERVICE.search_products(user=user, args=filters)
    except (ComexValidationError, ComexConflictError) as exc:
        return _invalid(str(exc))
    return _ok(
        payload,
        meta={"delpi/source":
              "bff:/market-intelligence/comex/products/search"},
    )


def tool_comex_governance_list(filters: dict) -> CallToolResult:
    user = _market_user()
    try:
        items = _COMEX_SERVICE.list_governance(
            status=filters.get("status")
        )
    except ComexValidationError as exc:
        return _invalid(str(exc))
    return _ok(
        {"items": items},
        meta={"delpi/source":
              "bff:/market-intelligence/comex/ncm-governance"},
    )


def tool_comex_governance_get(identity: dict) -> CallToolResult:
    user = _market_user()
    gid = str(identity.get("governance_id") or "").strip()
    if not gid:
        return _invalid("comex identity requires 'governance_id'.")
    try:
        payload = _COMEX_SERVICE.get_governance(gid)
    except (
        ComexNotFoundError, ComexForbiddenError, ComexValidationError
    ) as exc:
        return _invalid(str(exc))
    return _ok(
        payload,
        meta={"delpi/source":
              "bff:/market-intelligence/comex/ncm-governance/{id}"},
    )


def tool_comex_views() -> CallToolResult:
    user = _market_user()
    items = _COMEX_SERVICE.list_views(user=user)
    return _ok(
        {"items": items},
        meta={"delpi/source": "bff:/market-intelligence/comex/views"},
    )


def tool_comex_view_get(identity: dict) -> CallToolResult:
    user = _market_user()
    vid = str(identity.get("view_id") or "").strip()
    if not vid:
        return _invalid("comex identity requires 'view_id'.")
    try:
        payload = _COMEX_SERVICE.get_view(vid, user=user)
    except (
        ComexNotFoundError, ComexForbiddenError, ComexValidationError
    ) as exc:
        return _invalid(str(exc))
    return _ok(
        payload,
        meta={"delpi/source":
              "bff:/market-intelligence/comex/views/{id}"},
    )


def _shell_user() -> EffectiveUser:
    user = _effective_user()
    if not can_enter_shell(user):
        raise AuthorizationError("Forbidden")
    return user


def _dispatch_session_read(
    action: str, filters: dict, identity: dict
) -> CallToolResult:
    if identity:
        return _invalid(
            f"read(session,{action}) does not accept 'identity'."
        )
    allowed = (
        SESSION_CAPABILITIES_KEYS
        if action == "capabilities"
        else SESSION_PREFERENCES_KEYS
    )
    unknown = _unknown_keys(filters, allowed)
    if unknown:
        return _invalid(
            f"Unknown session {action} filters: {sorted(unknown)}. "
            "Expected: none."
        )
    if action == "capabilities":
        return tool_session_capabilities()
    return tool_session_preferences()


def tool_session_capabilities() -> CallToolResult:
    user = _shell_user()
    payload = _CAPABILITY_SERVICE.resolve(user)
    return _ok(payload, meta={"delpi/source": "bff:/me/capabilities"})


def tool_session_preferences() -> CallToolResult:
    user = _shell_user()
    payload = _PREFERENCES_SERVICE.get(user)
    return _ok(payload, meta={"delpi/source": "bff:/me/preferences"})


def _dispatch_users_read(
    action: str, filters: dict, identity: dict
) -> CallToolResult:
    if action == "related_requests":
        unknown = _unknown_keys(filters, USERS_RELATED_KEYS)
        if unknown:
            return _invalid(
                f"Unknown users related_requests filters: "
                f"{sorted(unknown)}. Allowed: "
                f"{sorted(USERS_RELATED_KEYS)}"
            )
    elif filters:
        return _invalid(
            f"read(users,{action}) accepts no 'filters'."
        )
    unknown = _unknown_keys(identity, USERS_IDENTITY_KEYS)
    if unknown:
        return _invalid(
            f"Unknown users identity keys: {sorted(unknown)}. "
            f"Allowed: {sorted(USERS_IDENTITY_KEYS)}"
        )
    uid = str(identity.get("user_id") or "").strip()
    if not uid:
        return _invalid("users identity requires 'user_id'.")
    if action == "profile":
        return tool_users_profile(uid)
    if action == "photo":
        return tool_users_photo(uid)
    return tool_users_related_requests(uid, filters)


def tool_users_profile(user_id: str) -> CallToolResult:
    user = _operations_user()
    try:
        payload = _USER_PROFILE_SERVICE.get(user, user_id)
    except AuthorizationError:
        raise
    except Exception as exc:
        return _invalid(str(exc))
    return _ok(
        payload, meta={"delpi/source": "bff:/users/{id}/profile"}
    )


def tool_users_photo(user_id: str) -> CallToolResult:
    user = _operations_user()
    photo = _USER_PROFILE_SERVICE.photo(user, user_id)
    if not photo:
        return _invalid("photo not found")
    content, content_type, file_name = photo
    import base64 as _b64
    return _ok(
        {
            "content_base64": _b64.b64encode(content).decode("ascii"),
            "content_type": content_type or "image/jpeg",
            "file_name": file_name,
        },
        meta={"delpi/source": "bff:/users/{id}/photo"},
    )


def tool_users_related_requests(
    user_id: str, filters: dict
) -> CallToolResult:
    user = _operations_user()
    try:
        payload = _USER_PROFILE_SERVICE.related_purchase_requests(
            user,
            user_id,
            branches=_clean_branches(filters.get("branch")),
            page=filters.get("page") or 1,
            page_size=filters.get("page_size") or 5,
            sort_by=filters.get("sort_by"),
            sort_dir=filters.get("sort_dir"),
        )
    except AuthorizationError:
        raise
    except Exception as exc:
        return _invalid(str(exc))
    return _ok(
        payload, meta={"delpi/source": "bff:/users/{id}/related-requests"}
    )

