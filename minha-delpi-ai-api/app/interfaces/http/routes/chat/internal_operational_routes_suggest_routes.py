"""S2S: sugestão dry-run de rotas operacionais para apps (ex.: TV Dashboard)."""

from __future__ import annotations

from flask import jsonify, request

from app.interfaces.http.routes.chat.shared import chat_bp


def _require_internal_service_token():
    from delpi_auth.service_token import headers_have_valid_internal_service_token

    if headers_have_valid_internal_service_token(dict(request.headers)):
        return None
    return jsonify({"success": False, "message": "Unauthorized service"}), 401


@chat_bp.post("/internal/operational-routes/suggest")
def suggest_operational_routes_internal():
    """S2S: NL → ranked operationIds (sem executar actions)."""
    denied = _require_internal_service_token()
    if denied is not None:
        return denied

    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query") or payload.get("message") or "").strip()
    if not query:
        return jsonify({"ok": False, "error": "query required"}), 400

    try:
        limit = int(payload.get("limit") or 5)
    except (TypeError, ValueError):
        limit = 5
    limit = max(1, min(limit, 20))

    allowed_raw = payload.get("allowedActionIds") or payload.get("allowed_action_ids")
    allowed_action_ids = None
    if isinstance(allowed_raw, list):
        allowed_action_ids = [str(item).strip() for item in allowed_raw if str(item).strip()]

    from app.composition.chat_composer import make_suggest_operational_routes_use_case

    result = make_suggest_operational_routes_use_case().execute(
        query,
        limit=limit,
        allowed_action_ids=allowed_action_ids,
    )
    return jsonify(result), 200
