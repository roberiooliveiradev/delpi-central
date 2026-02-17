# app/domain/services/notification_service.py

from app.infrastructure.db.models.notification import Notification
from app.extensions.db import db
from app.extensions.socket import socketio

def notify_user(sub: str, title: str, message: str, type: str = "info"):
    notification = Notification(
        user_id=sub,
        title=title,
        message=message,
        type=type,
    )

    db.session.add(notification)
    db.session.commit()

    payload = {
        "id": str(notification.id),
        "title": notification.title,
        "message": notification.message,
        "type": notification.type,
        "createdAt": notification.created_at.isoformat() + "Z",
        "read": False,
    }

    # ✅ namespace explícito e room do usuário
    socketio.emit(
        "notification",
        payload,
        room=sub,
        namespace="/",
    )

    print(f"✅ emitting event 'notification' to room={sub}")

    return notification
