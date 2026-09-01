from __future__ import annotations

import time

import pytest

from financial_app.application.services.cost_center_service import CostCenterService
from financial_app.application.services.delinquency_service import DelinquencyService
from financial_app.application.services.indicators_service import IndicatorsService
from financial_app.application.services.overview_service import OverviewService
from financial_app.domain.errors import BranchAccessDenied
from tests.conftest import full_user, user
from tests.fakes import FakeFinancialGateway, FakeStrategicIndicatorsGateway


def build(
    *, failing: set[str] | None = None, si_failing: bool = False
) -> tuple[OverviewService, FakeFinancialGateway]:
    gateway = FakeFinancialGateway(failing=failing)
    si_gateway = FakeStrategicIndicatorsGateway(failing=si_failing)
    service = OverviewService(
        gateway,
        delinquency=DelinquencyService(gateway),
        cost_centers=CostCenterService(gateway),
        indicators=IndicatorsService(si_gateway),
    )
    return service, gateway


def test_overview_aggregates_every_block() -> None:
    service, _ = build()
    result = service.build(full_user(), branch="01")

    assert result["branch"] == "01"
    start, end = result["period"]["startDate"], result["period"]["endDate"]
    assert start and end
    assert start <= end
    assert start.endswith("-01")

    blocks = result["blocks"]
    assert set(blocks) == {
        "rol",
        "ebitda",
        "fixedCost",
        "pmr",
        "delinquency",
        "costCenters",
        "indicators",
    }
    assert all(block["available"] for block in blocks.values())

    assert blocks["rol"]["value"] == 5_000_000.0
    assert blocks["ebitda"]["value"] == 18.4
    assert blocks["ebitda"]["target"] == 20.0
    assert blocks["fixedCost"]["value"] == 12.1
    assert blocks["pmr"]["value"] == 47.0
    assert blocks["delinquency"]["indicators"]["onTimePctByCount"] == 80.0
    assert blocks["delinquency"]["series"][0]["yearMonth"] == "2026-08"
    assert blocks["costCenters"]["totalAmount"] == 450_000.0
    assert blocks["costCenters"]["top"][0]["code"] == "1101"
    assert blocks["indicators"]["department"]["idd"] == 8.4


def test_failing_block_does_not_break_the_screen() -> None:
    service, _ = build(failing={"fetch_pmr"})
    blocks = service.build(full_user(), branch="01")["blocks"]

    assert blocks["pmr"]["available"] is False
    assert blocks["pmr"]["error"]
    assert blocks["rol"]["available"] is True
    assert blocks["delinquency"]["available"] is True


def test_missing_financial_sheet_uses_configured_message() -> None:
    from financial_app.domain.errors import DelpiGatewayError

    service, gateway = build()

    def explode(**_: object) -> dict:
        raise DelpiGatewayError("sheet_id is required")

    gateway.fetch_ebitda_pct = explode  # type: ignore[method-assign]
    blocks = service.build(full_user(), branch="01")["blocks"]

    assert blocks["ebitda"]["available"] is False
    assert "planilha financeira" in blocks["ebitda"]["error"]
    assert blocks["rol"]["available"] is True


def test_strategic_indicators_outage_only_marks_its_block() -> None:
    service, _ = build(si_failing=True)
    blocks = service.build(full_user(), branch="01")["blocks"]

    assert blocks["indicators"]["available"] is True
    assert blocks["indicators"]["department"]["available"] is False
    assert blocks["rol"]["available"] is True


def test_missing_module_permission_marks_block_as_forbidden() -> None:
    service, _ = build()
    limited = user("financial.access", "financial.view.filial-01")
    blocks = service.build(limited, branch="01")["blocks"]

    assert blocks["rol"]["available"] is True
    assert blocks["delinquency"]["available"] is False
    assert blocks["delinquency"]["error"]
    assert blocks["costCenters"]["available"] is False
    assert blocks["indicators"]["available"] is False


def test_consolidated_requires_both_branches() -> None:
    service, _ = build()
    partial = user("financial.access", "financial.view.filial-01")
    with pytest.raises(BranchAccessDenied):
        service.build(partial, branch=None)


def test_access_permission_is_required() -> None:
    service, _ = build()
    with pytest.raises(PermissionError):
        service.build(user(), branch="01")


def test_overview_loads_independent_gateway_calls_in_parallel() -> None:
    service, gateway = build()
    sleep_s = 0.05
    original_record = gateway._record

    def slow_record(name: str, **kwargs: object) -> None:
        time.sleep(sleep_s)
        original_record(name, **kwargs)

    gateway._record = slow_record  # type: ignore[method-assign]

    started = time.monotonic()
    result = service.build(full_user(), branch="01")
    elapsed = time.monotonic() - started

    assert result["blocks"]["rol"]["available"] is True
    assert result["blocks"]["delinquency"]["available"] is True
    # 8 chamadas ao gateway financeiro; em série passaria de 0,40 s.
    assert elapsed < 0.32
    assert {name for name, _ in gateway.calls} >= {
        "fetch_rol",
        "fetch_ebitda_pct",
        "fetch_fixed_cost_pct",
        "fetch_pmr",
        "fetch_delinquency_summary",
        "fetch_delinquency_monthly",
    }
