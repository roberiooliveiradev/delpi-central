# app/interfaces/http/portal_tour_controller.py

import logging
from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.application.use_cases.admin.list_portal_tour_explorers_use_case import (
    ListPortalTourExplorersUseCase,
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


def _progress_payload(result) -> dict:
    return {
        "tourVersion": result.tour_version,
        "status": result.status,
        "completedQuestIds": list(result.completed_quest_ids),
        "startedAt": _iso(result.started_at),
        "lastActivityAt": _iso(result.last_activity_at),
        "completedAt": _iso(result.completed_at),
    }


@portal_tour_bp.route("/me/portal-tour", methods=["GET"])
@require_auth()
def get_my_portal_tour_progress():
    user = g.current_user

    with SqlAlchemyUnitOfWork() as uow:
        result = GetPortalTourProgressUseCase(uow).execute(str(user.id))

    return jsonify(_progress_payload(result)), 200


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
                    "startedAt": _iso(item.started_at),
                    "lastActivityAt": _iso(item.last_activity_at),
                    "completedAt": _iso(item.completed_at),
                }
                for item in result.items
            ],
        }
    ), 200
