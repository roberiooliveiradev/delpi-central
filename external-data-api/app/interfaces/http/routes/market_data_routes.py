"""HTTP surface — ``/v1/market-data/*`` read APIs (PROC-0076).

Internal-only: individual S2S auth + consumer allowlist, same posture as
the frozen CNPJ route. These endpoints serve persisted history only —
they never reach the internet. Correlation IDs propagate via
``X-Correlation-Id`` and errors keep the ``{"detail", "code"}`` envelope.
"""

from __future__ import annotations

import logging
import uuid

from flask import Blueprint, g, jsonify, request

from app.application.contracts import ExternalDataError, RateLimitedError
from app.application.market_data_queries import (
    get_catalog,
    get_ingestion_status,
    list_fx_observations,
    list_metal_observations,
)
from app.infrastructure.s2s_auth import require_s2s_service

logger = logging.getLogger("external-data-api.market_data")

market_data_bp = Blueprint("market_data", __name__)

_ALLOWED_BFF_CLIENTS = ("supplies-api",)


def _correlation_id() -> str:
    return (
        (request.headers.get("X-Correlation-Id") or "").strip()
        or (request.headers.get("X-Request-Id") or "").strip()
        or str(uuid.uuid4())
    )


def _respond(payload, correlation_id: str, status: int = 200):
    response = jsonify(payload)
    response.headers["X-Correlation-Id"] = correlation_id
    return response, status


def _error_response(exc: ExternalDataError):
    body = {"detail": str(exc), "code": exc.code}
    response = jsonify(body)
    if isinstance(exc, RateLimitedError) and exc.retry_after:
        response.headers["Retry-After"] = str(exc.retry_after)
    return response, exc.http_status


@market_data_bp.errorhandler(ExternalDataError)
def _handle_error(exc: ExternalDataError):
    logger.info(
        "market_data_request_rejected code=%s status=%s",
        exc.code,
        exc.http_status,
    )
    return _error_response(exc)


@market_data_bp.get("/v1/market-data/catalog")
@require_s2s_service(allowed_clients=_ALLOWED_BFF_CLIENTS)
def get_market_catalog():
    """operationId: listMarketDataCatalogV1."""
    return _respond(get_catalog(), _correlation_id())


@market_data_bp.get("/v1/market-data/metals/observations")
@require_s2s_service(allowed_clients=_ALLOWED_BFF_CLIENTS)
def get_metal_observations():
    """operationId: listMetalObservationsV1."""
    payload = list_metal_observations(
        instrument_code=request.args.get("instrument_code"),
        date_from_raw=request.args.get("date_from"),
        date_to_raw=request.args.get("date_to"),
        limit_raw=request.args.get("limit"),
        cursor_raw=request.args.get("cursor"),
    )
    return _respond(payload, _correlation_id())


@market_data_bp.get("/v1/market-data/fx/observations")
@require_s2s_service(allowed_clients=_ALLOWED_BFF_CLIENTS)
def get_fx_observations():
    """operationId: listFxObservationsV1."""
    payload = list_fx_observations(
        pair=request.args.get("pair"),
        rate_kind=request.args.get("rate_kind"),
        date_from_raw=request.args.get("date_from"),
        date_to_raw=request.args.get("date_to"),
        limit_raw=request.args.get("limit"),
        cursor_raw=request.args.get("cursor"),
    )
    return _respond(payload, _correlation_id())


@market_data_bp.get("/v1/market-data/ingestion-status")
@require_s2s_service(allowed_clients=_ALLOWED_BFF_CLIENTS)
def get_market_ingestion_status():
    """operationId: getMarketDataIngestionStatusV1."""
    return _respond(get_ingestion_status(), _correlation_id())
