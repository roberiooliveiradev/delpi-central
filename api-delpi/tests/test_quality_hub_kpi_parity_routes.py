from __future__ import annotations

import json
from unittest.mock import MagicMock, patch


def _body(response) -> dict:
    return json.loads(response.body.decode())


@patch("app.interface.http.routes.quality.ppm_routes.enrich_dashboard_metric", side_effect=lambda p, **_: p)
@patch("app.interface.http.routes.quality.ppm_routes.build_get_ppm_summary_use_case")
def test_ppm_internal_summary_attaches_value_and_operational_summary(
    mock_build_use_case: MagicMock,
    _mock_enrich: MagicMock,
) -> None:
    from app.interface.http.routes.quality.ppm_routes import get_internal_ppm_summary

    mock_build_use_case.return_value.execute.return_value.to_dict.return_value = {
        "ppm": 12.5,
        "total_produzido_un": 800.0,
        "total_produzido_milheiro": 0.8,
        "total_devolvido_un": 10.0,
    }

    response = get_internal_ppm_summary(
        branch="01",
        start_date="2026-07-01",
        end_date="2026-07-31",
        date_start=None,
        date_end=None,
        product_prefix=None,
    )
    assert response.status_code == 200
    data = _body(response)["data"]
    assert data["ppm"] == 12.5
    assert data["value"] == 12.5
    assert data["total_produzido_un"] == 800.0
    summary = data["summary"]
    assert summary["branch_filter_applied"] is True
    assert summary["consolidated_across_branches"] is False
    assert summary["is_complete"] is True
    assert summary["ppm"] == 12.5
    assert summary["total_produzido_un"] == 800.0
    assert summary["period"] == {"start": "2026-07-01", "end": "2026-07-31"}


@patch("app.interface.http.routes.quality.quality_router.enrich_dashboard_metric", side_effect=lambda p, **_: p)
@patch("app.interface.http.routes.quality.quality_router.build_get_audit_5s_summary_use_case")
def test_audit_5s_summary_attaches_value_and_operational_summary(
    mock_build_use_case: MagicMock,
    _mock_enrich: MagicMock,
) -> None:
    from app.interface.http.routes.quality.quality_router import get_audit_5s_summary

    mock_build_use_case.return_value.execute.return_value.to_dict.return_value = {
        "average_score": 8.7,
        "list_audits": [],
    }

    response = get_audit_5s_summary(
        start_date="2026-07-01",
        end_date="2026-07-31",
        branch="02",
    )
    assert response.status_code == 200
    data = _body(response)["data"]
    assert data["average_score"] == 8.7
    assert data["value"] == 8.7
    summary = data["summary"]
    assert summary["branch_filter_applied"] is True
    assert summary["average_score"] == 8.7
    assert summary["period"] == {"start": "2026-07-01", "end": "2026-07-31"}
