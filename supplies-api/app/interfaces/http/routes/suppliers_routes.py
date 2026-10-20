"""Supplier master-data BFF — list, detail, gated create/update via api-delpi.

AuthZ: ``supplies.access`` (Core effective). Technical identity: individual S2S
credential via ``DelpiS2SApiGateway``; the shared legacy token is never used.
Writes are single-attempt, gate-guarded upstream, and never declare persistence
from an ACK alone.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.application.security.supplies_permissions import can_use_operations
from app.application.services.suppliers_dto import (
    normalize_supplier_id,
    project_detail,
    project_list_envelope,
    sanitize_post_body,
    sanitize_put_body,
)
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.infrastructure.gateways.delpi_s2s_gateway import DelpiS2SApiGateway
from app.interfaces.http.auth_decorators import require_policy
from flask import g

suppliers_bp = Blueprint("suppliers", __name__)

logger = logging.getLogger(__name__)

_GATEWAY = DelpiS2SApiGateway()

_LIST_QUERY_KEYS = (
    "query",
    "state",
    "blocked",
    "page",
    "page_size",
    "sort_by",
    "sort_dir",
)


def _access_token() -> str:
    return g.current_user.access_token or ""


def _gateway_error_response(exc: DelpiApiGatewayError, *, write: bool = False):
    upstream_code = exc.code
    if write and upstream_code and upstream_code.endswith("_DISABLED"):
        # Feature gate closed upstream — explicit operational block, no write sent.
        return jsonify(
            {
                "detail": "Supplier write is disabled by gate",
                "code": upstream_code,
                "outcome": "write_disabled",
            }
        ), 503
    if exc.status_code is None:
        # Timeout / connection failure — write outcome is indeterminate.
        payload = {
            "detail": "api-delpi unreachable",
            "code": "upstream_unreachable",
        }
        if write:
            payload["outcome"] = "indeterminate"
        return jsonify(payload), 504
    status = exc.status_code
    if status == 401:
        return jsonify({"detail": "Unauthorized", "code": "unauthorized"}), 401
    if status == 403:
        # Propagate the upstream denial code so the response identifies the
        # denial owner (e.g. S2S_SCOPE_DENIED) instead of collapsing into the
        # same "forbidden" the BFF uses for its own supplies.access denial.
        logger.warning(
            "suppliers_upstream_denied status=403 upstream_code=%s",
            upstream_code or "none",
        )
        return jsonify(
            {
                "detail": "Forbidden",
                "code": upstream_code or "upstream_forbidden",
            }
        ), 403
    if status == 404:
        return jsonify({"detail": "Not Found", "code": "not_found"}), 404
    if status < 500:
        payload = {
            "detail": str(exc),
            "code": upstream_code or "upstream_client_error",
        }
        if write:
            payload["outcome"] = "rejected"
        return jsonify(payload), status
    payload = {
        "detail": "api-delpi unavailable",
        "code": upstream_code or "bad_gateway",
    }
    if write:
        payload["outcome"] = "indeterminate"
    return jsonify(payload), 502


def _validation_error(exc: ValueError):
    return jsonify({"detail": str(exc), "code": "invalid_request"}), 422


@suppliers_bp.get("/suppliers")
@require_policy(can_use_operations)
def list_suppliers():
    """operationId: list_portal_suppliers — paged SA2 search via api-delpi."""
    params = {
        key: request.args[key]
        for key in _LIST_QUERY_KEYS
        if (request.args.get(key) or "").strip()
    }
    try:
        payload = _GATEWAY.get(
            "/supplies/suppliers",
            access_token=_access_token(),
            params=params,
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    data = unwrap_delpi_envelope(payload)
    return jsonify(project_list_envelope(data)), 200


@suppliers_bp.get("/suppliers/<code>/<store>")
@require_policy(can_use_operations)
def get_supplier(code: str, store: str):
    """operationId: get_portal_supplier — supplier detail via Protheus REST."""
    try:
        supplier_id = normalize_supplier_id(code, store)
    except ValueError as exc:
        return _validation_error(exc)
    try:
        payload = _GATEWAY.get(
            f"/integrations/protheus/suppliers/{supplier_id}",
            access_token=_access_token(),
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(project_detail(unwrap_delpi_envelope(payload))), 200


@suppliers_bp.post("/suppliers")
@require_policy(can_use_operations)
def create_supplier():
    """operationId: create_portal_supplier — gated Protheus POST forwarder."""
    try:
        fornecedor = sanitize_post_body(request.get_json(silent=True))
    except ValueError as exc:
        return _validation_error(exc)
    try:
        payload = _GATEWAY.post(
            "/integrations/protheus/suppliers",
            access_token=_access_token(),
            json_body={"fornecedor": fornecedor},
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc, write=True)
    data = unwrap_delpi_envelope(payload)
    if not isinstance(data, dict):
        data = {}
    return jsonify(
        {
            "acknowledged": True,
            "persistence_proven": bool(data.get("creation_confirmed")),
            "data": data,
        }
    ), 200


@suppliers_bp.put("/suppliers/<code>/<store>")
@require_policy(can_use_operations)
def update_supplier(code: str, store: str):
    """operationId: update_portal_supplier — allowlisted field edit via PUT."""
    try:
        supplier_id = normalize_supplier_id(code, store)
        fornecedor = sanitize_put_body(request.get_json(silent=True))
    except ValueError as exc:
        return _validation_error(exc)
    try:
        payload = _GATEWAY.put(
            f"/integrations/protheus/suppliers/{supplier_id}",
            access_token=_access_token(),
            json_body={"fornecedor": fornecedor},
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc, write=True)
    data = unwrap_delpi_envelope(payload)
    if not isinstance(data, dict):
        data = {}
    return jsonify(
        {
            "acknowledged": bool(data.get("update_acknowledged", True)),
            "persistence_proven": bool(data.get("persistence_proven")),
            "data": data,
        }
    ), 200
