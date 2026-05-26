# app/interfaces/http/me_controller.py

import logging
import os
from uuid import UUID

from flask import Blueprint, jsonify, g, request

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
from app.application.use_cases.list_notifications_use_case import (
    ListNotificationsUseCase,
)
from app.interfaces.http.serializers.notification_serializer import serialize_notification

from app.application.use_cases.mark_notification_read_use_case import (
    MarkNotificationReadUseCase,
    NotificationAccessDeniedError,
    NotificationNotFoundError,
)

from app.application.use_cases.mark_all_notifications_read_use_case import (
    MarkAllNotificationsReadUseCase,
)
from app.application.use_cases.delete_notification_use_case import (
    DeleteNotificationUseCase,
)
from app.application.use_cases.set_notification_important_use_case import (
    SetNotificationImportantUseCase,
)
from app.application.use_cases.get_notification_preferences_use_case import (
    GetNotificationPreferencesUseCase,
)
from app.application.use_cases.update_notification_preferences_use_case import (
    UpdateNotificationPreferencesUseCase,
)
from app.domain.notifications.notification_constants import ALLOWED_NOTIFICATION_CATEGORIES

from app.application.use_cases.notify_user_use_case import (
    NotifyUserUseCase,
)

from app.application.use_cases.lookup_directory_users_use_case import (
    LookupDirectoryUsersUseCase,
)
from app.application.use_cases.search_directory_users_use_case import (
    SearchDirectoryUsersUseCase,
)

logger = logging.getLogger(__name__)

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

    return jsonify([serialize_notification(n) for n in result]), 200


@me_bp.route("/me/notifications/history", methods=["GET"])
@require_auth()
def list_notifications_history():
    user = g.current_user

    status = request.args.get("status", "all")
    if status not in ("all", "unread", "read"):
        return api_error("invalid_status", "status must be all, unread or read", status=400)

    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return api_error("invalid_pagination", "limit and offset must be integers", status=400)

    category = request.args.get("category")
    if category:
        category = category.strip().lower()
        if category not in ALLOWED_NOTIFICATION_CATEGORIES:
            return api_error("invalid_category", "invalid notification category", status=400)

    important_param = request.args.get("important", "").strip().lower()
    important_only = important_param in ("1", "true", "yes")

    with SqlAlchemyUnitOfWork() as uow:
        result = ListNotificationsUseCase(uow).execute(
            user_id=user.id,
            status=status,
            category=category or None,
            important_only=important_only,
            limit=limit,
            offset=offset,
        )

    return (
        jsonify(
            {
                "items": [serialize_notification(n) for n in result.items],
                "total": result.total,
                "limit": result.limit,
                "offset": result.offset,
            }
        ),
        200,
    )


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
        logger.exception("mark_failed")
        return api_error("mark_failed", "Erro ao processar notificação.", status=500)


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
        logger.exception("mark_all_failed")
        return api_error("mark_all_failed", "Erro ao processar notificações.", status=500)


@me_bp.route("/me/notifications/<notification_id>", methods=["DELETE"])
@require_auth()
def delete_notification(notification_id: str):
    user = g.current_user

    try:
        notification_uuid = UUID(notification_id)
    except ValueError:
        return api_error("invalid_id", "Invalid notification id", status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            DeleteNotificationUseCase(uow).execute(notification_uuid, actor_user_id=str(user.id))
        return jsonify({"ok": True}), 200
    except NotificationNotFoundError:
        return api_error("not_found", "Notification not found", status=404)
    except NotificationAccessDeniedError:
        return api_error("forbidden", "Notification does not belong to current user", status=403)
    except Exception as e:
        logger.exception("delete_failed")
        return api_error("delete_failed", "Erro ao excluir notificação.", status=500)


@me_bp.route("/me/notifications/<notification_id>/important", methods=["PATCH"])
@require_auth()
def set_notification_important(notification_id: str):
    user = g.current_user

    try:
        notification_uuid = UUID(notification_id)
    except ValueError:
        return api_error("invalid_id", "Invalid notification id", status=400)

    body = request.get_json(silent=True) or {}
    if "isImportant" not in body and "is_important" not in body:
        return api_error("validation_error", "isImportant is required", status=400)

    is_important = body.get("isImportant", body.get("is_important"))
    if not isinstance(is_important, bool):
        return api_error("validation_error", "isImportant must be a boolean", status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = SetNotificationImportantUseCase(uow).execute(
                notification_uuid,
                actor_user_id=str(user.id),
                is_important=is_important,
            )
        return jsonify(result), 200
    except NotificationNotFoundError:
        return api_error("not_found", "Notification not found", status=404)
    except NotificationAccessDeniedError:
        return api_error("forbidden", "Notification does not belong to current user", status=403)
    except Exception as e:
        logger.exception("important_failed")
        return api_error("important_failed", "Erro ao atualizar notificação.", status=500)


# ==========================================================
# NOTIFICATION PREFERENCES
# ==========================================================

@me_bp.route("/me/notifications/preferences", methods=["GET"])
@require_auth()
def get_notification_preferences():
    user = g.current_user

    with SqlAlchemyUnitOfWork() as uow:
        result = GetNotificationPreferencesUseCase(uow).execute(str(user.id))

    return jsonify(
        {
            "mutedCategories": result.muted_categories,
            "mutableCategories": result.mutable_categories,
        }
    ), 200


@me_bp.route("/me/notifications/preferences", methods=["PATCH"])
@require_auth()
def update_notification_preferences():
    user = g.current_user
    body = request.get_json(silent=True) or {}

    muted = body.get("mutedCategories", body.get("muted_categories"))
    if muted is None:
        return api_error("validation_error", "mutedCategories is required", status=400)
    if not isinstance(muted, list) or not all(isinstance(item, str) for item in muted):
        return api_error("validation_error", "mutedCategories must be an array of strings", status=400)

    with SqlAlchemyUnitOfWork() as uow:
        result = UpdateNotificationPreferencesUseCase(uow).execute(
            str(user.id),
            muted_categories=muted,
        )

    return jsonify(
        {
            "mutedCategories": result.muted_categories,
            "mutableCategories": result.mutable_categories,
        }
    ), 200


# ==========================================================
# GET /me/directory/users
# ==========================================================


@me_bp.route("/me/directory/users", methods=["GET"])
@require_auth()
def search_directory_users():
    user = g.current_user
    query = request.args.get("q") or request.args.get("query")
    limit = request.args.get("limit", 10)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            results = SearchDirectoryUsersUseCase(uow).execute(
                current_user_id=str(user.id),
                query=query,
                limit=int(limit),
            )
    except ValueError:
        return api_error("validation_error", "limit must be a number", status=400)
    except Exception as exc:
        logger.exception("search_directory_users_failed")
        return api_error("search_directory_users_failed", "Erro ao buscar usuários.", status=500)

    return jsonify({"items": results}), 200


@me_bp.route("/me/directory/users/lookup", methods=["POST"])
@require_auth()
def lookup_directory_users():
    body = request.get_json(silent=True) or {}
    raw_ids = body.get("ids") if isinstance(body, dict) else None

    if not isinstance(raw_ids, list):
        return api_error("validation_error", "ids must be an array", status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            results = LookupDirectoryUsersUseCase(uow).execute(
                user_ids=[str(item) for item in raw_ids if item],
            )
    except Exception as exc:
        logger.exception("lookup_directory_users_failed")
        return api_error("lookup_directory_users_failed", "Erro ao buscar usuários.", status=500)

    return jsonify({"items": results}), 200


# ==========================================================
# TEST NOTIFICATION (DEV)
# ==========================================================

@me_bp.route("/me/notifications/test", methods=["POST"])
@require_auth()
def test_notification():
    if os.getenv("FLASK_ENV", "").lower() == "production":
        return api_error(
            "forbidden",
            "Test notifications are disabled in production",
            status=403,
        )

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
        logger.exception("notify_failed")
        return api_error("notify_failed", "Erro ao enviar notificação.", status=500)


# ==========================================================
# LGPD — PRIVACY INFO
# ==========================================================

@me_bp.route("/me/privacy", methods=["GET"])
@require_auth()
def get_privacy_info():
    from app.domain.lgpd.privacy_constants import (
        DPO_EMAIL,
        DPO_NAME,
        PRIVACY_POLICY_URL,
        CONSENT_PURPOSES,
        DATA_RETENTION_DAYS,
    )
    return jsonify({
        "dpo": {"name": DPO_NAME, "email": DPO_EMAIL},
        "privacyPolicyUrl": PRIVACY_POLICY_URL,
        "consentPurposes": CONSENT_PURPOSES,
        "dataRetentionDays": DATA_RETENTION_DAYS,
        "rights": [
            "Confirmação de tratamento (Art. 18, I)",
            "Acesso aos dados (Art. 18, II)",
            "Correção de dados (Art. 18, III)",
            "Anonimização/bloqueio (Art. 18, IV)",
            "Portabilidade (Art. 18, V) — GET /me/data-export",
            "Eliminação (Art. 18, VI) — Solicitar ao DPO",
            "Revogação de consentimento (Art. 18, IX) — DELETE /me/consents/<purpose>",
        ],
    }), 200


# ==========================================================
# LGPD — CONSENTS
# ==========================================================

VALID_CONSENT_PURPOSES = {"data_processing", "analytics", "ai_context", "birthday_notifications", "usage_tracking"}


@me_bp.route("/me/consents", methods=["GET"])
@require_auth()
def list_consents():
    user = g.current_user
    with SqlAlchemyUnitOfWork() as uow:
        from app.application.use_cases.list_consents_use_case import ListConsentsUseCase
        items = ListConsentsUseCase(uow).execute(user_id=str(user.id))
    return jsonify({
        "items": [
            {
                "id": str(c.id),
                "purpose": c.purpose,
                "granted": c.granted,
                "grantedAt": c.granted_at.isoformat() if c.granted_at else None,
                "revokedAt": c.revoked_at.isoformat() if c.revoked_at else None,
            }
            for c in items
        ],
        "availablePurposes": sorted(VALID_CONSENT_PURPOSES),
    }), 200


@me_bp.route("/me/consents", methods=["POST"])
@require_auth()
def grant_consent():
    user = g.current_user
    body = request.get_json(silent=True) or {}
    purpose = (body.get("purpose") or "").strip().lower()

    if purpose not in VALID_CONSENT_PURPOSES:
        return api_error("invalid_purpose", f"Purpose must be one of: {', '.join(sorted(VALID_CONSENT_PURPOSES))}", status=400)

    with SqlAlchemyUnitOfWork() as uow:
        from app.application.use_cases.manage_consent_use_case import GrantConsentUseCase
        result = GrantConsentUseCase(uow).execute(
            user_id=str(user.id),
            purpose=purpose,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent", "")[:500],
        )

    return jsonify({
        "id": str(result.id),
        "purpose": result.purpose,
        "granted": result.granted,
        "grantedAt": result.granted_at.isoformat() if result.granted_at else None,
    }), 200


@me_bp.route("/me/consents/<purpose>", methods=["DELETE"])
@require_auth()
def revoke_consent(purpose: str):
    user = g.current_user
    purpose = purpose.strip().lower()

    if purpose not in VALID_CONSENT_PURPOSES:
        return api_error("invalid_purpose", "Invalid consent purpose", status=400)

    with SqlAlchemyUnitOfWork() as uow:
        from app.application.use_cases.manage_consent_use_case import RevokeConsentUseCase
        result = RevokeConsentUseCase(uow).execute(user_id=str(user.id), purpose=purpose)

    if not result:
        return api_error("not_found", "Consent not found", status=404)

    return jsonify({"ok": True, "purpose": result.purpose, "granted": result.granted}), 200


# ==========================================================
# LGPD — DATA EXPORT (PORTABILITY)
# ==========================================================

@me_bp.route("/me/data-export", methods=["GET"])
@require_auth()
def export_my_data():
    user = g.current_user
    try:
        with SqlAlchemyUnitOfWork() as uow:
            from app.application.use_cases.export_user_data_use_case import ExportUserDataUseCase
            data = ExportUserDataUseCase(uow).execute(user_id=str(user.id))
        return jsonify(data), 200
    except Exception:
        logger.exception("data_export_failed")
        return api_error("export_failed", "Erro ao exportar dados.", status=500)


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