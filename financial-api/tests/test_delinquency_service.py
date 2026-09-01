from __future__ import annotations

import pytest

from financial_app.application.services.delinquency_service import (
    DelinquencyService,
    InvalidDelinquencyQuery,
)
from financial_app.domain.errors import BranchAccessDenied, InvalidPeriod
from tests.conftest import full_user, user
from tests.fakes import FakeFinancialGateway


def build() -> tuple[DelinquencyService, FakeFinancialGateway]:
    gateway = FakeFinancialGateway()
    return DelinquencyService(gateway), gateway


def test_summary_maps_envelope_to_camel_case() -> None:
    service, _ = build()
    result = service.summary(full_user(), start_date=None, end_date=None)

    assert result["period"]["startDate"] == "2025-08-01"
    assert result["period"]["endDateExclusive"] == "2026-08-01"
    assert result["totals"]["lateTitles"] == 24
    assert result["totals"]["titles"] == 120
    assert result["totals"]["totalAmount"] == 1_500_000.0
    assert result["indicators"]["onTimePctByCount"] == 80.0
    assert result["scopeNotice"]


def test_summary_accepts_legacy_total_titulos_alias() -> None:
    service, gateway = build()

    def legacy_summary(**_: object) -> dict:
        return {
            "success": True,
            "data": {
                "periodo": {
                    "data_inicio": "2025-08-01",
                    "data_fim_exclusiva": "2026-08-01",
                },
                "totais": {
                    "total_titulos": 88,
                    "titulos_em_dia": 70,
                    "titulos_atraso": 18,
                    "valor_total": 1.0,
                    "valor_atraso": 0.2,
                },
                "indicadores": {
                    "percentual_em_dia_qtd": 79.5,
                    "percentual_em_dia_valor": 80.0,
                    "percentual_inadimplencia_qtd": 20.5,
                    "percentual_inadimplencia_valor": 20.0,
                },
            },
        }

    gateway.fetch_delinquency_summary = legacy_summary  # type: ignore[method-assign]
    result = service.summary(full_user(), start_date=None, end_date=None, refresh=True)

    assert result["totals"]["titles"] == 88
    assert result["indicators"]["latePctByCount"] == 20.5


def test_monthly_and_aging_are_normalized() -> None:
    service, _ = build()

    monthly = service.monthly(full_user(), start_date=None, end_date=None)
    assert monthly["items"][0]["yearMonth"] == "2026-08"
    assert monthly["items"][0]["onTimePctByAmount"] == 80.0

    aging = service.aging(full_user(), start_date=None, end_date=None)
    assert [item["code"] for item in aging["items"]] == ["EM_DIA", "ATRASO_1_A_5_DIAS"]


def test_summary_for_customer_uses_customer_row_and_titles() -> None:
    service, gateway = build()
    result = service.summary(
        full_user(),
        start_date=None,
        end_date=None,
        customer_code="000001",
        store_code="01",
        refresh=True,
    )

    assert result["totals"]["titles"] == 40
    assert result["totals"]["lateTitles"] == 10
    assert result["totals"]["lateAmount"] == 120_000.0
    assert result["indicators"]["onTimePctByCount"] == 75.0
    assert result["indicators"]["averageDaysLate"] == 4.0
    assert "WEG" in result["scopeNotice"]
    assert gateway.call_kwargs("fetch_delinquency_titles")["customer_code"] == "000001"


def test_monthly_forwards_customer_filter() -> None:
    service, gateway = build()
    service.monthly(
        full_user(),
        start_date=None,
        end_date=None,
        customer_code="000001",
        store_code="01",
        refresh=True,
    )
    kwargs = gateway.call_kwargs("fetch_delinquency_monthly")
    assert kwargs["customer_code"] == "000001"
    assert kwargs["store_code"] == "01"


def test_aging_for_customer_aggregates_titles() -> None:
    service, gateway = build()
    result = service.aging(
        full_user(),
        start_date=None,
        end_date=None,
        customer_code="000001",
        store_code="01",
        refresh=True,
    )
    by_code = {item["code"]: item for item in result["items"]}
    assert by_code["ATRASO_1_A_5_DIAS"]["count"] == 1
    assert by_code["ATRASO_1_A_5_DIAS"]["amount"] == 25_000.0
    assert gateway.call_kwargs("fetch_delinquency_titles")["customer_code"] == "000001"


def test_dashboard_forwards_customer_filter() -> None:
    service, gateway = build()
    result = service.dashboard(
        full_user(),
        start_date=None,
        end_date=None,
        customer_code="000001",
        store_code="01",
        page=1,
        page_size=20,
        sort_by="late_amount",
        sort_dir="desc",
        only_with_delays=False,
        refresh=True,
    )

    assert result["summary"]["totals"]["titles"] == 40
    assert result["monthly"]["items"][0]["yearMonth"] == "2026-08"
    assert result["aging"]["items"]
    assert result["customers"]["items"][0]["customerCode"] == "000001"
    assert result["topDelinquentCustomers"]["items"][0]["customerCode"] == "000001"
    monthly_kwargs = gateway.call_kwargs("fetch_delinquency_monthly")
    assert monthly_kwargs["customer_code"] == "000001"
    assert monthly_kwargs["store_code"] == "01"
    title_calls = [name for name, _ in gateway.calls if name == "fetch_delinquency_titles"]
    assert len(title_calls) == 1


def test_dashboard_top_delinquent_uses_proportional_sort() -> None:
    service, gateway = build()
    result = service.dashboard(
        full_user(),
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
        sort_by="late_amount",
        sort_dir="desc",
        only_with_delays=False,
    )

    assert result["topDelinquentCustomers"]["items"][0]["customerCode"] == "000001"
    customer_calls = [
        kwargs for name, kwargs in gateway.calls if name == "fetch_delinquency_customers"
    ]
    assert len(customer_calls) == 2
    top_call = customer_calls[1]
    assert top_call["sort_by"] == "on_time_by_quantity_percent"
    assert top_call["sort_dir"] == "asc"
    assert top_call["only_with_delays"] is True
    assert top_call["page_size"] == 8


def test_customers_maps_pagination_and_sort() -> None:
    service, gateway = build()
    result = service.customers(
        full_user(),
        start_date=None,
        end_date=None,
        page=1,
        page_size=20,
        sort_by="late_amount",
        sort_dir="desc",
        search="weg",
        only_with_delays=True,
    )

    assert result["pagination"]["totalItems"] == 1
    assert result["pagination"]["isComplete"] is True
    assert result["sort"] == {"sortBy": "late_amount", "sortDir": "desc"}
    assert result["items"][0]["customerCode"] == "000001"
    assert gateway.call_kwargs("fetch_delinquency_customers")["search"] == "weg"


def test_titles_maps_delay_range_and_filters() -> None:
    service, _ = build()
    result = service.titles(
        full_user(),
        start_date=None,
        end_date=None,
        customer_code="000001",
        store_code="01",
        status="late",
        delay_range="ATRASO_1_A_5_DIAS",
        search=None,
        page=1,
        page_size=20,
        sort_by=None,
        sort_dir=None,
    )

    assert result["filters"]["status"] == "late"
    assert result["items"][0]["delayRange"]["label"] == "1 a 5 dias"
    assert result["items"][0]["paidOnTime"] is False
    assert result["items"][0]["daysLate"] == 4


def test_requires_delinquency_permission() -> None:
    service, _ = build()
    with pytest.raises(PermissionError):
        service.summary(user("financial.access"), start_date=None, end_date=None)


def test_consolidated_scope_requires_both_branches() -> None:
    service, _ = build()
    partial = user(
        "financial.access", "financial.delinquency.view", "financial.view.filial-01"
    )
    with pytest.raises(BranchAccessDenied):
        service.summary(partial, start_date=None, end_date=None)


def test_half_open_period_is_rejected() -> None:
    service, _ = build()
    with pytest.raises(InvalidPeriod):
        service.summary(full_user(), start_date="2026-01-01", end_date=None)


def test_delinquency_defaults_to_current_month_for_gateway() -> None:
    service, gateway = build()
    service.summary(full_user(), start_date=None, end_date=None, refresh=True)
    kwargs = gateway.call_kwargs("fetch_delinquency_summary")
    assert kwargs["start_date"].endswith("-01")
    assert kwargs["start_date"][:7] == kwargs["end_date"][:7]


def test_delinquency_period_converts_inclusive_end_for_gateway() -> None:
    service, gateway = build()
    service.summary(full_user(), start_date="2026-08-01", end_date="2026-08-21")
    kwargs = gateway.call_kwargs("fetch_delinquency_summary")
    assert kwargs["start_date"] == "2026-08-01"
    assert kwargs["end_date"] == "2026-08-22"


def test_invalid_sort_and_status_are_rejected() -> None:
    service, _ = build()
    with pytest.raises(InvalidDelinquencyQuery):
        service.customers(
            full_user(),
            start_date=None,
            end_date=None,
            page=1,
            page_size=20,
            sort_by="valor_total; DROP TABLE",
            sort_dir="desc",
            search=None,
            only_with_delays=True,
        )

    with pytest.raises(InvalidDelinquencyQuery):
        service.titles(
            full_user(),
            start_date=None,
            end_date=None,
            customer_code=None,
            store_code=None,
            status="pendente",
            delay_range=None,
            search=None,
            page=1,
            page_size=20,
            sort_by=None,
            sort_dir=None,
        )


def test_page_size_is_capped_by_catalog() -> None:
    service, gateway = build()
    service.customers(
        full_user(),
        start_date=None,
        end_date=None,
        page=0,
        page_size=5000,
        sort_by=None,
        sort_dir=None,
        search=None,
        only_with_delays=False,
    )
    kwargs = gateway.call_kwargs("fetch_delinquency_customers")
    assert kwargs["page"] == 1
    assert kwargs["page_size"] == 100


def test_repeated_reads_hit_the_cache() -> None:
    service, gateway = build()
    service.summary(full_user(), start_date=None, end_date=None)
    service.summary(full_user(), start_date=None, end_date=None)

    calls = [name for name, _ in gateway.calls if name == "fetch_delinquency_summary"]
    assert len(calls) == 1

    service.summary(full_user(), start_date=None, end_date=None, refresh=True)
    calls = [name for name, _ in gateway.calls if name == "fetch_delinquency_summary"]
    assert len(calls) == 2
