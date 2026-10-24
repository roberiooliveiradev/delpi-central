"""Portal safety stock BFF routes (E11)."""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from app.application.security.supplies_permissions import can_use_operations
from app.application.services.safety_stock_service import SafetyStockService
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.interfaces.http.auth_decorators import require_policy

safety_stock_bp = Blueprint("safety_stock", __name__)


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


@safety_stock_bp.get("/safety-stock/filters")
@require_policy(can_use_operations)
def get_portal_safety_stock_filters():
    """operationId: get_portal_safety_stock_filters."""
    service = SafetyStockService()
    try:
        payload = service.get_filters(
            g.current_user,
            branch=request.args.get("branch"),
            include_blocked=request.args.get("includeBlocked"),
        )
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200


@safety_stock_bp.get("/safety-stock/summary")
@require_policy(can_use_operations)
def get_portal_safety_stock_summary():
    """operationId: get_portal_safety_stock_summary."""
    service = SafetyStockService()
    try:
        payload = service.get_summary(
            g.current_user,
            branch=request.args.get("branch"),
            include_blocked=request.args.get("includeBlocked"),
            product_group=request.args.get("productGroup"),
            unit=request.args.get("unit"),
            search=request.args.get("search"),
            status=request.args.get("status"),
            include_without_safety_stock=request.args.get(
                "includeWithoutSafetyStock"
            ),
        )
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200


@safety_stock_bp.get("/safety-stock/items")
@require_policy(can_use_operations)
def list_portal_safety_stock_items():
    """operationId: list_portal_safety_stock_items."""
    service = SafetyStockService()
    try:
        payload = service.list_items(
            g.current_user,
            branch=request.args.get("branch"),
            page=request.args.get("page"),
            page_size=request.args.get("page_size"),
            sort_by=request.args.get("sortBy"),
            sort_direction=request.args.get("sortDirection"),
            include_blocked=request.args.get("includeBlocked"),
            product_group=request.args.get("productGroup"),
            unit=request.args.get("unit"),
            search=request.args.get("search"),
            status=request.args.get("status"),
            include_without_safety_stock=request.args.get(
                "includeWithoutSafetyStock"
            ),
        )
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200


@safety_stock_bp.get("/safety-stock/items/<code>/details")
@require_policy(can_use_operations)
def get_portal_safety_stock_item_details(code: str):
    """operationId: get_portal_safety_stock_item_details."""
    service = SafetyStockService()
    try:
        payload = service.get_item_details(
            g.current_user,
            code=code,
            branch=request.args.get("branch"),
        )
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200


@safety_stock_bp.get("/safety-stock/items/<code>/suppliers")
@require_policy(can_use_operations)
def get_portal_safety_stock_item_suppliers(code: str):
    """operationId: get_portal_safety_stock_item_suppliers."""
    service = SafetyStockService()
    try:
        payload = service.get_item_suppliers(
            g.current_user,
            code=code,
            branch=request.args.get("branch"),
        )
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200
