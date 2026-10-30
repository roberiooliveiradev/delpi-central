"""Consumption audit BFF (GLPI #1353) — OP × operation detail via api-delpi.

AuthZ: ``supplies.access`` (Core effective) + unit scope 01|02. Technical
identity: individual S2S credential via ``DelpiS2SApiGateway`` — the shared
legacy token is never used and no local recalculation of Protheus rules is
performed; the BFF only projects the producer payload.
"""

from __future__ import annotations

import logging
import re

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
