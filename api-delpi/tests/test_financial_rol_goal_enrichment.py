"""Meta ROL no Portal Financeiro — mesma fonte SI do Comercial (`commercial_rol`)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_FINANCIAL = "app.interface.http.routes.financial.financial_routes"


@patch(
    f"{_FINANCIAL}.enrich_dashboard_metric",
    side_effect=lambda payload, **_: {
        **payload,
        "comparable_goal": 800_000.0,
        "rol_target_pct": 85.6,
        "target": 800_000.0,
    },
)
@patch(f"{_FINANCIAL}.build_get_rol_use_case")
def test_get_financial_rol_enriches_commercial_rol_goal(mock_build, mock_enrich) -> None:
    import app.interface.http.routes.financial.financial_routes as router_mod
    from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys

    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "01",
        "start_date": "20260901",
        "end_date": "20260901",
        "rol": 684_900.0,
        "gross_revenue": 750_000.0,
        "returns": 0.0,
        "discounts": 0.0,
    }
    mock_build.return_value = use_case

    response = router_mod.get_rol(
        branch="01",
        start_date="2026-09-01",
        end_date="2026-09-01",
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_financial_rol",
        shape="scalar",
        entity="financial_rol",
    )
    assert payload["data"]["rol"] == 684_900.0
    assert payload["data"]["target"] == 800_000.0
    assert payload["data"]["rol_target_pct"] == 85.6

    mock_enrich.assert_called_once()
    enrich_kwargs = mock_enrich.call_args.kwargs
    assert enrich_kwargs["source_key"] == goal_keys.COMMERCIAL_ROL
    assert enrich_kwargs["recompute_target_pct_from"] == "rol"
    assert enrich_kwargs["branch"] == "01"
    assert enrich_kwargs["start_date"] == "2026-09-01"
    assert enrich_kwargs["end_date"] == "2026-09-01"
