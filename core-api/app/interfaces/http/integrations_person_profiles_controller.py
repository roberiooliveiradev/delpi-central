"""Person profiles S2S — leitura por user_id para plugins (commercial, etc.)."""

from __future__ import annotations

import logging
from uuid import UUID

from flask import Blueprint, jsonify, request, send_file

from app.application.use_cases.manage_person_profile_use_case import (
    ManagePersonProfileUseCase,
)
from app.extensions.integration_rate_limit import integration_rate_limit
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.service_token import require_service_token
from app.interfaces.http.utils.errors import api_error

logger = logging.getLogger(__name__)

integrations_person_profiles_bp = Blueprint(
    "integrations_person_profiles",
    __name__,
    url_prefix="/integrations/person-profiles",
)

_LOOKUP_MAX_IDS = 50


def _manage(uow) -> ManagePersonProfileUseCase:
    return ManagePersonProfileUseCase(repository=uow.person_profiles)


def _parse_user_id(raw: str) -> UUID:
    return UUID(str(raw).strip())


def _with_s2s_photo_url(payload: dict) -> dict:
    """Reescreve photo_url para o path S2S (não /me)."""
    data = dict(payload)
    user_id = str(data.get("user_id") or "").strip()
    if data.get("has_photo") and user_id:
        data["photo_url"] = f"/integrations/person-profiles/{user_id}/photo"
    else:
        data["photo_url"] = None
    return data


@integrations_person_profiles_bp.route("/<user_id>", methods=["GET"])
@require_service_token()
@integration_rate_limit()
def get_integration_person_profile(user_id: str):
    try:
        uid = _parse_user_id(user_id)
    except ValueError:
        return api_error("validation_error", "user_id inválido.", status=400)
    try:
        with SqlAlchemyUnitOfWork() as uow:
            data = _with_s2s_photo_url(_manage(uow).get_profile(user_id=uid))
        return jsonify(data), 200
    except Exception:
        logger.exception("get_integration_person_profile_failed")
        return api_error(
            "person_profile_failed",
            "Erro ao carregar perfil.",
            status=500,
        )


@integrations_person_profiles_bp.route("/<user_id>/photo", methods=["GET"])
@require_service_token()
@integration_rate_limit()
def get_integration_person_profile_photo(user_id: str):
    try:
        uid = _parse_user_id(user_id)
    except ValueError:
        return api_error("validation_error", "user_id inválido.", status=400)
    try:
        with SqlAlchemyUnitOfWork() as uow:
            photo = _manage(uow).get_photo_file(user_id=uid)
        return send_file(
            photo.path,
            mimetype=photo.content_type,
            download_name=photo.file_name,
            as_attachment=False,
        )
    except LookupError as exc:
        return api_error("not_found", str(exc), status=404)
    except Exception:
        logger.exception("get_integration_person_profile_photo_failed")
        return api_error(
            "person_profile_photo_failed",
            "Erro ao carregar foto.",
            status=500,
        )


@integrations_person_profiles_bp.route("/lookup", methods=["POST"])
@require_service_token()
@integration_rate_limit()
def lookup_integration_person_profiles():
    body = request.get_json(silent=True) or {}
    raw_ids = body.get("ids") if isinstance(body, dict) else None
    if not isinstance(raw_ids, list):
        return api_error("validation_error", "ids must be an array", status=400)
    if len(raw_ids) > _LOOKUP_MAX_IDS:
        return api_error(
            "validation_error",
            f"ids must contain at most {_LOOKUP_MAX_IDS} items",
            status=400,
        )

    items: list[dict] = []
    try:
        with SqlAlchemyUnitOfWork() as uow:
            uc = _manage(uow)
            for raw in raw_ids:
                try:
                    uid = _parse_user_id(str(raw))
                except ValueError:
                    continue
                items.append(_with_s2s_photo_url(uc.get_profile(user_id=uid)))
        return jsonify({"items": items}), 200
    except Exception:
        logger.exception("lookup_integration_person_profiles_failed")
        return api_error(
            "person_profile_lookup_failed",
            "Erro ao buscar perfis.",
            status=500,
        )
