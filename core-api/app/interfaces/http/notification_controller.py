# app/interfaces/http/notification_controller.py


from flask import Blueprint, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.socket.socket_event_dispatcher import SocketIOEventDispatcher

from app.application.use_cases.list_unread_notifications_use_case import (
    ListUnreadNotificationsUseCase,
)
from app.application.use_cases.mark_notification_read_use_case import (
    MarkNotificationReadUseCase,
)
from app.application.use_cases.mark_all_notifications_read_use_case import (
    MarkAllNotificationsReadUseCase,
)
from app.application.use_cases.notify_user_use_case import (
    NotifyUserUseCase,
)


notification_bp = Blueprint("notifications", __name__)


# ---------------------------------------------------------
# List unread
# ---------------------------------------------------------

@notification_bp.route("/notifications", methods=["GET"])
def list_notifications():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    uow = SqlAlchemyUnitOfWork()
    use_case = ListUnreadNotificationsUseCase(uow)

    result = use_case.execute(user_id=g.current_sub)

    return jsonify(result), 200


# ---------------------------------------------------------
# Mark single as read
# ---------------------------------------------------------

@notification_bp.route("/notifications/<notification_id>/read", methods=["POST"])
def mark_read(notification_id: str):
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    uow = SqlAlchemyUnitOfWork()
    use_case = MarkNotificationReadUseCase(uow)

    use_case.execute(notification_id)

    return jsonify({"ok": True}), 200


# ---------------------------------------------------------
# Mark all as read
# ---------------------------------------------------------

@notification_bp.route("/notifications/read-all", methods=["POST"])
def mark_all_read():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    uow = SqlAlchemyUnitOfWork()
    use_case = MarkAllNotificationsReadUseCase(uow)

    use_case.execute(user_id=g.current_sub)

    return jsonify({"ok": True}), 200


# ---------------------------------------------------------
# Test notification
# ---------------------------------------------------------

@notification_bp.route("/notifications/test", methods=["POST"])
def test_notification():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    uow = SqlAlchemyUnitOfWork()
    dispatcher = SocketIOEventDispatcher()

    use_case = NotifyUserUseCase(
        uow=uow,
        notification_repo=uow.notifications,
        event_dispatcher=dispatcher,
    )

    use_case.execute(
        user_id=g.current_sub,
        title="Teste tempo real",
        message="Notificação disparada via endpoint",
        type="success",
    )

    return jsonify({"ok": True}), 200