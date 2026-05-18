# app/interfaces/http/me_controller.py

from uuid import UUID
from flask import Blueprint, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import (
    SqlAlchemyUnitOfWork,
)

from app.interfaces.http.security.authorization import require_auth
from app.interfaces.http.utils.errors import api_error

from app.application.use_cases.list_user_apps_use_case import (
    ListUserAppsUseCase,
)

from app.application.use_cases.list_favorite_apps_use_case import (
    ListFavoriteAppsUseCase,
)

from app.application.use_cases.add_favorite_app_use_case import (
    AddFavoriteAppUseCase,
)

from app.application.use_cases.remove_favorite_app_use_case import (
    RemoveFavoriteAppUseCase,
)

from app.application.use_cases.list_unread_notifications_use_case import (
    ListUnreadNotificationsUseCase,
)

from app.application.use_cases.mark_notification_read_use_case import (
    MarkNotificationReadUseCase,
    NotificationAccessDeniedError,
    NotificationNotFoundError,
)

from app.application.use_cases.mark_all_notifications_read_use_case import (
    MarkAllNotificationsReadUseCase,
)

from app.application.use_cases.notify_user_use_case import (
    NotifyUserUseCase,
)

me_bp = Blueprint("me", __name__)


# ==========================================================
# GET /me
# ==========================================================

@me_bp.route("/me", methods=["GET"])
@require_auth()
def get_me():
    user = g.current_user

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "roles": getattr(user, "roles", []),
        "groups": getattr(user, "groups", []),
        "permissions": getattr(user, "permissions", []),
        "is_superadmin": getattr(user, "is_superadmin", False),
    }), 200


# ==========================================================
# GET /me/apps
# ==========================================================

@me_bp.route("/me/apps", methods=["GET"])
@require_auth()
def get_my_apps():
    user = g.current_user

    with SqlAlchemyUnitOfWork() as uow:
        uc = ListUserAppsUseCase(uow.app_queries)

        result = uc.execute(
            permissions=user.permissions,
            is_superadmin=user.is_superadmin,
        )

    return jsonify(result), 200


# ==========================================================
# FAVORITES
# ==========================================================

@me_bp.route("/me/apps/favorites", methods=["GET"])
@require_auth()
def list_favorites():
    user = g.current_user

    with SqlAlchemyUnitOfWork() as uow:
        uc = ListFavoriteAppsUseCase(uow)

        result = uc.execute(
            user_id=str(user.id),
            permissions=user.permissions,
            is_superadmin=user.is_superadmin,
        )

    return jsonify(result), 200


@me_bp.route("/me/apps/favorites/<app_id>", methods=["POST"])
@require_auth()
def add_favorite(app_id: str):
    user = g.current_user

    with SqlAlchemyUnitOfWork() as uow:
        uc = AddFavoriteAppUseCase(uow)

        uc.execute(
            user_id=str(user.id),
            app_id=app_id,
        )

    return jsonify({"ok": True}), 200


@me_bp.route("/me/apps/favorites/<app_id>", methods=["DELETE"])
@require_auth()
def remove_favorite(app_id: str):
    user = g.current_user

    with SqlAlchemyUnitOfWork() as uow:
        uc = RemoveFavoriteAppUseCase(uow)

        uc.execute(
            user_id=str(user.id),
            app_id=app_id,
        )

    return jsonify({"ok": True}), 200


# ==========================================================
# NOTIFICATIONS
# ==========================================================

@me_bp.route("/me/notifications", methods=["GET"])
@require_auth()
def list_notifications():
    user = g.current_user

    with SqlAlchemyUnitOfWork() as uow:
        uc = ListUnreadNotificationsUseCase(uow)
        result = uc.execute(user_id=user.id)

    return jsonify([
        {
            "id": str(n.id),
            "user_id": str(n.user_id),
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "read": n.read,
            "createdAt": n.created_at.isoformat() + "Z",
        }
        for n in result
    ]), 200


@me_bp.route("/me/notifications/<notification_id>/read", methods=["POST"])
@require_auth()
def mark_notification_read(notification_id: str):
    user = g.current_user

    try:
        notification_uuid = UUID(notification_id)
    except ValueError:
        return api_error("invalid_id", "Invalid notification id", status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = MarkNotificationReadUseCase(uow)
            uc.execute(notification_uuid, actor_user_id=str(user.id))

        return jsonify({"ok": True}), 200

    except NotificationNotFoundError:
        return api_error("not_found", "Notification not found", status=404)
    except NotificationAccessDeniedError:
        return api_error("forbidden", "Notification does not belong to current user", status=403)
    except Exception as e:
        return api_error("mark_failed", str(e))


@me_bp.route("/me/notifications/read-all", methods=["POST"])
@require_auth()
def mark_all_notifications_read():
    user = g.current_user

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = MarkAllNotificationsReadUseCase(uow)
            uc.execute(user_id=user.id)

        return jsonify({"ok": True}), 200

    except Exception as e:
        return api_error("mark_all_failed", str(e))


# ==========================================================
# TEST NOTIFICATION (DEV)
# ==========================================================

@me_bp.route("/me/notifications/test", methods=["POST"])
@require_auth()
def test_notification():
    user = g.current_user

    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = NotifyUserUseCase(uow)

            result = uc.execute(
                user_id=str(user.id),
                title="Teste tempo real",
                message="Notificação disparada via endpoint",
                type="success",
            )

        return jsonify(
            {
                "ok": True,
                "createdCount": result.created_count,
            }
        ), 200

    except Exception as e:
        return api_error("notify_failed", str(e))


# ==========================================================
# DASHBOARD
# ==========================================================

@me_bp.route("/me/dashboard", methods=["GET"])
@require_auth()
def get_dashboard():
    user = g.current_user

    with SqlAlchemyUnitOfWork() as uow:
        uc = ListUserAppsUseCase(app_query=uow.app_queries)

        apps = uc.execute(
            permissions=user.permissions,
            is_superadmin=user.is_superadmin,
        )

    return jsonify({
        "appsCount": len(apps),
        "apps": apps,
    }), 200