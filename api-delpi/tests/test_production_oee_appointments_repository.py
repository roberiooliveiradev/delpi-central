from unittest.mock import MagicMock, patch

from app.application.dto.production.get_production_oee_request import (
    GetProductionOeeRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.models.page import Page
from app.application.services.production.production_kpi_cache import (
    production_oee_appointments_bundle_cache_key,
)
from app.composition.query_cache_composer import build_query_cache
from app.infrastructure.persistence.totvs.production_repositories.overall_equipment_effectiveness_repository import (
    OverallEquipmentEffectivenessRepository,
)


def test_oee_appointments_bundle_uses_single_loader_and_cache() -> None:
    repository = OverallEquipmentEffectivenessRepository()
    request = GetProductionOeeRequest(
        branch="01",
        start_date="2026-06-01",
        end_date="2026-06-24",
        page=1,
        page_size=20,
    )
    summary = {
        "total_appointments": 4,
        "valid_appointments": 3,
        "outlier_appointments": 1,
        "avg_oee_pct": 70.0,
    }
    page = Page(items=[{"appointment_id": 1}], total=1, page=1, page_size=20)

    with patch.object(
        OverallEquipmentEffectivenessRepository,
        "_load_oee_appointments_bundle",
        return_value=(summary, page),
    ) as loader:
        first_summary, first_page = repository.get_oee_appointments_bundle(request)
        second_summary, second_page = repository.get_oee_appointments_bundle(request)

    assert first_summary == summary
    assert first_page.total == 1
    assert second_summary == summary
    assert second_page.total == 1
    loader.assert_called_once()

    cache_key = production_oee_appointments_bundle_cache_key(request)
    cached = build_query_cache().get(cache_key)
    assert cached is not None
    assert cached["summary"]["total_appointments"] == 4


def test_oee_appointments_materialized_cache_reused_across_pages() -> None:
    from app.composition.query_cache_composer import reset_query_cache_for_tests

    reset_query_cache_for_tests()
    repository = OverallEquipmentEffectivenessRepository()
    base_request = GetProductionOeeRequest(
        branch="01",
        start_date="2026-06-01",
        end_date="2026-06-24",
        page=1,
        page_size=20,
    )
    page_two_request = GetProductionOeeRequest(
        branch="01",
        start_date="2026-06-01",
        end_date="2026-06-24",
        page=2,
        page_size=20,
    )
    rows = [
        {
            "appointment_id": index,
            "status": "valid",
            "branch": "01",
            "oee_pct": 80.0,
            "production_date": "2026-06-10",
            "production_order": f"{index:05d}",
            "operation": "01",
        }
        for index in range(30)
    ]

    with patch.object(
        repository,
        "execute_query_multiple",
        return_value=[{"data": rows}],
    ) as sql_mock:
        with patch.object(repository, "__enter__", return_value=repository):
            with patch.object(repository, "__exit__", return_value=False):
                _first_summary, first_page = repository.get_oee_appointments_bundle(
                    base_request
                )
                _second_summary, second_page = repository.get_oee_appointments_bundle(
                    page_two_request
                )

    sql_mock.assert_called_once()
    assert first_page.page == 1
    assert len(first_page.items) == 20
    assert second_page.page == 2
    assert len(second_page.items) == 10


def test_oee_by_branch_derives_from_daily_series_without_extra_scan() -> None:
    repository = OverallEquipmentEffectivenessRepository()
    request = ProductionRequest(
        branch=None,
        start_date="2026-05-01",
        end_date="2026-05-31",
    )
    daily_rows = [
        {
            "production_date": "2026-05-10",
            "branch": "01",
            "oee_pct": 80.0,
            "appointment_count": 2,
            "efficiency_sum": 170.0,
            "efficiency_sample_count": 2,
        },
        {
            "production_date": "2026-05-11",
            "branch": "01",
            "oee_pct": 90.0,
            "appointment_count": 1,
            "efficiency_sum": 90.0,
            "efficiency_sample_count": 1,
        },
    ]

    with patch.object(
        OverallEquipmentEffectivenessRepository,
        "list_oee_kpi_by_day_and_branch",
        return_value=daily_rows,
    ) as daily_loader:
        rows = repository._load_overall_equipment_effectiveness_by_branch(request)

    daily_loader.assert_called_once()
    assert rows == [{"branch": "01", "oee_pct": round((170.0 + 90.0) / 3, 2)}]


def test_oee_appointment_summary_and_list_reuse_bundle() -> None:
    repository = OverallEquipmentEffectivenessRepository()
    request = GetProductionOeeRequest(
        branch="02",
        start_date="2026-06-01",
        end_date="2026-06-24",
    )
    bundle_mock = MagicMock(
        return_value=(
            {"total_appointments": 2, "valid_appointments": 2, "outlier_appointments": 0},
            Page(items=[{"branch": "02"}], total=1, page=1, page_size=20),
        )
    )

    with patch.object(
        OverallEquipmentEffectivenessRepository,
        "get_oee_appointments_bundle",
        bundle_mock,
    ):
        summary = repository.get_oee_appointment_summary(request)
        page = repository.list_oee_appointments(request)

    assert summary["total_appointments"] == 2
    assert page.total == 1
    assert bundle_mock.call_count == 2
