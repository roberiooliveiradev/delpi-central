"""Diretório de usuários para integrações S2S (api-pac, api-delpi)."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.application.use_cases.search_directory_users_use_case import (
    SearchDirectoryUsersUseCase,
)
from app.extensions.integration_rate_limit import integration_rate_limit
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.service_token import require_service_token
from app.interfaces.http.utils.errors import api_error

logger = logging.getLogger(__name__)

integrations_directory_bp = Blueprint(
    "integrations_directory",
    __name__,
    url_prefix="/integrations/directory",
)

_PAC_QUALITY_APP_ID = "quality-action-plans"


@integrations_directory_bp.route("/users", methods=["GET"])
@require_service_token()
@integration_rate_limit()
def search_integration_directory_users():
    query = request.args.get("q") or request.args.get("query")
    limit = request.args.get("limit", 10)
    app_id = (request.args.get("app") or _PAC_QUALITY_APP_ID).strip() or _PAC_QUALITY_APP_ID
    permission_code = (request.args.get("permission") or "").strip() or None
    browse_raw = (request.args.get("browse") or "").strip().lower()
    browse = browse_raw in {"1", "true", "yes"}

    try:
        with SqlAlchemyUnitOfWork() as uow:
            results = SearchDirectoryUsersUseCase(uow).execute(
                query=query,
                limit=int(limit),
                app_id=app_id,
                permission_code=permission_code,
                browse=browse,
            )
    except ValueError:
        return api_error("validation_error", "limit must be a number", status=400)
    except Exception:
        logger.exception("search_integration_directory_users_failed")
        return api_error(
            "search_integration_directory_users_failed",
            "Erro ao buscar usuários.",
            status=500,
        )

    return jsonify({"items": results}), 200
