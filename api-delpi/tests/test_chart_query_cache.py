from unittest.mock import MagicMock, patch

from app.application.dto.commercial.commercial_rol_series_request import (
    CommercialRolSeriesRequest,
)
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.dto.production.production_oee_series_request import (
    ProductionOeeSeriesRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.services.charts.chart_series_cache_keys import (
    commercial_rol_series_cache_key,
    production_oee_series_cache_key,
)
from app.application.services.financial.financial_rol_cache import financial_rol_cache_key
from app.application.use_cases.commercial.get_commercial_rol_series_use_case import (
    GetCommercialRolSeriesUseCase,
)
from app.application.use_cases.production.get_production_oee_series_use_case import (
    GetProductionOeeSeriesUseCase,
)
from app.composition.query_cache_composer import build_query_cache, reset_query_cache_for_tests
from app.domain.entities.production.overall_equipment_effectiveness import (
    OverallEquipmentEffectiveness,
)
from app.domain.services.query_cache_stats_service import reset_query_cache_stats_for_tests
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import (
    FinancialRepository,
)


def setup_function() -> None:
    reset_query_cache_stats_for_tests()
    reset_query_cache_for_tests()


def test_financial_rol_cache_key_varies_by_segment() -> None:
    base = GetRolRequest(branch="01", start_date="2026-01-01", end_date="2026-01-31")
    with_segment = GetRolRequest(
        branch="01",
        start_date="2026-01-01",
        end_date="2026-01-31",
        customer_segment="weg",
    )
    assert financial_rol_cache_key(base) != financial_rol_cache_key(with_segment)


def test_financial_repository_reuses_cached_rol() -> None:
    repository = FinancialRepository()
    request = GetRolRequest(
        branch="01",
        start_date="2026-01-01",
        end_date="2026-01-31",
    )
    payload = {
        "branch": "01",
        "rol_with_ipi": 123.45,
    }

    with patch.object(FinancialRepository, "_load_rol", return_value=payload) as loader:
        first = repository.get_rol(request)
        second = repository.get_rol(request)

    assert first == payload
    assert second == payload
    loader.assert_called_once()


def test_commercial_rol_series_use_case_caches_full_response() -> None:
    repository = MagicMock()
    repository.get_rol.return_value = {"rol_with_ipi": 100.0}

    use_case = GetCommercialRolSeriesUseCase(repository)
    request = CommercialRolSeriesRequest(
        granularity="month",
        date_start="2026-05-01",
        date_end="2026-05-31",
    )

    first = use_case.execute(request)
    second = use_case.execute(request)

    assert first.points
    assert second.points[0].rol_matrix == first.points[0].rol_matrix
    assert repository.get_rol.call_count == 2

    cache_key = commercial_rol_series_cache_key(request)
    assert build_query_cache().get(cache_key) is not None


def test_production_oee_series_use_case_caches_full_response() -> None:
    repository = MagicMock()
    repository.list_oee_kpi_by_day_and_branch.return_value = [
        {
            "production_date": "2026-05-15",
            "branch": "01",
            "oee_pct": 88.5,
            "appointment_count": 5,
        },
        {
            "production_date": "2026-05-15",
            "branch": "02",
            "oee_pct": 88.5,
            "appointment_count": 5,
        },
    ]

    use_case = GetProductionOeeSeriesUseCase(repository)
    request = ProductionOeeSeriesRequest(
        granularity="month",
        date_start="2026-05-01",
        date_end="2026-05-31",
    )

    first = use_case.execute(request)
    second = use_case.execute(request)

    assert first.points[0].oee_filial_01 == 88.5
    assert second.points[0].oee_filial_01 == 88.5
    assert repository.list_oee_kpi_by_day_and_branch.call_count == 1

    cache_key = production_oee_series_cache_key(request)
    assert build_query_cache().get(cache_key) is not None


def test_production_oee_repository_reuses_cached_kpi() -> None:
    from app.infrastructure.persistence.totvs.production_repositories.overall_equipment_effectiveness_repository import (
        OverallEquipmentEffectivenessRepository,
    )

    repository = OverallEquipmentEffectivenessRepository()
    request = ProductionRequest(
        branch="01",
        start_date="2026-05-01",
        end_date="2026-05-31",
    )
    entity = OverallEquipmentEffectiveness(
        branch="01",
        start_date="2026-05-01",
        end_date="2026-05-31",
        oee_pct=75.0,
    )

    with patch.object(
        OverallEquipmentEffectivenessRepository,
        "_load_overall_equipment_effectiveness",
        return_value=entity,
    ) as loader:
        first = repository.get_overall_equipment_effectiveness(request)
        second = repository.get_overall_equipment_effectiveness(request)

    assert first.oee_pct == 75.0
    assert second.oee_pct == 75.0
    loader.assert_called_once()


def test_production_oee_single_branch_reuses_grouped_by_branch_loader() -> None:
    from app.infrastructure.persistence.totvs.production_repositories.overall_equipment_effectiveness_repository import (
        OverallEquipmentEffectivenessRepository,
    )

    repository = OverallEquipmentEffectivenessRepository()
    request = ProductionRequest(
        branch="02",
        start_date="2026-05-01",
        end_date="2026-05-31",
    )
    rows = [
        {"branch": "01", "oee_pct": 80.0},
        {"branch": "02", "oee_pct": 91.5},
    ]

    with patch.object(
        OverallEquipmentEffectivenessRepository,
        "_load_overall_equipment_effectiveness_by_branch",
        return_value=rows,
    ) as loader:
        result = repository._load_overall_equipment_effectiveness(request)

    assert result.oee_pct == 91.5
    assert loader.call_count == 1
    consolidated_request = loader.call_args.args[0]
    assert consolidated_request.branch is None


def test_production_oee_by_branch_list_is_cached() -> None:
    from app.application.services.production.production_kpi_cache import (
        production_oee_by_branch_cache_key,
    )
    from app.infrastructure.persistence.totvs.production_repositories.overall_equipment_effectiveness_repository import (
        OverallEquipmentEffectivenessRepository,
    )

    repository = OverallEquipmentEffectivenessRepository()
    request = ProductionRequest(
        branch=None,
        start_date="2026-05-01",
        end_date="2026-05-31",
    )
    rows = [{"branch": "01", "oee_pct": 88.0}]

    with patch.object(
        OverallEquipmentEffectivenessRepository,
        "_load_overall_equipment_effectiveness_by_branch",
        return_value=rows,
    ) as loader:
        first = repository.list_overall_equipment_effectiveness_by_branch(request)
        second = repository.list_overall_equipment_effectiveness_by_branch(request)

    assert first == rows
    assert second == rows
    loader.assert_called_once()

    cache_key = production_oee_by_branch_cache_key(request)
    assert build_query_cache().get(cache_key) == rows
