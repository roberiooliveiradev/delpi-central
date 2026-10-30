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
import logging
from typing import Any

from delpi_mcp.errors import kind_for_http_status, mcp_tool_result
from delpi_mcp.identity import require_mcp_context
from mcp.types import CallToolResult

from app.application.security.supplies_permissions import (
    can_use_operations,
    has_canonical_access,
    has_canonical_manage,
)
from app.application.services.authorization_service import AuthorizationService
from app.domain.entities import EffectiveUser
from app.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    CoreApiUnavailableError,
)
from app.infrastructure.gateways.delpi_api_gateway import (
    DelpiApiGateway,
    DelpiApiGatewayError,
)
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.interfaces.mcp import knowledge
from app.interfaces.mcp.branding import SURI_FULL_NAME, SURI_MISSION
from app.interfaces.mcp.constants import (
    CATALOG_VERSION,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MAX_SAMPLE_SIZE,
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
    meta = None
    if status_code == 401:
        meta = mcp_www_authenticate_meta(
            error="invalid_token",
            error_description="Authentication required",
        )
    return mcp_tool_result(
        {
            "success": False,
            "message": message,
            "data": err_data,
            "status_code": status_code,
        },
        is_error=True,
        meta=meta,
    )


def handle_tool_error(exc: Exception) -> CallToolResult:
    if isinstance(exc, AuthenticationError):
        return _error(
            "Authentication required.", status_code=401, error_code="unauthenticated"
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


def tool_get_catalog() -> CallToolResult:
    _effective_user()
    return _ok(
        {
            "mcp": {
                "name": "supplies",
                "persona": SURI_FULL_NAME,
                "mission": SURI_MISSION,
                "catalog_version": CATALOG_VERSION,
            },
            "tools": [
                {"name": name, "tool_class": TOOL_CLASS[name]}
                for name in sorted(TOOL_CLASS)
            ],
            "limits": {
                "max_page_size": MAX_PAGE_SIZE,
                "max_sample_size": MAX_SAMPLE_SIZE,
                "operational_units": ["01", "02"],
            },
            "directives": [
                "Tool metadata describes semantics; it never authorizes.",
                "READ tools mirror the Portal BFF contracts; no write "
                "capability exists in this version.",
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


# -- KNOWLEDGE (S5) --------------------------------------------------------


def _knowledge_user() -> EffectiveUser:
    user = _effective_user()
    if not has_canonical_access(user):
        raise AuthorizationError("Forbidden")
    return user


def tool_search_supplies_knowledge(
    query: str | None = None,
    topic: str | None = None,
    limit: int = 8,
) -> CallToolResult:
    _knowledge_user()
    return _ok(
        knowledge.search_knowledge(query=query, topic=topic, limit=limit)
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
