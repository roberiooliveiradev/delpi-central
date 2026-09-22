"""Portal inventory stock balances BFF routes."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from app.application.security.supplies_permissions import can_use_operations
from app.application.services.inventory_stock_balances_service import (
    InventoryStockBalancesService,
)
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.interfaces.http.auth_decorators import require_policy

inventory_bp = Blueprint("inventory", __name__)


def _branch_args() -> list[str]:
    values: list[str] = []
    for raw in request.args.getlist("branch"):
        values.extend(part.strip() for part in str(raw).split(",") if part.strip())
    return values


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


@inventory_bp.get("/inventory/stock-balances/summary")
@require_policy(can_use_operations)
def get_portal_inventory_stock_balances_summary():
    """operationId: get_portal_inventory_stock_balances_summary."""
    service = InventoryStockBalancesService()
    try:
        payload = service.get_summary(
            g.current_user,
            branches=_branch_args(),
            warehouse=request.args.get("warehouse"),
        )
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200


@inventory_bp.get("/inventory/stock-balances/items")
@require_policy(can_use_operations)
def list_portal_inventory_stock_balances():
    """operationId: list_portal_inventory_stock_balances."""
    service = InventoryStockBalancesService()
    try:
        payload = service.list_items(
            g.current_user,
            branches=_branch_args(),
            warehouse=request.args.get("warehouse"),
            page=request.args.get("page"),
            page_size=request.args.get("page_size"),
            sort=request.args.get("sort"),
        )
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200
