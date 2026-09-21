from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from app.application.security.supplies_permissions import can_use_operations
from app.application.services.late_deliveries_composition_service import (
    LateDeliveriesCompositionService,
)
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.interfaces.http.auth_decorators import require_policy

deliveries_bp = Blueprint("deliveries", __name__)


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


@deliveries_bp.get("/deliveries/late")
@require_policy(can_use_operations)
def list_late_deliveries():
    """operationId: list_portal_late_deliveries — MP receipt punctuality panel via api-delpi."""
    service = LateDeliveriesCompositionService()
    try:
        payload = service.compose(
            g.current_user,
            branches=_branch_args(),
            status=request.args.get("status"),
            start_date=request.args.get("start_date"),
            end_date=request.args.get("end_date"),
            page=request.args.get("page"),
            page_size=request.args.get("page_size"),
            sort_by=request.args.get("sort_by"),
            sort_dir=request.args.get("sort_dir"),
        )
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200
