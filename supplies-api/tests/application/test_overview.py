from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.services.overview_composition_service import OverviewCompositionService
from app.create_app import create_app
from app.domain.entities import AuthenticatedIdentity, EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.strategic_indicators_gateway import StrategicIndicatorsGateway


def _user(*, permissions: set[str], is_superadmin: bool = False) -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="analyst@delpi.com.br",
        name="Analyst",
        permissions=permissions,
        is_superadmin=is_superadmin,
        keycloak_sub="11111111-1111-1111-1111-111111111111",
        access_token="token",
    )


def _identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        sub="11111111-1111-1111-1111-111111111111",
        email="analyst@delpi.com.br",
        name="Analyst",
    )


def _stub_reads():
    reads = MagicMock()
    reads.get_otd.return_value = {"otd_percentage": 95.0, "goal_value": 98.0}
    reads.get_stock_value.return_value = {"total_stock_value": 1000.0}
    reads.get_inventory_turnover.return_value = {"inventory_turnover_times": 2.5}
    reads.get_cpv.return_value = {"cpv_percentage": 40.0}
    reads.get_negotiation_savings.return_value = {"total_savings": 500.0}
    reads.get_safety_stock_summary.return_value = {"below_safety_stock": 3}
    return reads


def test_overview_positive_seven_kpis():
    reads = _stub_reads()
    pr = MagicMock()
    pr.count_open_requests.return_value = 12
    si = MagicMock()
    si.metrics_by_kpi.return_value = {
        "KPI-OTD": {
            "goal_value": 98.0,
            "comparable_goal": 30.0,
            "reference_goal": 98.0,
            "score": 6.57,
            "performance_direction": "higher_is_better",
            "goal_mode": "standard",
            "goal": 98.0,
        },
    }

    service = OverviewCompositionService(
        delpi_reads=reads,
        purchase_requests=pr,
        strategic_indicators=si,
    )
    result = service.compose(
        _user(
            permissions={
                "supplies.access",
                "supplies.unit.filial-01",
            }
        ),
        branch="01",
        start_date="2026-09-01",
        end_date="2026-09-08",
    )

    assert result["scope"]["mode"] == "single"
    assert result["scope"]["branches"] == ["01"]
    assert len(result["kpis"]) == 7
    ids = [kpi["id"] for kpi in result["kpis"]]
    assert ids == [
        "KPI-OTD",
        "KPI-STOCK-VALUE",
        "KPI-TURNOVER",
        "KPI-CPV",
        "KPI-SAVINGS",
        "KPI-SC-OPEN",
        "KPI-CRITICAL-MP",
    ]
    assert all(kpi["status"] == "available" for kpi in result["kpis"])
    otd = next(k for k in result["kpis"] if k["id"] == "KPI-OTD")
    assert otd["value"] == 95.0
    assert next(k for k in result["kpis"] if k["id"] == "KPI-SC-OPEN")["value"] == 12.0
    assert otd["meta"] == 30.0
    assert otd["goalValue"] == 98.0
    assert otd["comparableGoal"] == 30.0
    assert otd["referenceGoal"] == 98.0
    assert otd["iddScore"] == 6.57
    assert otd["performanceDirection"] == "higher_is_better"
    assert otd["comparableGoal"] != otd["referenceGoal"]
    assert otd["temporalNature"] == "interval"
    assert next(k for k in result["kpis"] if k["id"] == "KPI-CRITICAL-MP")["temporalNature"] == (
        "snapshot"
    )


def test_overview_sibling_consolidated_two_units():
    reads = _stub_reads()
    reads.get_stock_value.side_effect = [
        {"total_stock_value": 100.0},
        {"total_stock_value": 200.0},
    ]
    pr = MagicMock()
    pr.count_open_requests.side_effect = [5, 7]
    si = MagicMock()
    si.metrics_by_kpi.return_value = {}

    result = OverviewCompositionService(
        delpi_reads=reads,
        purchase_requests=pr,
        strategic_indicators=si,
    ).compose(
        _user(
            permissions={
                "supplies.access",
                "supplies.unit.filial-01",
                "supplies.unit.filial-02",
            }
        ),
        branch=None,
        start_date="2026-09-01",
        end_date="2026-09-08",
    )

    assert result["scope"]["mode"] == "consolidated"
    assert result["scope"]["branches"] == ["01", "02"]
    stock = next(k for k in result["kpis"] if k["id"] == "KPI-STOCK-VALUE")
    assert stock["value"] == 300.0
    sc = next(k for k in result["kpis"] if k["id"] == "KPI-SC-OPEN")
    assert sc["value"] == 12.0


def test_overview_unit_cross_forbidden():
    service = OverviewCompositionService(
        delpi_reads=_stub_reads(),
        purchase_requests=MagicMock(),
        strategic_indicators=MagicMock(),
    )
    try:
        service.compose(
            _user(permissions={"supplies.manage"}),
            branch="02",
        )
        assert False, "expected AuthorizationError"
    except Exception as exc:
        assert exc.__class__.__name__ == "AuthorizationError"


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_overview_forbidden_without_analytics(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(permissions={"supplies.manage"})
    client = create_app().test_client()
    response = client.get(
        "/analytics/overview",
        headers={"Authorization": "Bearer good-token"},
    )
    assert response.status_code == 403


@patch("app.interfaces.http.auth_middleware.KeycloakJwtValidator.validate")
@patch(
    "app.interfaces.http.auth_middleware.AuthorizationService.resolve_effective_user"
)
def test_http_overview_positive(mock_resolve, mock_validate):
    mock_validate.return_value = _identity()
    mock_resolve.return_value = _user(
        permissions={
            "supplies.access",
            "supplies.unit.filial-01",
        }
    )

    reads = _stub_reads()
    pr = MagicMock()
    pr.count_open_requests.return_value = 1
    si = MagicMock()
    si.metrics_by_kpi.return_value = {}

    with patch(
        "app.interfaces.http.routes.analytics_routes.OverviewCompositionService",
        return_value=OverviewCompositionService(
            delpi_reads=reads,
            purchase_requests=pr,
            strategic_indicators=si,
        ),
    ):
        client = create_app().test_client()
        response = client.get(
            "/analytics/overview?branch=01&from=2026-09-01&to=2026-09-08",
            headers={"Authorization": "Bearer good-token"},
        )
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["kpis"]) == 7
    assert "partialFailures" in body


def _strategic_user() -> EffectiveUser:
    return _user(permissions={"supplies.access"})


def _si_indicators(*, realized_02, goal_02, indicator_score=6.57):
    rows = []
    for indicator_id in (
        "supplies-otd",
        "supplies-stock-value",
        "supplies-stock-turnover",
        "supplies-cpv",
        "supplies-negotiation-savings",
    ):
        rows.append(
            {
                "indicator_id": indicator_id,
                "goal_value": 98.0,
                "comparable_goal": 30.0,
                "reference_goal": 90.0,
                "goal_mode": "prorated",
                "goal_period_kind": "accumulated",
                "goal_period_partial": False,
                "performance_direction": "lower_is_better",
                "score": indicator_score,
                "value_suffix": "%",
                "value_decimals": 1,
                "realized": {"consolidated": 95.0, "01": 96.1, "02": realized_02},
                "goals": {"consolidated": 97.0, "01": 94.0, "02": goal_02},
            }
        )
    return rows


def _delpi_for_scopes(*, fail=False, score_02=6.0):
    delpi = MagicMock()

    def _get(_path, access_token=None, params=None, **_kwargs):
        if fail:
            raise RuntimeError("si down")
        branch = (params or {}).get("branch")
        if branch == "01":
            score, classification = 8.2, "Bom"
        elif branch == "02":
            score, classification = score_02, ("Atencao" if score_02 is not None else None)
        else:
            score, classification = 7.4, "Regular"
        return {
            "item": {
                "department_id": "supplies",
                "score": score,
                "classification": classification,
                "partial_success": False,
                "indicators": _si_indicators(realized_02=None, goal_02=None),
            }
        }

    delpi.get.side_effect = _get
    return delpi


def test_overview_strategic_context_and_unit_maps():
    gateway = StrategicIndicatorsGateway(delpi=_delpi_for_scopes())
    result = OverviewCompositionService(
        delpi_reads=_stub_reads(),
        purchase_requests=MagicMock(count_open_requests=MagicMock(return_value=4)),
        strategic_indicators=gateway,
    ).compose(
        _strategic_user(),
        branch=None,
        start_date="2026-09-01",
        end_date="2026-09-08",
    )

    scores = result["strategicContext"]["scores"]
    assert set(scores) == {"consolidated", "01", "02"}
    assert scores["consolidated"]["score"] == 7.4
    assert scores["01"]["classification"] == "Bom"
    assert scores["02"]["score"] == 6.0
    assert result["scope"]["mode"] == "consolidated"
    assert result["period"]["from"] == "2026-09-01"
    assert "partialFailures" in result

    strategic_ids = (
        "KPI-OTD",
        "KPI-STOCK-VALUE",
        "KPI-TURNOVER",
        "KPI-CPV",
        "KPI-SAVINGS",
    )
    for kpi_id in strategic_ids:
        strategic = next(k for k in result["kpis"] if k["id"] == kpi_id)["strategic"]
        assert strategic["indicatorId"]
        assert strategic["realized"]["consolidated"] == 95.0
        assert strategic["realized"]["01"] == 96.1
        assert strategic["realized"]["02"] is None
        assert strategic["goals"]["consolidated"] == 97.0
        assert strategic["goals"]["01"] == 94.0
        assert strategic["goals"]["02"] is None
        assert strategic["score"] == 6.57
        assert strategic["goalMode"] == "prorated"
        assert strategic["goalPeriodKind"] == "accumulated"
        assert strategic["performanceDirection"] == "lower_is_better"
        assert strategic["goalValue"] == 98.0
        assert strategic["comparableGoal"] == 30.0
        assert strategic["referenceGoal"] == 90.0

    by_id = {kpi["id"]: kpi for kpi in result["kpis"]}
    assert by_id["KPI-SC-OPEN"]["strategic"] is None
    assert by_id["KPI-CRITICAL-MP"]["strategic"] is None
    assert by_id["KPI-OTD"]["value"] == 95.0
    assert by_id["KPI-OTD"]["goalValue"] == 98.0
    assert by_id["KPI-OTD"]["comparableGoal"] == 30.0
    assert by_id["KPI-OTD"]["iddScore"] == 6.57
    assert any(item["kpiId"] == "KPI-STOCK-VALUE" for item in result["siValueDrift"])


def test_overview_branch_filter_keeps_only_selected_unit():
    gateway = StrategicIndicatorsGateway(delpi=_delpi_for_scopes())
    service = OverviewCompositionService(
        delpi_reads=_stub_reads(),
        purchase_requests=MagicMock(count_open_requests=MagicMock(return_value=1)),
        strategic_indicators=gateway,
    )
    for branch in ("01", "02"):
        result = service.compose(
            _strategic_user(),
            branch=branch,
            start_date="2026-09-01",
            end_date="2026-09-08",
        )
        assert set(result["strategicContext"]["scores"]) == {branch}
        otd = next(k for k in result["kpis"] if k["id"] == "KPI-OTD")["strategic"]
        assert set(otd["realized"]) == {branch}
        assert set(otd["goals"]) == {branch}


def test_overview_missing_department_score_stays_null():
    gateway = StrategicIndicatorsGateway(delpi=_delpi_for_scopes(score_02=None))
    result = OverviewCompositionService(
        delpi_reads=_stub_reads(),
        purchase_requests=MagicMock(count_open_requests=MagicMock(return_value=1)),
        strategic_indicators=gateway,
    ).compose(_strategic_user(), branch="02", start_date="2026-09-01", end_date="2026-09-08")
    assert result["strategicContext"]["scores"]["02"]["score"] is None


def test_overview_si_failure_keeps_operational_headline():
    gateway = StrategicIndicatorsGateway(delpi=_delpi_for_scopes(fail=True))
    result = OverviewCompositionService(
        delpi_reads=_stub_reads(),
        purchase_requests=MagicMock(count_open_requests=MagicMock(return_value=9)),
        strategic_indicators=gateway,
    ).compose(_strategic_user(), branch="01", start_date="2026-09-01", end_date="2026-09-08")
    otd = next(k for k in result["kpis"] if k["id"] == "KPI-OTD")
    assert otd["value"] == 95.0
    assert otd["status"] == "available"
    assert otd["strategic"] is None
    assert result["strategicContext"]["scores"] == {}
    assert any(item["source"] == "si" for item in result["partialFailures"])

