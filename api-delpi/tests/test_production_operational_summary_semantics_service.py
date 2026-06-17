from app.domain.services.production.production_operational_summary_semantics_service import (
    ProductionOperationalSummarySemanticsService,
)


def test_consolidated_for_ranking_general_without_branch() -> None:
    assert ProductionOperationalSummarySemanticsService.consolidated_for_ranking(
        branch=None,
        group_by="general",
    )


def test_consolidated_for_ranking_false_with_branch() -> None:
    assert (
        ProductionOperationalSummarySemanticsService.consolidated_for_ranking(
            branch="01",
            group_by="general",
        )
        is False
    )


def test_consolidated_for_ranking_false_when_group_by_branch() -> None:
    assert (
        ProductionOperationalSummarySemanticsService.consolidated_for_ranking(
            branch=None,
            group_by="branch",
        )
        is False
    )


def test_consolidated_for_ranking_true_when_group_by_product_group() -> None:
    assert ProductionOperationalSummarySemanticsService.consolidated_for_ranking(
        branch=None,
        group_by="product_group",
    )


def test_consolidated_for_ranking_true_when_group_by_unit() -> None:
    assert ProductionOperationalSummarySemanticsService.consolidated_for_ranking(
        branch=None,
        group_by="unit",
    )


def test_consolidated_for_ranking_false_when_group_by_branch_summary() -> None:
    assert (
        ProductionOperationalSummarySemanticsService.consolidated_for_ranking(
            branch=None,
            group_by="branch_summary",
        )
        is False
    )


def test_consolidated_for_product_aggregation_without_branch() -> None:
    assert ProductionOperationalSummarySemanticsService.consolidated_for_product_aggregation(
        branch=None,
    )


def test_consolidated_for_product_aggregation_with_branch() -> None:
    assert (
        ProductionOperationalSummarySemanticsService.consolidated_for_product_aggregation(
            branch="01",
        )
        is False
    )
