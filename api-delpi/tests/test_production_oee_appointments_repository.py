from unittest.mock import MagicMock, patch

from app.application.dto.production.get_production_oee_request import (
    GetProductionOeeRequest,
)
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


def test_oee_by_branch_sql_groups_by_raw_filial_column() -> None:
    import inspect

    source = inspect.getsource(
        OverallEquipmentEffectivenessRepository._load_overall_equipment_effectiveness_by_branch
    )
    assert "GROUP BY EF.FILIAL" in source
    assert "GROUP BY RTRIM(LTRIM(EF.FILIAL))" not in source


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
