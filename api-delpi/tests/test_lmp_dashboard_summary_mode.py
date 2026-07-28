"""Smoke: contrato OpenAPI do summary LMP (summary_mode + operation_id)."""

from inspect import signature

from app.interface.http.query_param_enums import (
    LMP_SUMMARY_MODE_VALUES,
    LMP_SUMMARY_MODE_QUERY,
)
from app.interface.http.routes.engineering.engineering_router import (
    lmps_dashboard_summary_route,
)


def test_lmp_summary_mode_query_defaults_to_kpi() -> None:
    query = LMP_SUMMARY_MODE_QUERY()
    assert query.default == "kpi"
    assert LMP_SUMMARY_MODE_VALUES == ("kpi", "full")


def test_lmps_dashboard_summary_route_exposes_summary_mode() -> None:
    """operation_id canônico: get_lmps_dashboard_summary (meta / Saúde SQL)."""
    params = signature(lmps_dashboard_summary_route).parameters
    assert "summary_mode" in params
