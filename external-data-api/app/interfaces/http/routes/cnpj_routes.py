"""HTTP surface — ``GET /v1/cnpj/{cnpj}`` (X0 §4 frozen contract).

Internal-only route: individual S2S auth + per-capability consumer
allowlist; the validated client_id is the rate-limit ``consumer``
dimension. Correlation IDs propagate via ``X-Request-Id`` /
``X-Correlation-Id`` and are echoed back. Error mapping follows the
frozen ``{"detail", "code"}`` envelope.
"""

from __future__ import annotations

import logging
import uuid

from flask import Blueprint, g, jsonify, request

from app.application.contracts import ExternalDataError, RateLimitedError
from app.application.lookup_cnpj_use_case import LookupCnpjUseCase
from app.infrastructure.providers.brasilapi_cnpj_provider import (
    build_cnpj_provider,
)
from app.infrastructure.rate_limits import rate_limiter
from app.infrastructure.s2s_auth import require_s2s_service

logger = logging.getLogger("external-data-api.cnpj")

cnpj_bp = Blueprint("cnpj", __name__)

_ALLOWED_BFF_CLIENTS = ("supplies-api",)


def _correlation_id() -> str:
    return (
        (request.headers.get("X-Correlation-Id") or "").strip()
        or (request.headers.get("X-Request-Id") or "").strip()
        or str(uuid.uuid4())
    )


def _external_error_response(exc: ExternalDataError):
    body = {"detail": str(exc), "code": exc.code}
    response = jsonify(body)
    if isinstance(exc, RateLimitedError) and exc.retry_after:
        response.headers["Retry-After"] = str(exc.retry_after)
    return response, exc.http_status


@cnpj_bp.errorhandler(ExternalDataError)
def _handle_external_error(exc: ExternalDataError):
    logger.info(
        "cnpj_request_rejected code=%s status=%s", exc.code, exc.http_status
    )
    return _external_error_response(exc)


@cnpj_bp.get("/v1/cnpj/<cnpj>")
@require_s2s_service(allowed_clients=_ALLOWED_BFF_CLIENTS)
def get_cnpj(cnpj: str):
    correlation_id = _correlation_id()
    consumer = str(getattr(g.service_identity, "client_id", "") or "unknown")
    try:
        result = LookupCnpjUseCase(
            provider=build_cnpj_provider(),
            limiter=rate_limiter(),
        ).execute(
            tax_id=cnpj,
            consumer=consumer,
            correlation_id=correlation_id,
        )
    except ExternalDataError as exc:
        logger.info(
            "cnpj_lookup_failed code=%s consumer=%s",
            exc.code,
            consumer,
        )
        return _external_error_response(exc)

    response = jsonify(result)
    response.headers["X-Correlation-Id"] = correlation_id
    return response, 200
