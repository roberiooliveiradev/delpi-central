from __future__ import annotations

import pytest

from financial_app.application.services.indicators_service import IndicatorsService
from tests.conftest import full_user, user
from tests.fakes import FakeStrategicIndicatorsGateway


def test_department_maps_idd_and_indicators() -> None:
    service = IndicatorsService(FakeStrategicIndicatorsGateway())
    result = service.department(full_user())

    assert result["available"] is True
    assert result["idd"] == 8.4
    assert result["departmentId"] == "financial"
    assert result["indicators"][0]["indicatorId"] == "fin-ebitda"
    assert result["indicators"][0]["weightPct"] == 40.0
    assert result["indicators"][0]["gap"] == -1.6
    assert result["notice"] is None


def test_partial_success_adds_notice() -> None:
    service = IndicatorsService(FakeStrategicIndicatorsGateway(partial=True))
    result = service.department(full_user())

    assert result["partialSuccess"] is True
    assert result["notice"]


def test_department_degrades_when_si_is_down() -> None:
    service = IndicatorsService(FakeStrategicIndicatorsGateway(failing=True))
    result = service.department(full_user())

    assert result["available"] is False
    assert result["reason"]
    assert "SI fora do ar" in result["detail"]


def test_global_score_maps_hero() -> None:
    service = IndicatorsService(FakeStrategicIndicatorsGateway())
    result = service.global_score(full_user())

    assert result["available"] is True
    assert result["igd"] == 7.9
    assert result["bestDepartment"] == "Qualidade"


def test_global_score_degrades_when_si_is_down() -> None:
    service = IndicatorsService(FakeStrategicIndicatorsGateway(failing=True))
    assert service.global_score(full_user())["available"] is False


def test_consolidated_branch_is_sent_as_global_scope() -> None:
    gateway = FakeStrategicIndicatorsGateway()
    IndicatorsService(gateway).department(full_user(), branch="all")

    assert gateway.calls[0][1]["branch"] is None


def test_requires_indicators_permission() -> None:
    service = IndicatorsService(FakeStrategicIndicatorsGateway())
    with pytest.raises(PermissionError):
        service.department(user("financial.access"))
