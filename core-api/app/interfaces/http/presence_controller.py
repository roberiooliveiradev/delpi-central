# app/interfaces/http/presence_controller.py

from flask import Blueprint, current_app, jsonify

from app.application.use_cases.admin.list_online_users_use_case import (
    ListOnlineUsersUseCase,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.presence.presence_store_provider import is_user_presence_enabled
from app.interfaces.http.security.authorization import require_superadmin
from app.interfaces.http.utils.errors import api_error

admin_presence_bp = Blueprint("admin_presence", __name__)


@admin_presence_bp.route("/admin/users/presence", methods=["GET"])
@require_superadmin()
def list_online_users():
    if not is_user_presence_enabled():
        return jsonify({"items": [], "total": 0, "ttlSeconds": 0, "enabled": False}), 200

    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = ListOnlineUsersUseCase(uow).execute()

        return (
            jsonify(
                {
                    **result,
                    "ttlSeconds": int(current_app.config.get("USER_PRESENCE_TTL_SECONDS", 90)),
                    "enabled": True,
                }
            ),
            200,
        )
    except Exception as exc:
        return api_error("presence_list_failed", str(exc))
