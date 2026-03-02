# app/interfaces/http/notification_controller.py

from uuid import UUID
from flask import Blueprint, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.application.use_cases.list_unread_notifications_use_case import ListUnreadNotificationsUseCase
from app.application.use_cases.mark_notification_read_use_case import MarkNotificationReadUseCase
from app.application.use_cases.mark_all_notifications_read_use_case import MarkAllNotificationsReadUseCase
from app.application.use_cases.notify_user_use_case import NotifyUserUseCase

from app.interfaces.http.utils.errors import unauthorized, api_error

notification_bp = Blueprint("notifications", __name__)


def _get_user():
    user = getattr(g, "current_user", None)
    if not user:
        return None, unauthorized()
    return user, None


@notification_bp.route("/notifications", methods=["GET"])
def list_notifications():
    user, error = _get_user()
    if error:
        return error

    with SqlAlchemyUnitOfWork() as uow:
        use_case = ListUnreadNotificationsUseCase(uow)
        result = use_case.execute(user_id=user.id)

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


@notification_bp.route("/notifications/<notification_id>/read", methods=["POST"])
def mark_read(notification_id: str):
    user, error = _get_user()
    if error:
        return error

    try:
        notification_uuid = UUID(notification_id)
    except ValueError:
        return api_error("invalid_id", "Invalid notification id", status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            use_case = MarkNotificationReadUseCase(uow)
            use_case.execute(notification_uuid)

        return jsonify({"ok": True}), 200
    except Exception as e:
        return api_error("mark_failed", str(e))


@notification_bp.route("/notifications/read-all", methods=["POST"])
def mark_all_read():
    user, error = _get_user()
    if error:
        return error

    try:
        with SqlAlchemyUnitOfWork() as uow:
            use_case = MarkAllNotificationsReadUseCase(uow)
            use_case.execute(user_id=user.id)

        return jsonify({"ok": True}), 200
    except Exception as e:
        return api_error("mark_all_failed", str(e))


@notification_bp.route("/notifications/test", methods=["POST"])
def test_notification():
    user, error = _get_user()
    if error:
        return error

    try:
        with SqlAlchemyUnitOfWork() as uow:
            use_case = NotifyUserUseCase(uow)
            use_case.execute(
                user_id=user.id,
                title="Teste tempo real",
                message="Notificação disparada via endpoint",
                type="success",
            )

        return jsonify({"ok": True}), 200
    except Exception as e:
        return api_error("notify_failed", str(e))