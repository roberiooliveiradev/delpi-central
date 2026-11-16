from unittest.mock import Mock

import pytest

from app.application.use_cases.supplies.get_supplier_performance_use_case import (
    GetSupplierPerformanceUseCase,
)
from app.domain.services.supplies.supplier_performance import (
    compose_supplier_performance,
)
from app.infrastructure.cache.memory_query_cache import MemoryQueryCache
from app.interface.http.schemas.supplier_performance_schema import (
    SupplierPerformancePayload,
)


def fact(source, total, positive, *, code="000001", store="01", branch="01", **extra):
    return dict(
        source=source,
        branch=branch,
        supplier_code=code,
        supplier_store=store,
        supplier_name="Fornecedor de teste",
        assessed_count=total,
        positive_count=positive,
        **extra
    )


def test_approved_weights_equal_scale_and_explicit_counts():
    result = compose_supplier_performance(
        [
            fact("quality", 10, 8, conditional_count=2, urgent_count=1),
            fact("delivery", 10, 6),
        ]
    )
    item = result["items"][0]
    assert item["idf"] == 74
    assert item["quality_contribution"] == 56
    assert item["delivery_contribution"] == 18
    assert item["quality"]["negative_count"] == 2
    assert item["quality"]["conditional_count"] == 2
    assert item["quality"]["urgent_count"] == 1
    assert result["methodology"]["classification_bands"] is None


def test_branches_sum_counts_before_ratios_and_supplier_stores_stay_separate():
    result = compose_supplier_performance(
        [
            fact("quality", 1, 0),
            fact("quality", 9, 9, branch="02"),
            fact("delivery", 1, 1),
            fact("quality", 1, 0, store="02"),
            fact("delivery", 1, 0, store="02"),
        ]
    )
    assert len(result["items"]) == 2
    item = result["items"][0]
    assert item["quality"]["index"] == 90  # not mean(0,100)=50
    assert item["idf"] == 93
    assert item["branches"] == ["01", "02"]
    assert result["items"][1]["idf"] == 0  # zero is a valid score
    assert result["summary"]["average_idf"] == 46.5  # equal supplier weights


@pytest.mark.parametrize(
    "rows,status",
    [
        ([fact("quality", 1, 1)], "missing_delivery"),
        ([fact("delivery", 1, 1)], "missing_quality"),
        (
            [fact("quality", 2, 2, unknown_count=1), fact("delivery", 1, 1)],
            "inconsistent",
        ),
        (
            [fact("quality", 1, 1), fact("delivery", 2, 1, unknown_count=1)],
            "inconsistent",
        ),
    ],
)
def test_missing_or_inconsistent_evidence_is_never_assumed_100(rows, status):
    result = compose_supplier_performance(rows)
    assert result["items"][0]["idf"] is None
    assert result["items"][0]["status"] == status
    assert result["summary"]["evaluated"] == 0
    assert result["summary"]["average_idf"] is None
    assert result["summary"]["incomplete"] == 1


def test_exact_ratios_round_once_and_incomplete_not_in_mean():
    result = compose_supplier_performance(
        [
            fact("quality", 3, 1),
            fact("delivery", 6, 1),
            fact("delivery", 1, 1, code="000002"),
        ]
    )
    assert result["items"][0]["idf"] == 28.33
    assert result["summary"]["average_idf"] == 28.33
    assert result["summary"]["suppliers"] == 2


def test_empty_result_and_wire_schema_are_complete():
    result = compose_supplier_performance([])
    assert result["items"] == []
    assert result["summary"]["average_idf"] is None
    result.update(
        period={"from": "2026-11-01", "to": "2026-11-16"},
        branches=["01"],
        calculated_at="2026-11-16T08:00:00-03:00",
    )
    SupplierPerformancePayload.model_validate(result)
    result["items"] = compose_supplier_performance([fact("quality", 1, 1)])["items"]
    validated = SupplierPerformancePayload.model_validate(result)
    assert validated.items[0].delivery.assessed_count == 0


@pytest.mark.parametrize(
    "row",
    [
        fact("quality", 1, 2),
        fact("quality", -1, 0),
        fact("oops", 1, 1),
        fact("quality", 1, 1, code=""),
    ],
)
def test_invalid_source_fails_instead_of_producing_plausible_score(row):
    with pytest.raises(ValueError):
        compose_supplier_performance([row])


@pytest.mark.parametrize(
    "branches,start,end",
    [
        ([], "2026-01-01", "2026-02-01"),
        (["03"], "2026-01-01", "2026-02-01"),
        (["01"], "20261101", "2026-11-16"),
        (["01"], "2026-02-30", "2026-03-01"),
        (["01"], "2026-11-16", "2026-11-01"),
        (["01"], "2024-01-01", "2026-01-01"),
        (["01"], None, None),
    ],
)
def test_filters_fail_closed_before_repository(branches, start, end):
    repository = Mock()
    case = GetSupplierPerformanceUseCase(repository, MemoryQueryCache(ttl_seconds=300))
    with pytest.raises(ValueError):
        case.execute(branches=branches, date_from=start, date_to=end)
    repository.read_counts.assert_not_called()


def test_cache_normalizes_branch_order_and_scopes_period():
    repository = Mock()
    repository.read_counts.return_value = [
        fact("quality", 1, 1),
        fact("delivery", 1, 1),
    ]
    case = GetSupplierPerformanceUseCase(repository, MemoryQueryCache(ttl_seconds=300))
    first = case.execute(
        branches=["02", "01", "01"], date_from="2026-11-01", date_to="2026-11-16"
    )
    again = case.execute(
        branches=["01", "02"], date_from="2026-11-01", date_to="2026-11-16"
    )
    assert first == again
    assert repository.read_counts.call_count == 1
    case.execute(branches=["01"], date_from="2026-11-01", date_to="2026-11-16")
    assert repository.read_counts.call_count == 2


def test_source_failure_is_not_cached_as_success():
    repository = Mock()
    repository.read_counts.side_effect = [RuntimeError("database down"), []]
    case = GetSupplierPerformanceUseCase(repository, MemoryQueryCache(ttl_seconds=300))
    with pytest.raises(RuntimeError):
        case.execute(branches=["01"], date_from="2026-11-01", date_to="2026-11-16")
    assert (
        case.execute(branches=["01"], date_from="2026-11-01", date_to="2026-11-16")[
            "items"
        ]
        == []
    )
