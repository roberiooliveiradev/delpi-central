# app/interfaces/http/notification_controller.py

from flask import Blueprint, jsonify, g
from sqlalchemy import desc
from datetime import datetime
from app.infrastructure.db.models.notification import Notification
from app.extensions.db import db

# ✅ sem url_prefix aqui
notification_bp = Blueprint("notifications", __name__)

@notification_bp.route("/notifications", methods=["GET"])
def list_notifications():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    rows = (
        Notification.query
        .filter(
            Notification.user_id == str(g.current_sub),
            Notification.read_at.is_(None)
        )
        .order_by(desc(Notification.created_at))
        .limit(50)
        .all()
    )

    return jsonify([{
        "id": str(n.id),
        "title": n.title,
        "message": n.message,
        "type": n.type,
        "read": False,
        "createdAt": n.created_at.isoformat() + "Z",
    } for n in rows])


@notification_bp.route("/notifications/<notification_id>/read", methods=["POST"])
def mark_read(notification_id: str):
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    n = Notification.query.filter_by(
        id=notification_id,
        user_id=str(g.current_sub)
    ).first()

    if not n:
        return jsonify({"error": "Not found"}), 404

    if n.read_at is None:
        n.read_at = datetime.utcnow()
        db.session.commit()

    return jsonify({"ok": True})


@notification_bp.route("/notifications/read-all", methods=["POST"])
def mark_all_read():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    Notification.query.filter_by(
        user_id=str(g.current_sub),
        read_at=None
    ).update(
        {"read_at": datetime.utcnow()},
        synchronize_session=False
    )
    db.session.commit()

    return jsonify({"ok": True})


@notification_bp.route("/notifications/test", methods=["POST"])
def test_notification():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    from app.domain.services.notification_service import notify_user

    notify_user(
        sub=str(user.id),
        title="Teste tempo real",
        message="Notificação disparada via endpoint",
        type="success"
    )

    return jsonify({"ok": True})
