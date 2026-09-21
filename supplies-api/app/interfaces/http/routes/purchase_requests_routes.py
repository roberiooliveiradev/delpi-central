from __future__ import annotations

import csv
import io
from typing import Any
from urllib.parse import urlencode

from flask import Blueprint, Response, g, jsonify, request

from app.domain.exceptions import AuthorizationError
from app.infrastructure.gateways.purchase_requests_gateway import (
    PurchaseRequestsGateway,
    PurchaseRequestsGatewayError,
)
from app.infrastructure.export.purchase_requests_xlsx import (
    EXPORT_FILENAME as XLSX_FILENAME,
    XLSX_MIME,
    build_purchase_requests_xlsx,
)
from app.application.security.supplies_permissions import (
    can_export_purchase_requests,
    can_use_purchase_requests,
)
from app.interfaces.http.auth_decorators import require_policy, require_unit, require_units

purchase_requests_bp = Blueprint("purchase_requests", __name__)

_GATEWAY = PurchaseRequestsGateway()


def _access_token() -> str:
    return g.current_user.access_token or ""


def _query_string_without_keys(*drop: str) -> str:
    pairs: list[tuple[str, str]] = []
    drop_set = {key for key in drop}
    for key in request.args.keys():
        if key in drop_set:
            continue
        for value in request.args.getlist(key):
            pairs.append((key, value))
    return urlencode(pairs, doseq=True)


def _gateway_error_response(exc: PurchaseRequestsGatewayError):
    status = exc.status_code or 502
    if status == 401:
        return jsonify({"detail": "Unauthorized", "code": "unauthorized"}), 401
    if status == 403:
        return jsonify({"detail": "Forbidden", "code": "forbidden"}), 403
    if status == 404:
        message = "Not Found"
        if isinstance(exc.payload, dict) and exc.payload.get("message"):
            message = str(exc.payload["message"])
        return jsonify({"detail": message, "code": "not_found"}), 404
    if status < 500:
        detail = "Upstream client error"
        if isinstance(exc.payload, dict) and exc.payload.get("message"):
            detail = str(exc.payload["message"])
        return jsonify({"detail": detail, "code": "upstream_client_error"}), status
    return jsonify({"detail": "purchase-requests-api unavailable", "code": "bad_gateway"}), 502


def _unwrap_data(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload.get("data")
    return payload


@purchase_requests_bp.get("/purchase-requests")
@require_policy(can_use_purchase_requests)
@require_units("branch")
def list_portal_purchase_requests():
    """operationId: list_portal_purchase_requests — BFF; supplies.access vê o recorte global."""
    try:
        payload = _GATEWAY.list_purchase_requests(
            access_token=_access_token(),
            query_string=request.query_string.decode("utf-8") or None,
        )
    except PurchaseRequestsGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(_unwrap_data(payload)), 200


@purchase_requests_bp.get("/purchase-requests/summary")
@require_policy(can_use_purchase_requests)
@require_units("branch")
def summarize_portal_purchase_requests():
    """operationId: summarize_portal_purchase_requests — BFF; counts stay on the owner."""
    try:
        payload = _GATEWAY.get_summary(
            access_token=_access_token(),
            query_string=request.query_string.decode("utf-8") or None,
        )
    except PurchaseRequestsGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(_unwrap_data(payload)), 200


@purchase_requests_bp.get("/purchase-requests/requesters")
@require_policy(can_use_purchase_requests)
@require_units("branch")
def list_portal_purchase_request_requesters():
    """operationId: list_portal_purchase_request_requesters"""
    try:
        payload = _GATEWAY.list_requesters(
            access_token=_access_token(),
            query_string=request.query_string.decode("utf-8") or None,
        )
    except PurchaseRequestsGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(_unwrap_data(payload)), 200


@purchase_requests_bp.get("/purchase-requests/export")
@require_policy(can_export_purchase_requests)
@require_units("branch")
def export_portal_purchase_requests():
    """operationId: export_portal_purchase_requests — CSV default, XLSX via format=."""
    branches = [item.strip() for item in request.args.getlist("branch") if item.strip()]
    if not branches:
        raise AuthorizationError("Forbidden")

    export_format = (request.args.get("format") or "csv").strip().lower()
    if export_format not in {"csv", "xlsx"}:
        return jsonify({"detail": "Unsupported export format", "code": "unprocessable"}), 422

    pairs: list[tuple[str, str]] = []
    for key in request.args.keys():
        if key in {"page", "page_size", "format"}:
            continue
        for value in request.args.getlist(key):
            pairs.append((key, value))

    try:
        payload = _GATEWAY.export_purchase_requests(
            access_token=_access_token(),
            query_string=urlencode(pairs, doseq=True),
        )
    except PurchaseRequestsGatewayError as exc:
        return _gateway_error_response(exc)

    data = _unwrap_data(payload)
    rows = data.get("items") if isinstance(data, dict) else []
    if not isinstance(rows, list):
        rows = []

    if export_format == "xlsx":
        body = build_purchase_requests_xlsx([item for item in rows if isinstance(item, dict)])
        return Response(
            body,
            status=200,
            mimetype=XLSX_MIME,
            headers={
                "Content-Disposition": f'attachment; filename="{XLSX_FILENAME}"',
                "Cache-Control": "no-store",
            },
        )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "branch",
            "request_number",
            "request_item",
            "product_code",
            "product_description",
            "requester",
            "cost_center",
            "issue_date",
            "overall_stage",
            "approval_status",
        ]
    )
    fallback_branch = branches[0]
    for item in rows:
        if not isinstance(item, dict):
            continue
        requester = item.get("requester") if isinstance(item.get("requester"), dict) else {}
        cost_center = item.get("cost_center") if isinstance(item.get("cost_center"), dict) else {}
        approval = item.get("approval") if isinstance(item.get("approval"), dict) else {}
        derived = item.get("derived") if isinstance(item.get("derived"), dict) else {}
        writer.writerow(
            [
                item.get("branch") or fallback_branch,
                item.get("request_number") or "",
                item.get("request_item") or "",
                item.get("product_code") or "",
                item.get("product_description") or "",
                (requester or {}).get("name") or "",
                (cost_center or {}).get("code") or item.get("cost_center_code") or "",
                item.get("request_issue_date") or item.get("issue_date") or "",
                (derived or {}).get("overall_stage") or item.get("overall_stage") or "",
                (approval or {}).get("status") or "",
            ]
        )

    filename = "purchase-requests.csv"
    return Response(
        buffer.getvalue(),
        status=200,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@purchase_requests_bp.get("/purchase-requests/<branch>/<request_number>")
@require_policy(can_use_purchase_requests)
@require_unit("branch")
def get_portal_purchase_request(branch: str, request_number: str):
    """operationId: get_portal_purchase_request"""
    qs = _query_string_without_keys("branch")
    try:
        payload = _GATEWAY.get_purchase_request(
            access_token=_access_token(),
            branch=branch,
            request_number=request_number,
            query_string=qs or None,
        )
    except PurchaseRequestsGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(_unwrap_data(payload)), 200
