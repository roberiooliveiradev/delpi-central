from flask import Blueprint, g, jsonify, request

from app.application.services.otd_series_service import OtdSeriesService
from app.application.services.overview_composition_service import OverviewCompositionService
from app.interfaces.http.auth_decorators import require_permission

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/analytics/overview")
@require_permission("supplies.analytics.access")
def get_analytics_overview():
    """operationId: get_supplies_overview"""
    branch = (request.args.get("branch") or "").strip() or None
    start_date = (request.args.get("from") or request.args.get("start_date") or "").strip() or None
    end_date = (request.args.get("to") or request.args.get("end_date") or "").strip() or None
    service = OverviewCompositionService()
    return jsonify(
        service.compose(
            g.current_user,
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
    ), 200


@analytics_bp.get("/analytics/otd/series")
@require_permission("supplies.analytics.access")
def get_analytics_otd_series():
    """operationId: get_supplies_otd_series"""
    branch = (request.args.get("branch") or "").strip() or None
    start_date = (request.args.get("from") or request.args.get("start_date") or "").strip() or None
    end_date = (request.args.get("to") or request.args.get("end_date") or "").strip() or None
    granularity = (request.args.get("granularity") or "month").strip() or "month"
    service = OtdSeriesService()
    return jsonify(
        service.compose(
            g.current_user,
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
        )
    ), 200
