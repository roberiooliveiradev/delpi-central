"""Consumption audit BFF (GLPI #1353) — OP × operation detail via api-delpi.

AuthZ: ``supplies.access`` (Core effective) + unit scope 01|02. Technical
identity: individual S2S credential via ``DelpiS2SApiGateway`` — the shared
legacy token is never used and no local recalculation of Protheus rules is
performed; the BFF only projects the producer payload.
"""

from __future__ import annotations

import logging
import re
from datetime import date

from flask import Blueprint, g, jsonify, request

from app.application.security.supplies_permissions import can_use_operations
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.infrastructure.gateways.delpi_s2s_gateway import DelpiS2SApiGateway
from app.interfaces.http.auth_decorators import require_policy, require_unit

consumption_audit_bp = Blueprint("consumption_audit", __name__)

logger = logging.getLogger(__name__)

_GATEWAY = DelpiS2SApiGateway()

# Chave canônica da OP — C2_NUM(6) + C2_ITEM(2) + C2_SEQUEN(3), zeros
# preservados; validada antes de qualquer chamada upstream.
_PRODUCTION_ORDER_RE = re.compile(r"^[0-9A-Z]{11}$")
_SEARCH_FRAGMENT_RE = re.compile(r"^[0-9A-Z]{1,11}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATE_TYPES = {"emission", "finished", "appointment"}
_MAX_COMPARE_ORDERS = 10
_MIN_COMPARE_ORDERS = 2


def _access_token() -> str:
    return g.current_user.access_token or ""


def _gateway_error_response(exc: DelpiApiGatewayError):
    if exc.status_code is None:
        # Timeout / connection failure / S2S credential unavailable.
        return jsonify(
            {"detail": "api-delpi unreachable", "code": "upstream_unreachable"}
        ), 504
    status = exc.status_code
    if status == 401:
        return jsonify({"detail": "Unauthorized", "code": "unauthorized"}), 401
    if status == 403:
        # Propagate the upstream denial code (e.g. S2S_SCOPE_DENIED) so the
        # response identifies the denial owner instead of collapsing into
        # the same "forbidden" the BFF uses for its own supplies.access check.
        logger.warning(
            "consumption_audit_upstream_denied status=403 upstream_code=%s",
            exc.code or "none",
        )
        return jsonify(
            {"detail": "Forbidden", "code": exc.code or "upstream_forbidden"}
        ), 403
    if status == 404:
        return jsonify({"detail": "Not Found", "code": "not_found"}), 404
    if status < 500:
        return jsonify(
            {
                "detail": "api-delpi client error",
                "code": exc.code or "upstream_client_error",
            }
        ), status
    return jsonify(
        {
            "detail": "api-delpi unavailable",
            "code": exc.code or "bad_gateway",
        }
    ), 502


def _invalid(detail: str):
    return jsonify({"detail": detail, "code": "invalid_request"}), 422


def _optional_text(name: str, *, limit: int, upper: bool = False) -> str | None:
    text = (request.args.get(name) or "").strip()[:limit]
    return text.upper() if upper and text else text or None


def _optional_date(name: str) -> str | None:
    text = _optional_text(name, limit=10)
    if text:
        try:
            date.fromisoformat(text)
        except ValueError:
            raise ValueError(name)
    return text


def _optional_positive_int(name: str, *, default: int, maximum: int) -> int:
    raw = (request.args.get(name) or "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(name)
    if not (1 <= value <= maximum):
        raise ValueError(name)
    return value


@consumption_audit_bp.get("/consumption-audit/orders")
@require_policy(can_use_operations)
@require_unit("unit")
def search_portal_consumption_audit_orders():
    """operationId: search_portal_consumption_audit_orders — busca paginada."""
    try:
        search = _optional_text("search", limit=11, upper=True)
        if search and not _SEARCH_FRAGMENT_RE.match(search):
            raise ValueError("search")
        params = {
            "branch": (request.args.get("unit") or "").strip(),
            "search": search,
            "product": _optional_text("product", limit=60),
            "date_type": _optional_text("date_type", limit=20) or "emission",
            "period_start": _optional_date("period_start"),
            "period_end": _optional_date("period_end"),
            "status": _optional_text("status", limit=1, upper=True),
            "work_center": _optional_text("work_center", limit=20, upper=True),
            "operation": _optional_text("operation", limit=4, upper=True),
            "page": _optional_positive_int("page", default=1, maximum=10000),
            "page_size": _optional_positive_int(
                "page_size", default=25, maximum=50
            ),
        }
        if params["date_type"] not in _DATE_TYPES:
            raise ValueError("date_type")
        if (
            params["period_start"]
            and params["period_end"]
            and params["period_start"] > params["period_end"]
        ):
            raise ValueError("period")
    except ValueError as exc:
        return _invalid(f"invalid parameter: {exc}")

    upstream_params = {key: value for key, value in params.items() if value is not None}
    try:
        payload = _GATEWAY.get(
            "/supplies/consumption-audit/orders",
            access_token=_access_token(),
            params=upstream_params,
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)

    data = unwrap_delpi_envelope(payload)
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        return jsonify(
            {"detail": "Malformed upstream payload", "code": "bad_gateway"}
        ), 502
    return jsonify(data), 200


@consumption_audit_bp.get("/consumption-audit/comparison")
@require_policy(can_use_operations)
@require_unit("unit")
def get_portal_consumption_audit_comparison():
    """operationId: get_portal_consumption_audit_comparison — batch ≤10 OPs."""
    raw = (request.args.get("orders") or "").strip()
    orders = [part.strip().upper() for part in raw.split(",") if part.strip()]
    unique = list(dict.fromkeys(orders))
    if not (_MIN_COMPARE_ORDERS <= len(unique) <= _MAX_COMPARE_ORDERS):
        return _invalid(
            "orders must contain between "
            f"{_MIN_COMPARE_ORDERS} and {_MAX_COMPARE_ORDERS} distinct keys"
        )
    if any(not _PRODUCTION_ORDER_RE.match(op) for op in unique):
        return _invalid("each order must be the 11-position order key")

    try:
        payload = _GATEWAY.get(
            "/supplies/consumption-audit/comparison",
            access_token=_access_token(),
            params={
                "branch": (request.args.get("unit") or "").strip(),
                "orders": ",".join(unique),
            },
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)

    data = unwrap_delpi_envelope(payload)
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        return jsonify(
            {"detail": "Malformed upstream payload", "code": "bad_gateway"}
        ), 502
    return jsonify(data), 200


@consumption_audit_bp.get("/consumption-audit/orders/<production_order>")
@require_policy(can_use_operations)
@require_unit("unit")
def get_portal_consumption_audit_order(production_order: str):
    """operationId: get_portal_consumption_audit_order — detalhe OP × operação."""
    op = (production_order or "").strip().upper()
    if not _PRODUCTION_ORDER_RE.match(op):
        return jsonify(
            {
                "detail": "production_order must be the 11-position order key",
                "code": "invalid_request",
            }
        ), 422

    unit = (request.args.get("unit") or "").strip()
    try:
        payload = _GATEWAY.get(
            f"/supplies/consumption-audit/orders/{op}",
            access_token=_access_token(),
            params={"branch": unit},
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)

    data = unwrap_delpi_envelope(payload)
    if not isinstance(data, dict) or not data.get("order"):
        return jsonify(
            {"detail": "Malformed upstream payload", "code": "bad_gateway"}
        ), 502
    return jsonify(data), 200
