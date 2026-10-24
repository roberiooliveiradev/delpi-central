from flask import Blueprint, Response, g, jsonify, request

from app.application.services.user_profile_service import UserProfileService
from app.application.security.supplies_permissions import (
    can_enter_shell,
    can_use_operations,
)
from app.interfaces.http.auth_decorators import require_policy

users_bp = Blueprint("users", __name__)


@users_bp.get("/users/<user_id>/profile")
@require_policy(can_enter_shell)
def get_supplies_user_profile(user_id: str):
    """operationId: get_supplies_user_profile — AuthZ fino self|admin no service."""
    service = UserProfileService()
    return jsonify(service.get(g.current_user, user_id)), 200


@users_bp.get("/users/<user_id>/related-requests")
@require_policy(can_use_operations)
def get_supplies_user_related_requests(user_id: str):
    """operationId: get_supplies_user_related_requests — SCs do vínculo do target.

    Filtro `branch` opcional restringe às unidades do actor (fail-closed no
    service quando fornecido); o vínculo resolvido é sempre o do target —
    nunca o actor como substituto.
    """

    def _int(name: str, default: int) -> int:
        try:
            return int(request.args.get(name) or default)
        except (TypeError, ValueError):
            return default

    service = UserProfileService()
    payload = service.related_purchase_requests(
        g.current_user,
        user_id,
        branches=request.args.getlist("branch"),
        page=_int("page", 1),
        page_size=_int("page_size", 5),
        sort_by=request.args.get("sort_by"),
        sort_dir=request.args.get("sort_dir"),
    )
    return jsonify(payload), 200


@users_bp.get("/users/<user_id>/photo")
@require_policy(can_use_operations)
def get_supplies_user_photo(user_id: str):
    """operationId: get_supplies_user_photo — proxy S2S; self|admin no service."""
    service = UserProfileService()
    photo = service.photo(g.current_user, user_id)
    if not photo:
        return jsonify({"detail": "Not found", "code": "not_found"}), 404
    content, content_type, file_name = photo
    return Response(
        content,
        status=200,
        mimetype=content_type or "image/jpeg",
        headers={
            "Content-Disposition": f'inline; filename="{file_name}"',
            "Cache-Control": "private, max-age=300",
        },
    )


@users_bp.patch("/users/<user_id>/profile")
@require_policy(can_enter_shell)
def patch_supplies_user_profile(user_id: str):
    """operationId: patch_supplies_user_profile — self only."""
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"detail": "Invalid body", "code": "unprocessable"}), 422
    service = UserProfileService()
    return jsonify(service.patch(g.current_user, user_id, payload)), 200
