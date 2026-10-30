"""Supplier master-data BFF — list, detail, gated create/update via api-delpi.

AuthZ: ``supplies.access`` (Core effective). Technical identity: individual S2S
credential via ``DelpiS2SApiGateway``; the shared legacy token is never used.
Writes are single-attempt, gate-guarded upstream, and never declare persistence
from an ACK alone.
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.application.security.supplies_permissions import (
    can_administer,
    can_use_operations,
)
from app.application.services.suppliers_dto import (
    classify_supplier_write_error,
    normalize_operation_id,
    normalize_postal_code,
    normalize_supplier_id,
    project_detail,
    project_integration_status,
    project_list_envelope,
    project_operation,
    project_postal_lookup,
    sanitize_field_errors,
    sanitize_post_body,
    sanitize_put_body,
    SAFE_UPSTREAM_DETAIL_PREFIXES,
    SUPPLIER_CATALOG_KINDS,
    SUPPLIER_CATALOG_LIMIT_MAX,
    SUPPLIER_CATALOG_QUERY_KEYS,
    SUPPLIER_LIST_QUERY_KEYS,
)
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope
from app.infrastructure.gateways.delpi_s2s_gateway import DelpiS2SApiGateway
from app.interfaces.http.auth_decorators import require_policy
from flask import g

suppliers_bp = Blueprint("suppliers", __name__)

logger = logging.getLogger(__name__)

_GATEWAY = DelpiS2SApiGateway()

# CEP — o BFF nunca chama providers externos; a api-delpi é a owner da
# integração (INT-CEP-01). Validação local só rejeita formato inválido
# antes do S2S (normalize_postal_code canônico em suppliers_dto).


def _access_token() -> str:
    return g.current_user.access_token or ""


# Sanitized upstream-detail prefixes and field-error projection live in
# suppliers_dto (canonical owner) — shared by this route and the SURI MCP
# execute surface.
_SAFE_UPSTREAM_DETAIL_PREFIXES = SAFE_UPSTREAM_DETAIL_PREFIXES
_sanitize_field_errors = sanitize_field_errors


def _gateway_error_response(exc: DelpiApiGatewayError, *, write: bool = False):
    if write:
        # Single canonical classification shared with the SURI MCP execute
        # surface — the HTTP body shape stays exactly the contract above.
        classification = classify_supplier_write_error(exc)
        status = classification["status"]
        if status == 403:
            # Propagate the upstream denial code so the response identifies
            # the denial owner (e.g. S2S_SCOPE_DENIED) instead of collapsing
            # into the same "forbidden" the BFF uses for its own
            # supplies.access denial.
            logger.warning(
                "suppliers_upstream_denied status=403 upstream_code=%s",
                exc.code or "none",
            )
        body = {
            "detail": classification["detail"],
            "code": classification["code"],
        }
        if classification["fields"]:
            body["fields"] = classification["fields"]
        # outcome is published on the write contract for every status except
        # the transport-level 401/403/404 bodies (historical shape preserved).
        if status not in (401, 403, 404):
            body["outcome"] = classification["outcome"]
        return jsonify(body), status
    if exc.status_code is None:
        return jsonify(
            {
                "detail": "api-delpi unreachable",
                "code": "upstream_unreachable",
            }
        ), 504
    status = exc.status_code
    if status == 401:
        return jsonify({"detail": "Unauthorized", "code": "unauthorized"}), 401
    if status == 403:
        logger.warning(
            "suppliers_upstream_denied status=403 upstream_code=%s",
            exc.code or "none",
        )
        return jsonify(
            {
                "detail": "Forbidden",
                "code": exc.code or "upstream_forbidden",
            }
        ), 403
    if status == 404:
        return jsonify({"detail": "Not Found", "code": "not_found"}), 404
    if status < 500:
        detail = str(exc)
        safe_code = bool(
            exc.code
            and str(exc.code).startswith(_SAFE_UPSTREAM_DETAIL_PREFIXES)
        )
        if safe_code and exc.upstream_message:
            detail = exc.upstream_message[:300]
        payload = {
            "detail": detail,
            "code": exc.code or "upstream_client_error",
        }
        if safe_code:
            field_errors = _sanitize_field_errors(exc.fields)
            if field_errors:
                payload["fields"] = field_errors
        return jsonify(payload), status
    return jsonify(
        {
            "detail": "api-delpi unavailable",
            "code": exc.code or "bad_gateway",
        }
    ), 502


def _validation_error(exc: ValueError):
    return jsonify({"detail": str(exc), "code": "invalid_request"}), 422


@suppliers_bp.get("/suppliers")
@require_policy(can_use_operations)
def list_suppliers():
    """operationId: list_portal_suppliers — paged SA2 search via api-delpi."""
    params = {
        key: request.args[key]
        for key in SUPPLIER_LIST_QUERY_KEYS
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


@suppliers_bp.get("/suppliers/catalogs/<catalog>")
@require_policy(can_use_operations)
def list_supplier_catalog(catalog: str):
    """operationId: list_portal_supplier_catalog — catálogos SA2 via api-delpi."""
    kind = (catalog or "").strip().lower()
    if kind not in SUPPLIER_CATALOG_KINDS:
        return jsonify(
            {"detail": "Unknown supplier catalog", "code": "invalid_request"}
        ), 422
    params = {
        key: request.args[key]
        for key in SUPPLIER_CATALOG_QUERY_KEYS
        if (request.args.get(key) or "").strip()
    }
    limit = params.get("limit")
    if limit is not None:
        try:
            params["limit"] = str(
                max(1, min(int(limit), SUPPLIER_CATALOG_LIMIT_MAX))
            )
        except ValueError:
            return _validation_error(ValueError("invalid 'limit'"))
    try:
        payload = _GATEWAY.get(
            f"/supplies/supplier-catalogs/{kind}",
            access_token=_access_token(),
            params=params,
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(unwrap_delpi_envelope(payload)), 200


@suppliers_bp.get("/suppliers/postal-codes/<postal_code>")
@require_policy(can_use_operations)
def lookup_postal_code(postal_code: str):
    """operationId: lookup_portal_postal_code — proposta de endereço por CEP.

    Proposta somente: nada é persistido e nenhum campo é alterado sem
    confirmação do usuário no MFE.
    """
    try:
        digits = normalize_postal_code(postal_code)
    except ValueError as exc:
        return _validation_error(exc)
    try:
        payload = _GATEWAY.get(
            f"/addresses/postal-codes/{digits}",
            access_token=_access_token(),
        )
    except DelpiApiGatewayError as exc:
        if exc.status_code is None or exc.status_code == 504:
            return jsonify(
                {
                    "detail": "Postal address provider unreachable",
                    "code": "provider_unreachable",
                }
            ), 504
        if exc.status_code == 400:
            return _validation_error(ValueError("CEP inválido"))
        if exc.status_code in (401, 403):
            return _gateway_error_response(exc)
        return jsonify(
            {
                "detail": "Postal address provider error",
                "code": "provider_error",
            }
        ), 502
    data = unwrap_delpi_envelope(payload) or {}
    return jsonify(project_postal_lookup(data, digits)), 200


@suppliers_bp.get("/suppliers/integration-status")
@require_policy(can_administer)
def get_suppliers_integration_status():
    """operationId: get_portal_suppliers_integration_status — read-only diagnostic.

    Administrative surface (supplies.manage): proxies the api-delpi Protheus
    REST diagnostic and republishes only the sanitized allowlist — never
    URLs, tokens, credentials or upstream internals. Performs no ERP write.
    """
    try:
        payload = _GATEWAY.get(
            "/integrations/protheus/status",
            access_token=_access_token(),
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(project_integration_status(unwrap_delpi_envelope(payload))), 200


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


@suppliers_bp.get("/suppliers/operations/<operation_id>")
@require_policy(can_use_operations)
def get_supplier_operation(operation_id: str):
    """operationId: get_portal_supplier_operation — tracked write status.

    Read-only proxy for the api-delpi integration-tracking projection.
    api-delpi enforces caller-app + actor binding; the BFF only minimizes
    the payload for UX consumption (no state machine, no tracking storage).
    """
    try:
        normalized = normalize_operation_id(operation_id)
    except ValueError as exc:
        return _validation_error(exc)
    try:
        payload = _GATEWAY.get(
            f"/integrations/operations/{normalized}",
            access_token=_access_token(),
        )
    except DelpiApiGatewayError as exc:
        return _gateway_error_response(exc)
    data = unwrap_delpi_envelope(payload)
    return jsonify(project_operation(data)), 200


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
            "operation_id": data.get("operation_id"),
            "tracking_warning": data.get("tracking_warning"),
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
            "operation_id": data.get("operation_id"),
            "tracking_warning": data.get("tracking_warning"),
            "data": data,
        }
    ), 200
