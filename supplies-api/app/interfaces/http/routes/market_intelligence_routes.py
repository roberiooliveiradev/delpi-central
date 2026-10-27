"""Market intelligence BFF routes (PROC-0076).

AuthZ: ``supplies.access`` (Core effective) — fail-closed like every
other Portal route; no new permission. Upstream S2S negatives are
technical failures and never surface as a user-facing 403.
"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from app.application.security.supplies_permissions import (
    can_use_market_intelligence,
)
from app.application.services.comex_analysis_service import (
    ComexAnalysisService,
    ComexConflictError,
    ComexForbiddenError,
    ComexNotFoundError,
    ComexValidationError,
)
from app.application.services.market_intelligence_service import (
    MarketDataNotFoundError,
    MarketIntelligenceService,
)
from app.domain.comex_analysis.lifecycle import GovernanceTransitionError
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
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
    # Rights-contract drift (pending/failed migration on the producer)
    # is technical unavailability — never a user permission fault and
    # distinct from a license decision on a ready contract.
    if exc.code == "EXTERNAL_DATA_CONTRACT_NOT_READY":
        return (
            jsonify(
                {
                    "detail": "External data contract not ready",
                    "code": "contract_not_ready",
                }
            ),
            503,
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


@market_intelligence_bp.get("/market-intelligence/imports/series")
@require_policy(can_use_market_intelligence)
def list_market_intelligence_import_series():
    """operationId: listMarketIntelligenceImportSeriesV1."""
    try:
        payload = _service().list_import_series(
            ncm_code=request.args.get("ncm"),
            granularity=request.args.get("granularity"),
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
            country_code=request.args.get("country_code"),
            state_code=request.args.get("state_code"),
        )
    except MarketDataNotFoundError as exc:
        return jsonify({"detail": str(exc), "code": "not_found"}), 404
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    except MarketDataGatewayError as exc:
        return _gateway_error_response(exc)
    return jsonify(payload), 200


@market_intelligence_bp.get("/market-intelligence/producer-prices/series")
@require_policy(can_use_market_intelligence)
def list_market_intelligence_producer_price_series():
    """operationId: listMarketIntelligenceProducerPriceSeriesV1."""
    try:
        payload = _service().list_producer_price_series(
            series_id=request.args.get("series_id"),
            granularity=request.args.get("granularity"),
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


@market_intelligence_bp.get("/market-intelligence/fx/series")
@require_policy(can_use_market_intelligence)
def list_market_intelligence_fx_series():
    """operationId: listMarketIntelligenceFxSeriesV1."""
    try:
        payload = _service().list_fx_series(
            fx_kind=request.args.get("fx_kind"),
            granularity=request.args.get("granularity"),
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


@market_intelligence_bp.get("/market-intelligence/quotes/series")
@require_policy(can_use_market_intelligence)
def list_market_intelligence_quote_series():
    """operationId: listMarketIntelligenceQuoteSeriesV1."""
    try:
        payload = _service().list_quotes_series(
            instruments=request.args.get("instruments"),
            granularity=request.args.get("granularity"),
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


@market_intelligence_bp.get("/market-intelligence/quotes/compare")
@require_policy(can_use_market_intelligence)
def list_market_intelligence_quote_compare():
    """operationId: listMarketIntelligenceQuoteCompareV1."""
    try:
        payload = _service().list_quotes_compare(
            instruments=request.args.get("instruments"),
            granularity=request.args.get("granularity"),
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


# ---------------------------------------------------------------------------
# PROC-0076.COMEX.S2/S3 — configurable Comex analysis
# ---------------------------------------------------------------------------


def _comex_error_response(exc):
    if isinstance(exc, ComexValidationError):
        return jsonify({"detail": str(exc), "code": exc.code}), 422
    if isinstance(exc, ComexNotFoundError):
        return jsonify({"detail": str(exc), "code": "not_found"}), 404
    if isinstance(exc, ComexForbiddenError):
        return jsonify({"detail": str(exc), "code": "forbidden"}), 403
    if isinstance(exc, (ComexConflictError, GovernanceTransitionError)):
        code = getattr(exc, "code", "conflict")
        return jsonify({"detail": str(exc), "code": code}), 409
    return None


def _delpi_error_response(exc: DelpiApiGatewayError):
    status = exc.status_code or 502
    # Upstream 401/403/5xx are technical faults — never a user permission
    # fault; only upstream 4xx business rejections surface to the caller.
    if status in (401, 403) or status >= 500:
        return (
            jsonify(
                {
                    "detail": "Product catalog unavailable",
                    "code": "catalog_unavailable",
                }
            ),
            503,
        )
    if status == 429:
        return (
            jsonify({"detail": "Product catalog rate limited", "code": "rate_limited"}),
            429,
        )
    return (
        jsonify({"detail": "Product catalog request rejected", "code": "bad_request"}),
        400,
    )


@market_intelligence_bp.get("/market-intelligence/comex/products/search")
@require_policy(can_use_market_intelligence)
def search_comex_products():
    """operationId: searchComexProductsV1."""
    try:
        payload = _comex_service().search_products(
            user=g.current_user, args=request.args
        )
    except DelpiApiGatewayError as exc:
        return _delpi_error_response(exc)
    return jsonify(payload), 200


@market_intelligence_bp.get("/market-intelligence/comex/ncm-governance")
@require_policy(can_use_market_intelligence)
def list_comex_ncm_governance():
    """operationId: listComexNcmGovernanceV1."""
    try:
        items = _comex_service().list_governance(
            status=request.args.get("status")
        )
    except (ComexValidationError,) as exc:
        return jsonify({"detail": str(exc), "code": exc.code}), 422
    return jsonify({"items": items}), 200


@market_intelligence_bp.get(
    "/market-intelligence/comex/ncm-governance/<governance_id>"
)
@require_policy(can_use_market_intelligence)
def get_comex_ncm_governance(governance_id):
    """operationId: getComexNcmGovernanceV1."""
    try:
        payload = _comex_service().get_governance(governance_id)
    except (
        ComexValidationError,
        ComexNotFoundError,
        ComexForbiddenError,
        ComexConflictError,
        GovernanceTransitionError,
    ) as exc:
        return _comex_error_response(exc)
    return jsonify(payload), 200


@market_intelligence_bp.post("/market-intelligence/comex/ncm-governance")
@require_policy(can_use_market_intelligence)
def create_comex_ncm_governance():
    """operationId: createComexNcmGovernanceV1."""
    body = request.get_json(silent=True) or {}
    try:
        payload = _comex_service().request_ncm(
            user=g.current_user,
            ncm_code=body.get("ncm_code"),
            description=body.get("description"),
            ncm_version=body.get("ncm_version"),
            family_code=body.get("family_code"),
            product_codes=body.get("product_codes"),
            notes=body.get("notes"),
            initial_status=body.get("initial_status"),
        )
    except (
        ComexValidationError,
        ComexNotFoundError,
        ComexForbiddenError,
        ComexConflictError,
        GovernanceTransitionError,
    ) as exc:
        return _comex_error_response(exc)
    return jsonify(payload), 201


@market_intelligence_bp.post(
    "/market-intelligence/comex/ncm-governance/<governance_id>/transition"
)
@require_policy(can_use_market_intelligence)
def transition_comex_ncm_governance(governance_id):
    """operationId: transitionComexNcmGovernanceV1."""
    body = request.get_json(silent=True) or {}
    try:
        payload = _comex_service().transition(
            user=g.current_user,
            governance_id=governance_id,
            to_status=body.get("to_status"),
            notes=body.get("notes"),
            expected_revision=body.get("expected_revision"),
        )
    except (
        ComexValidationError,
        ComexNotFoundError,
        ComexForbiddenError,
        ComexConflictError,
        GovernanceTransitionError,
    ) as exc:
        return _comex_error_response(exc)
    return jsonify(payload), 200


@market_intelligence_bp.get("/market-intelligence/comex/views")
@require_policy(can_use_market_intelligence)
def list_comex_views():
    """operationId: listComexMarketViewsV1."""
    items = _comex_service().list_views(user=g.current_user)
    return jsonify({"items": items}), 200


@market_intelligence_bp.post("/market-intelligence/comex/views")
@require_policy(can_use_market_intelligence)
def create_comex_view():
    """operationId: createComexMarketViewV1."""
    try:
        payload = _comex_service().create_view(
            user=g.current_user, body=request.get_json(silent=True) or {}
        )
    except (
        ComexValidationError,
        ComexNotFoundError,
        ComexForbiddenError,
        ComexConflictError,
        GovernanceTransitionError,
    ) as exc:
        return _comex_error_response(exc)
    return jsonify(payload), 201


@market_intelligence_bp.get("/market-intelligence/comex/views/<view_id>")
@require_policy(can_use_market_intelligence)
def get_comex_view(view_id):
    """operationId: getComexMarketViewV1."""
    try:
        payload = _comex_service().get_view(view_id, user=g.current_user)
    except (
        ComexValidationError,
        ComexNotFoundError,
        ComexForbiddenError,
        ComexConflictError,
        GovernanceTransitionError,
    ) as exc:
        return _comex_error_response(exc)
    return jsonify(payload), 200


@market_intelligence_bp.put("/market-intelligence/comex/views/<view_id>")
@require_policy(can_use_market_intelligence)
def update_comex_view(view_id):
    """operationId: updateComexMarketViewV1."""
    try:
        payload = _comex_service().update_view(
            view_id,
            user=g.current_user,
            body=request.get_json(silent=True) or {},
        )
    except (
        ComexValidationError,
        ComexNotFoundError,
        ComexForbiddenError,
        ComexConflictError,
        GovernanceTransitionError,
    ) as exc:
        return _comex_error_response(exc)
    return jsonify(payload), 200


@market_intelligence_bp.delete("/market-intelligence/comex/views/<view_id>")
@require_policy(can_use_market_intelligence)
def delete_comex_view(view_id):
    """operationId: deleteComexMarketViewV1."""
    try:
        _comex_service().delete_view(view_id, user=g.current_user)
    except (
        ComexValidationError,
        ComexNotFoundError,
        ComexForbiddenError,
        ComexConflictError,
        GovernanceTransitionError,
    ) as exc:
        return _comex_error_response(exc)
    return "", 204


def _comex_service() -> ComexAnalysisService:
    return ComexAnalysisService()
