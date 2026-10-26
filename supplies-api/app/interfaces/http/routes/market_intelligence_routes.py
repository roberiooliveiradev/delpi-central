"""Market intelligence BFF routes (PROC-0076).

AuthZ: ``supplies.access`` (Core effective) — fail-closed like every
other Portal route; no new permission. Upstream S2S negatives are
technical failures and never surface as a user-facing 403.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.application.security.supplies_permissions import (
    can_use_market_intelligence,
)
from app.application.services.market_intelligence_service import (
    MarketDataNotFoundError,
    MarketIntelligenceService,
)
from app.infrastructure.gateways.market_data_gateway import (
    MarketDataGatewayError,
)
from app.interfaces.http.auth_decorators import require_policy

market_intelligence_bp = Blueprint("market_intelligence", __name__)


def _gateway_error_response(exc: MarketDataGatewayError):
    status = exc.status_code or 502
    if status == 429:
        response = jsonify(
            {"detail": "External data rate limited", "code": "rate_limited"}
        )
        if exc.retry_after:
            response.headers["Retry-After"] = str(exc.retry_after)
        return response, 429
    if status == 504 or exc.code == "upstream_timeout":
        return (
            jsonify(
                {"detail": "External data timeout", "code": "gateway_timeout"}
            ),
            504,
        )
    # License quarantine is a source-state, never a user permission
    # fault — a dedicated code keeps it distinct from user 403.
    if exc.code == "EXTERNAL_DATA_USE_NOT_APPROVED":
        return (
            jsonify(
                {
                    "detail": "Source display use pending approval",
                    "code": "source_use_not_approved",
                }
            ),
            503,
        )
    # 401/403 upstream (S2S) are technical faults — never a user 403.
    if status in (401, 403) or status >= 500:
        return (
            jsonify(
                {
                    "detail": "External data service unavailable",
                    "code": "external_data_unavailable",
                }
            ),
            503,
        )
    # Upstream 4xx that survived local validation is a contract drift —
    # report as a bad gateway, not as the user's fault.
    return (
        jsonify({"detail": "External data contract error", "code": "bad_gateway"}),
        502,
    )


def _service() -> MarketIntelligenceService:
    return MarketIntelligenceService()


@market_intelligence_bp.get("/market-intelligence/filters")
@require_policy(can_use_market_intelligence)
def get_market_intelligence_filters():
    """operationId: listMarketIntelligenceFiltersV1."""
    try:
        payload = _service().get_filters()
    except MarketDataGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200


@market_intelligence_bp.get("/market-intelligence/summary")
@require_policy(can_use_market_intelligence)
def get_market_intelligence_summary():
    """operationId: getMarketIntelligenceSummaryV1."""
    try:
        payload = _service().get_summary(
            instrument_code=request.args.get("instrument"),
            currency=request.args.get("currency"),
            fx_kind=request.args.get("fx_kind"),
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
        )
    except MarketDataNotFoundError as exc:
        return jsonify({"detail": str(exc), "code": "not_found"}), 404
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except MarketDataGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200


@market_intelligence_bp.get("/market-intelligence/series")
@require_policy(can_use_market_intelligence)
def list_market_intelligence_series():
    """operationId: listMarketIntelligenceSeriesV1."""
    try:
        payload = _service().list_series(
            instrument_code=request.args.get("instrument"),
            currency=request.args.get("currency"),
            granularity=request.args.get("granularity"),
            fx_kind=request.args.get("fx_kind"),
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
        )
    except MarketDataNotFoundError as exc:
        return jsonify({"detail": str(exc), "code": "not_found"}), 404
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except MarketDataGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200


@market_intelligence_bp.get("/market-intelligence/monthly-averages")
@require_policy(can_use_market_intelligence)
def list_market_intelligence_monthly_averages():
    """operationId: listMarketIntelligenceMonthlyAveragesV1."""
    try:
        payload = _service().list_monthly_averages(
            instrument_code=request.args.get("instrument"),
            currency=request.args.get("currency"),
            fx_kind=request.args.get("fx_kind"),
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
            page=request.args.get("page"),
            page_size=request.args.get("page_size"),
        )
    except MarketDataNotFoundError as exc:
        return jsonify({"detail": str(exc), "code": "not_found"}), 404
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except MarketDataGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200
