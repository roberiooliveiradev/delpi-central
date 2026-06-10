# app/interfaces/http/portal_tour_controller.py

import logging
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.application.use_cases.admin.list_portal_tour_explorers_use_case import (
    ListPortalTourExplorersUseCase,
)
from app.application.use_cases.admin.list_portal_tour_top_explorers_use_case import (
    ListPortalTourTopExplorersUseCase,
)
from app.application.use_cases.get_portal_tour_catalog_use_case import (
    GetPortalTourCatalogUseCase,
)
from app.application.use_cases.get_portal_tour_achievements_use_case import (
    GetPortalTourAchievementsUseCase,
)
from app.application.use_cases.get_portal_tour_insights_use_case import (
    GetPortalTourInsightsUseCase,
)
from app.application.use_cases.get_portal_tour_progress_use_case import (
    GetPortalTourProgressUseCase,
)
from app.application.use_cases.reset_portal_tour_progress_use_case import (
    ResetPortalTourProgressUseCase,
)
from app.application.use_cases.sync_portal_tour_progress_use_case import (
    SyncPortalTourProgressUseCase,
)
from app.domain.portal_tour.portal_tour_availability_service import PortalTourUserContext
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.authorization import require_auth, require_permission
from app.interfaces.http.utils.errors import api_error

logger = logging.getLogger(__name__)

portal_tour_bp = Blueprint("portal_tour", __name__)
admin_portal_tour_bp = Blueprint("admin_portal_tour", __name__)


def _iso(value: datetime | None) -> str | None:
    if not value:
        return None
    return value.isoformat() + "Z"


def _portal_tour_user_context(user) -> PortalTourUserContext:
    return PortalTourUserContext(
        permissions=frozenset(getattr(user, "permissions", []) or []),
        is_superadmin=bool(getattr(user, "is_superadmin", False)),
    )


def _insights_payload(result) -> dict:
    return {
        "explorationDurationSeconds": result.exploration_duration_seconds,
        "questsCompletedAfterReturn": result.quests_completed_after_return,
        "returnStreakMessage": result.return_streak_message,
    }


def _progress_payload(result, insights=None) -> dict:
    payload = {
        "tourVersion": result.tour_version,
        "status": result.status,
        "completedQuestIds": list(result.completed_quest_ids),
        "startedAt": _iso(result.started_at),
        "lastActivityAt": _iso(result.last_activity_at),
        "completedAt": _iso(result.completed_at),
    }
    if insights is not None:
        payload["insights"] = _insights_payload(insights)
    return payload


def _catalog_payload(result) -> dict:
    return {
        "tourVersion": result.tour_version,
        "requiredQuestIds": list(result.required_quest_ids),
        "optionalQuestIds": list(result.optional_quest_ids),
        "newQuestIds": list(result.new_quest_ids),
        "progressPercent": result.progress_percent,
        "explorerLevel": result.explorer_level,
        "earnedXp": result.earned_xp,
        "categoryLabels": result.category_labels,
        "categoryOrder": list(result.category_order),
        "quests": [
            {
                "id": item.id,
                "title": item.title,
                "hint": item.hint,
                "category": item.category,
                "categoryLabel": item.category_label,
                "scope": item.scope,
                "optional": item.optional,
                "introducedInVersion": item.introduced_in_version,
                "isNew": item.is_new,
            }
            for item in result.quests
        ],
    }


@portal_tour_bp.route("/me/portal-tour/catalog", methods=["GET"])
@require_auth()
def get_my_portal_tour_catalog():
    user = g.current_user
    tour_version = request.args.get("tourVersion", request.args.get("tour_version"))
    context = _portal_tour_user_context(user)

    with SqlAlchemyUnitOfWork() as uow:
        result = GetPortalTourCatalogUseCase(uow).execute(
            str(user.id),
            context,
            tour_version=(tour_version or "").strip() or None,
        )

    return jsonify(_catalog_payload(result)), 200


@portal_tour_bp.route("/me/portal-tour", methods=["GET"])
@require_auth()
def get_my_portal_tour_progress():
    user = g.current_user

    with SqlAlchemyUnitOfWork() as uow:
        result = GetPortalTourProgressUseCase(uow).execute(str(user.id))
        insights = GetPortalTourInsightsUseCase(uow).execute(
            str(user.id),
            tour_version=result.tour_version,
        )

    return jsonify(_progress_payload(result, insights)), 200


@portal_tour_bp.route("/me/portal-tour", methods=["PATCH"])
@require_auth()
def sync_my_portal_tour_progress():
    user = g.current_user
    body = request.get_json(silent=True) or {}

    tour_version = body.get("tourVersion", body.get("tour_version"))
    status = body.get("status")
    completed_quest_ids = body.get("completedQuestIds", body.get("completed_quest_ids"))
    completed_quest_id = body.get("completedQuestId", body.get("completed_quest_id"))

    if not tour_version:
        return api_error("validation_error", "tourVersion is required", status=400)
    if not status:
        return api_error("validation_error", "status is required", status=400)

    if completed_quest_ids is not None and (
        not isinstance(completed_quest_ids, list)
        or not all(isinstance(item, str) for item in completed_quest_ids)
    ):
        return api_error(
            "validation_error",
            "completedQuestIds must be an array of strings",
            status=400,
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = SyncPortalTourProgressUseCase(uow).execute(
                str(user.id),
                tour_version=str(tour_version),
                status=str(status),
                completed_quest_ids=completed_quest_ids,
                completed_quest_id=str(completed_quest_id) if completed_quest_id else None,
                user_context=_portal_tour_user_context(user),
            )
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception:
        logger.exception("sync_portal_tour_progress_failed user_id=%s", user.id)
        return api_error("portal_tour_sync_failed", "Falha ao sincronizar tour", status=500)

    return jsonify(_progress_payload(result)), 200


@portal_tour_bp.route("/me/portal-tour", methods=["DELETE"])
@require_auth()
def reset_my_portal_tour_progress():
    user = g.current_user

    with SqlAlchemyUnitOfWork() as uow:
        ResetPortalTourProgressUseCase(uow).execute(str(user.id))

    return jsonify({"ok": True}), 200


@portal_tour_bp.route("/me/portal-tour/achievements", methods=["GET"])
@require_auth()
def get_my_portal_tour_achievements():
    user = g.current_user
    tour_version = request.args.get("tourVersion", request.args.get("tour_version"))
    context = _portal_tour_user_context(user)

    with SqlAlchemyUnitOfWork() as uow:
        result = GetPortalTourAchievementsUseCase(uow).execute(
            str(user.id),
            context,
            tour_version=(tour_version or "").strip() or None,
        )

    return jsonify(
        {
            "tourVersion": result.tour_version,
            "unlockedCount": result.unlocked_count,
            "totalCount": result.total_count,
            "progressPercent": result.progress_percent,
            "explorerLevel": result.explorer_level,
            "items": [
                {
                    "id": item.id,
                    "title": item.title,
                    "description": item.description,
                    "kind": item.kind,
                    "unlocked": item.unlocked,
                    "unlockedAt": _iso(item.unlocked_at),
                }
                for item in result.items
            ],
        }
    ), 200


@admin_portal_tour_bp.route("/admin/portal-tour/explorers", methods=["GET"])
@require_permission("rbac.manage")
def list_portal_tour_explorers():
    tour_version = request.args.get("tourVersion", request.args.get("tour_version"))
    status = request.args.get("status")
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return api_error("validation_error", "limit and offset must be integers", status=400)

    with SqlAlchemyUnitOfWork() as uow:
        result = ListPortalTourExplorersUseCase(uow).execute(
            tour_version=tour_version,
            status=status,
            limit=limit,
            offset=offset,
        )

    return jsonify(
        {
            "tourVersion": result.tour_version,
            "status": result.status,
            "total": result.total,
            "items": [
                {
                    "userId": item.user_id,
                    "name": item.name,
                    "email": item.email,
                    "tourVersion": item.tour_version,
                    "status": item.status,
                    "completedQuestIds": list(item.completed_quest_ids),
                    "completedQuestCount": item.completed_quest_count,
                    "progressPercent": item.progress_percent,
                    "explorerLevel": item.explorer_level,
                    "requiredQuestDone": item.required_quest_done,
                    "requiredQuestTotal": item.required_quest_total,
                    "startedAt": _iso(item.started_at),
                    "lastActivityAt": _iso(item.last_activity_at),
                    "completedAt": _iso(item.completed_at),
                }
                for item in result.items
            ],
        }
    ), 200


@admin_portal_tour_bp.route("/admin/portal-tour/top-explorers", methods=["GET"])
@require_permission("rbac.manage")
def list_portal_tour_top_explorers():
    tour_version = request.args.get("tourVersion", request.args.get("tour_version"))
    try:
        period_days = int(request.args.get("periodDays", request.args.get("days", 7)))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return api_error(
            "validation_error",
            "periodDays and limit must be integers",
            status=400,
        )

    with SqlAlchemyUnitOfWork() as uow:
        result = ListPortalTourTopExplorersUseCase(uow).execute(
            tour_version=tour_version,
            period_days=period_days,
            limit=limit,
        )

    return jsonify(
        {
            "periodDays": result.period_days,
            "tourVersion": result.tour_version,
            "items": [
                {
                    "userId": item.user_id,
                    "name": item.name,
                    "email": item.email,
                    "tourVersion": item.tour_version,
                    "questsInPeriod": item.quests_in_period,
                    "lastActivityAt": _iso(item.last_activity_at),
                }
                for item in result.items
            ],
        }
    ), 200
