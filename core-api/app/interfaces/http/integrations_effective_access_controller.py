"""S2S: resolve Core-authoritative effective access for a Keycloak subject.

Contract (frozen for TV-GPI-004B4):
  GET /integrations/effective-access/subjects/<keycloak_sub>
  operationId: get_effective_access_by_subject
  Auth: CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN
        (Authorization: Bearer … or X-Delpi-Service-Token)
  Subject: Keycloak sub (UUID) — Core user id; no email fallback
  Permission authority: PermissionResolver only
"""

from __future__ import annotations

import logging
import time
from uuid import UUID

from flask import Blueprint, jsonify, request

from app.application.use_cases.get_effective_access_by_subject_use_case import (
    EffectiveAccessIdentityNotFoundError,
    EffectiveAccessUnavailableError,
    GetEffectiveAccessBySubjectUseCase,
)
from app.extensions.integration_rate_limit import integration_rate_limit
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.service_token import (
    require_effective_access_service_token,
)
from app.interfaces.http.utils.errors import api_error

logger = logging.getLogger(__name__)

integrations_effective_access_bp = Blueprint(
    "integrations_effective_access",
    __name__,
    url_prefix="/integrations/effective-access",
)


@integrations_effective_access_bp.route(
    "/subjects/<keycloak_sub>",
    methods=["GET"],
    endpoint="get_effective_access_by_subject",
)
@require_effective_access_service_token()
@integration_rate_limit()
def get_effective_access_by_subject(keycloak_sub: str):
    """operationId: get_effective_access_by_subject"""
    started = time.monotonic()
    correlation_id = (
        request.headers.get("X-Correlation-Id")
        or request.headers.get("X-Request-Id")
        or ""
    ).strip() or None

    try:
        subject = UUID(str(keycloak_sub).strip())
    except Exception:
        return api_error(
            "validation_error",
            "keycloak_sub must be a UUID",
            status=400,
            path="keycloak_sub",
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = GetEffectiveAccessBySubjectUseCase(uow).execute(
                keycloak_subject=subject
            )
    except EffectiveAccessIdentityNotFoundError:
        logger.info(
            "effective_access_identity_not_found correlation_id=%s subject=%s latency_ms=%.1f",
            correlation_id,
            subject,
            (time.monotonic() - started) * 1000,
        )
        return api_error(
            "identity_not_found",
            "Keycloak subject is not linked to a Core user",
            status=404,
            path="keycloak_sub",
        )
    except EffectiveAccessUnavailableError:
        logger.exception(
            "effective_access_unavailable correlation_id=%s subject=%s latency_ms=%.1f",
            correlation_id,
            subject,
            (time.monotonic() - started) * 1000,
        )
        return api_error(
            "authorization_unavailable",
            "Authorization service unavailable",
            status=503,
        )
    except Exception:
        logger.exception(
            "effective_access_unexpected_failure correlation_id=%s subject=%s latency_ms=%.1f",
            correlation_id,
            subject,
            (time.monotonic() - started) * 1000,
        )
        return api_error(
            "effective_access_failed",
            "Unexpected error resolving effective access",
            status=500,
        )

    logger.info(
        "effective_access_ok correlation_id=%s subject=%s is_superadmin=%s "
        "permission_count=%s latency_ms=%.1f",
        correlation_id,
        subject,
        result.is_superadmin,
        len(result.permissions),
        (time.monotonic() - started) * 1000,
    )

    return (
        jsonify(
            {
                "userId": str(result.user_id),
                "keycloakSubject": str(result.keycloak_subject),
                "permissions": result.permissions,
                "isSuperadmin": result.is_superadmin,
            }
        ),
        200,
    )
