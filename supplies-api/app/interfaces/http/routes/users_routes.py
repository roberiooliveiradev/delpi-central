from flask import Blueprint, g, jsonify, request

from app.application.services.user_profile_service import UserProfileService
from app.interfaces.http.auth_decorators import require_permission

users_bp = Blueprint("users", __name__)


@users_bp.get("/users/<user_id>/profile")
@require_permission("supplies.portal.access")
def get_supplies_user_profile(user_id: str):
    """operationId: get_supplies_user_profile — AuthZ fino self|admin no service."""
    service = UserProfileService()
    return jsonify(service.get(g.current_user, user_id)), 200


@users_bp.patch("/users/<user_id>/profile")
@require_permission("supplies.portal.access")
def patch_supplies_user_profile(user_id: str):
    """operationId: patch_supplies_user_profile — self only."""
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"detail": "Invalid body", "code": "unprocessable"}), 422
    service = UserProfileService()
    return jsonify(service.patch(g.current_user, user_id, payload)), 200
