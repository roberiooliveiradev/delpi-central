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
from app.interfaces.http.auth_decorators import require_permission, require_unit

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
@require_permission("supplies.purchase-requests.access")
@require_unit("branch")
def list_portal_purchase_requests():
    """operationId: list_portal_purchase_requests — C1 gateway; CC fail-closed in PR-api."""
    try:
        payload = _GATEWAY.list_purchase_requests(
            access_token=_access_token(),
            query_string=request.query_string.decode("utf-8") or None,
        )
    except PurchaseRequestsGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(_unwrap_data(payload)), 200


@purchase_requests_bp.get("/purchase-requests/requesters")
@require_permission("supplies.purchase-requests.access")
@require_unit("branch")
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
@require_permission("supplies.purchase-requests.access")
@require_permission("supplies.purchase-requests.export")
@require_unit("branch")
def export_portal_purchase_requests():
    """operationId: export_portal_purchase_requests — CSV via list hop (CC in PR-api)."""
    branch = (request.args.get("branch") or "").strip()
    if not branch:
        raise AuthorizationError("Forbidden")

    max_pages = 20
    page_size = min(int(request.args.get("page_size") or 200), 200)
    base_pairs: list[tuple[str, str]] = []
    for key in request.args.keys():
        if key in {"page", "page_size", "format"}:
            continue
        for value in request.args.getlist(key):
            base_pairs.append((key, value))

    rows: list[dict[str, Any]] = []
    try:
        for page in range(1, max_pages + 1):
            pairs = list(base_pairs)
            pairs.append(("page", str(page)))
            pairs.append(("page_size", str(page_size)))
            payload = _GATEWAY.list_purchase_requests(
                access_token=_access_token(),
                query_string=urlencode(pairs, doseq=True),
            )
            data = _unwrap_data(payload)
            items = data.get("items") if isinstance(data, dict) else None
            if not isinstance(items, list) or not items:
                break
            for item in items:
                if isinstance(item, dict):
                    rows.append(item)
            total = int(data.get("total") or 0) if isinstance(data, dict) else 0
            if page * page_size >= total:
                break
    except PurchaseRequestsGatewayError as exc:
        return _gateway_error_response(exc)

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
    for item in rows:
        requester = item.get("requester") if isinstance(item.get("requester"), dict) else {}
        cost_center = item.get("cost_center") if isinstance(item.get("cost_center"), dict) else {}
        approval = item.get("approval") if isinstance(item.get("approval"), dict) else {}
        derived = item.get("derived") if isinstance(item.get("derived"), dict) else {}
        writer.writerow(
            [
                item.get("branch") or branch,
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

    filename = f"purchase-requests-{branch}.csv"
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
@require_permission("supplies.purchase-requests.access")
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
