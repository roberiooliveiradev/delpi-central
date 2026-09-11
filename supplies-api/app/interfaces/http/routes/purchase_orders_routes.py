from __future__ import annotations

from typing import Any

from flask import Blueprint, g, jsonify, request

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGateway, DelpiApiGatewayError
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.interfaces.http.auth_decorators import require_permission, require_unit

purchase_orders_bp = Blueprint("purchase_orders", __name__)

_GATEWAY = DelpiApiGateway()


def _access_token() -> str:
    return g.current_user.access_token or ""


def _gateway_error_response(exc: DelpiApiGatewayError):
    status = exc.status_code or 502
    if status == 401:
        return jsonify({"detail": "Unauthorized", "code": "unauthorized"}), 401
    if status == 403:
        return jsonify({"detail": "Forbidden", "code": "forbidden"}), 403
    if status == 404:
        return jsonify({"detail": "Not Found", "code": "not_found"}), 404
    if status < 500:
        return jsonify({"detail": str(exc), "code": "upstream_client_error"}), status
    return jsonify({"detail": "api-delpi unavailable", "code": "bad_gateway"}), 502


def _bool_query(name: str) -> bool:
    raw = (request.args.get(name) or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _list_params() -> dict[str, Any]:
    params: dict[str, Any] = {}
    for key in (
        "branch",
        "page",
        "page_size",
        "order_number",
        "product_code",
        "supplier_code",
        "expected_delivery_from",
        "expected_delivery_to",
    ):
        value = (request.args.get(key) or "").strip()
        if value:
            params[key] = value
    if _bool_query("late_only"):
        params["late_only"] = "true"
    return params


@purchase_orders_bp.get("/purchase-orders")
@require_permission("supplies.operations.access")
@require_unit("branch")
def list_portal_purchase_orders():
    """operationId: list_portal_purchase_orders — open SC7 lines via api-delpi."""
    try:
        payload = _GATEWAY.get(
            "/supplies/purchase-orders",
            access_token=_access_token(),
            params=_list_params(),
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    data = unwrap_delpi_envelope(payload)
    return jsonify(data if isinstance(data, dict) else {"items": [], "total": 0}), 200
