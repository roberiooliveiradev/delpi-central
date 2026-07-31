"""S2S: dry-run de parâmetros operacionais a partir de NL (TV data builder)."""

from __future__ import annotations

from flask import jsonify, request

from app.interfaces.http.routes.chat.shared import chat_bp


def _require_internal_service_token():
    from delpi_auth.service_token import headers_have_valid_internal_service_token

    if headers_have_valid_internal_service_token(dict(request.headers)):
        return None
    return jsonify({"success": False, "message": "Unauthorized service"}), 401


@chat_bp.post("/internal/operational-routes/suggest-params")
def suggest_operational_route_params_internal():
    """S2S: NL → params candidatos (sem executar action)."""
    denied = _require_internal_service_token()
    if denied is not None:
        return denied

    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query") or payload.get("message") or "").strip()
    if not query:
        return jsonify({"ok": False, "error": "query required"}), 400

    operation_id = str(payload.get("operationId") or payload.get("operation_id") or "").strip()
    action: dict = {}
    if operation_id:
        from app.composition.repository_composer import make_external_action_repository

        repo = make_external_action_repository()
        for row in repo.list_actions(provider_key="api-delpi"):
            if str(row.get("operationId") or "") == operation_id:
                action = dict(row)
                break

    from app.domain.services.operational_api_parameter_builder_service import (
        OperationalApiParameterBuilderService,
    )

    builder = OperationalApiParameterBuilderService()
    try:
        params = builder.build_date_branch(action or {"parameters": []}, message=query)
    except Exception:  # noqa: BLE001
        params = {}

    if not isinstance(params, dict):
        params = {}

    return jsonify(
        {
            "ok": True,
            "query": query,
            "operationId": operation_id or None,
            "params": params,
        }
    ), 200
