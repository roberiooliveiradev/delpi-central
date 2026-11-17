from flask import Blueprint, g, jsonify, request

from app.application.services.otd_aggregate_service import OtdAggregateService
from app.application.services.otd_series_service import OtdSeriesService
from app.application.services.overview_composition_service import (
    OverviewCompositionService,
    normalize_overview_branches,
)
from app.application.security.supplies_permissions import can_use_analytics
from app.interfaces.http.auth_decorators import require_policy, require_units
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGateway, DelpiApiGatewayError
from app.infrastructure.gateways.delpi_envelope import unwrap_delpi_envelope

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/analytics/overview")
@require_policy(can_use_analytics)
def get_analytics_overview():
    """operationId: get_supplies_overview"""
    branches = _branch_args()
    start_date = (request.args.get("from") or request.args.get("start_date") or "").strip() or None
    end_date = (request.args.get("to") or request.args.get("end_date") or "").strip() or None
    service = OverviewCompositionService()
    try:
        payload = service.compose(
            g.current_user,
            branches=branches,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    return jsonify(payload), 200


def _branch_args() -> list[str]:
    values: list[str] = []
    for raw in request.args.getlist("branch"):
        values.extend(part.strip() for part in str(raw).split(",") if part.strip())
    return values


@analytics_bp.get("/analytics/otd/series")
@require_policy(can_use_analytics)
def get_analytics_otd_series():
    """operationId: get_supplies_otd_series"""
    branches = _branch_args()
    start_date = (request.args.get("from") or request.args.get("start_date") or "").strip() or None
    end_date = (request.args.get("to") or request.args.get("end_date") or "").strip() or None
    granularity = (request.args.get("granularity") or "month").strip() or "month"
    try:
        effective = normalize_overview_branches(branches)
    except ValueError as exc:
        return jsonify({"detail": str(exc), "code": "unprocessable"}), 422
    series_branch = effective[0] if len(effective) == 1 else None
    service = OtdSeriesService()
    return jsonify(
        service.compose(
            g.current_user,
            branch=series_branch,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
        )
    ), 200


@analytics_bp.get("/analytics/otd")
@require_policy(can_use_analytics)
def get_analytics_otd():
    """operationId: get_portal_otd"""
    branch = (request.args.get("branch") or "").strip() or None
    start_date = (request.args.get("from") or request.args.get("start_date") or "").strip() or None
    end_date = (request.args.get("to") or request.args.get("end_date") or "").strip() or None
    service = OtdAggregateService()
    return jsonify(
        service.compose(
            g.current_user,
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
    ), 200


@analytics_bp.get("/analytics/freight-impact")
@require_policy(can_use_analytics)
@require_units("branch")
def get_portal_freight_impact():
    """GLPI #1567 — authorized user/branch scope at BFF, trusted S2S on api-delpi."""
    params = {
        "branch": request.args.getlist("branch"),
        "date_from": (request.args.get("date_from") or "").strip(),
        "date_to": (request.args.get("date_to") or "").strip(),
        "page": (request.args.get("page") or "1").strip(),
        "page_size": (request.args.get("page_size") or "25").strip(),
        "situation": (request.args.get("situation") or "all").strip(),
        "date_mode": (request.args.get("date_mode") or "issue").strip(),
    }
    try:
        raw = DelpiApiGateway().get(
            "/supplies/freight-impact",
            access_token=g.current_user.access_token or "",
            params=params,
        )
    except DelpiApiGatewayError as exc:
        status = exc.status_code or 502
        if status in (401, 403):
            return jsonify({"detail": "Acesso negado ao indicador.", "code": "forbidden"}), status
        if status == 422:
            return jsonify({
                "detail": exc.upstream_message or "Verifique as filiais e o período.",
                "code": "unprocessable",
            }), 422
        return jsonify({"detail": "Dados de frete indisponíveis.", "code": "bad_gateway"}), 502
    data = unwrap_delpi_envelope(raw)
    if not isinstance(data, dict) or not isinstance(data.get("summary"), dict):
        return jsonify({"detail": "Resposta de frete inválida.", "code": "bad_gateway"}), 502
    return jsonify(data), 200
