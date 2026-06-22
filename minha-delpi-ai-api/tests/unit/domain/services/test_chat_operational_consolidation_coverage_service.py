from app.domain.services.chat_operational_consolidation_coverage_service import (
    ChatOperationalConsolidationCoverageService,
)


def test_schedule_today_is_listing_entity() -> None:
    assert ChatOperationalConsolidationCoverageService.is_listing_entity(
        "production_schedule_today"
    )


def test_consumption_top_items_is_not_listing_entity() -> None:
    assert not ChatOperationalConsolidationCoverageService.is_listing_entity(
        "production_consumption_top_items"
    )


def test_listing_complete_should_not_emit_banner() -> None:
    assert not ChatOperationalConsolidationCoverageService.should_emit_complete_consolidation_notice(
        "production_schedule_today"
    )


def test_aggregated_complete_should_emit_banner() -> None:
    assert ChatOperationalConsolidationCoverageService.should_emit_complete_consolidation_notice(
        "production_consumption_top_items"
    )


def test_coverage_message_key_for_listing_incomplete() -> None:
    key = ChatOperationalConsolidationCoverageService.coverage_message_key(
        entity="production_schedule_today",
        incomplete=True,
    )

    assert key == "operationalIncompleteListingAllBranches"


def test_resolve_entity_from_response_meta() -> None:
    entity = ChatOperationalConsolidationCoverageService.resolve_entity(
        response_meta={"entity": "production_schedule_today"},
        path="/production/schedule/today",
    )

    assert entity == "production_schedule_today"
