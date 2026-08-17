"""Diretório de usuários para integrações S2S (api-pac, api-delpi)."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from app.application.use_cases.lookup_directory_users_use_case import (
    LookupDirectoryUsersUseCase,
)
from app.application.use_cases.list_directory_users_by_app_use_case import (
    ListDirectoryUsersByAppUseCase,
)
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
_LOOKUP_MAX_IDS = 50


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
                mask_email=False,
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


@integrations_directory_bp.route("/users/by-app", methods=["GET"])
@require_service_token()
@integration_rate_limit()
def list_integration_directory_users_by_app():
    """Lista paginada completa de usuários com acesso ao app (S2S roster — não typeahead)."""
    app_id = (request.args.get("app") or "").strip()
    if not app_id:
        return api_error("validation_error", "app is required", status=400)

    page = request.args.get("page", 1)
    page_size = request.args.get("pageSize", request.args.get("page_size", 100))

    try:
        with SqlAlchemyUnitOfWork() as uow:
            payload = ListDirectoryUsersByAppUseCase(uow).execute(
                app_id=app_id,
                page=int(page),
                page_size=int(page_size),
                mask_email=False,
            )
    except ValueError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception:
        logger.exception("list_integration_directory_users_by_app_failed")
        return api_error(
            "list_integration_directory_users_by_app_failed",
            "Erro ao listar usuários do app.",
            status=500,
        )

    return jsonify(payload), 200


@integrations_directory_bp.route("/users/lookup", methods=["POST"])
@require_service_token()
@integration_rate_limit()
def lookup_integration_directory_users():
    """Resolve e-mails SMTP reais por user ids (S2S — envio Graph/Outlook)."""
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

    app_id = (body.get("app") if isinstance(body, dict) else None) or request.args.get(
        "app"
    )
    app_id = (str(app_id).strip() if app_id else "") or None

    try:
        with SqlAlchemyUnitOfWork() as uow:
            results = LookupDirectoryUsersUseCase(uow).execute(
                user_ids=[str(item) for item in raw_ids if item],
                mask_email=False,
                app_id=app_id,
            )
    except Exception:
        logger.exception("lookup_integration_directory_users_failed")
        return api_error(
            "lookup_integration_directory_users_failed",
            "Erro ao buscar usuários.",
            status=500,
        )

    return jsonify({"items": results}), 200
