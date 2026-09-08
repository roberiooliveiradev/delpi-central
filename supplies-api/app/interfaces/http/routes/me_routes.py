from flask import Blueprint, g, jsonify, request

from app.application.services.capability_resolution_service import (
    CapabilityResolutionService,
)
from app.application.services.preferences_service import PreferencesService
from app.interfaces.http.auth_decorators import require_permission

me_bp = Blueprint("me", __name__)


@me_bp.get("/me/capabilities")
@require_permission("supplies.portal.access")
def get_capabilities():
    service = CapabilityResolutionService()
    return jsonify(service.resolve(g.current_user)), 200


@me_bp.get("/me/preferences")
@require_permission("supplies.portal.access")
def get_preferences():
    service = PreferencesService()
    return jsonify(service.get(g.current_user)), 200


@me_bp.patch("/me/preferences")
@require_permission("supplies.portal.access")
def patch_preferences():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"detail": "Invalid body", "code": "unprocessable"}), 422
    service = PreferencesService()
    return jsonify(service.patch(g.current_user, payload)), 200
