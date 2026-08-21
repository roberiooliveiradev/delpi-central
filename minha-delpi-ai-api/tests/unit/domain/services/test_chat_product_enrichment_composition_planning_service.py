from app.domain.services.chat_product_enrichment_composition_planning_service import (
    ChatProductEnrichmentCompositionPlanningService,
)


class FakeSelectionService:
    def select_registry_route_id(
        self,
        route_id,
        message,
        *,
        allowed_action_ids=None,
        previous_messages=None,
    ):
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": f"action-{route_id}",
                "parameters": {"code": "90260148"},
                "routeId": route_id,
            },
        }

    def select_action_for_product(self, *args, **kwargs):
        intent = kwargs.get("intent")
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": f"action-{intent}",
                "parameters": {"code": "90260148"},
            },
        }


def test_looks_like_product_overview_triggers():
    assert ChatProductEnrichmentCompositionPlanningService.looks_like_product_overview(
        "me fale do produto 90260148"
    )
    assert ChatProductEnrichmentCompositionPlanningService.looks_like_product_overview(
        "situação do 90260148"
    )
    assert not ChatProductEnrichmentCompositionPlanningService.looks_like_product_overview(
        "estoque do produto 90260148"
    )
    assert not ChatProductEnrichmentCompositionPlanningService.looks_like_product_overview(
        "só estoque do 90260148"
    )


def test_plan_overview_returns_multi_route():
    planned = ChatProductEnrichmentCompositionPlanningService.plan(
        FakeSelectionService(),
        message="me fale do produto 90260148",
        product_code="90260148",
        allowed_action_ids=["a", "b", "c"],
        max_calls=4,
    )

    assert len(planned) >= 2
    scopes = [item.get("enrichmentScope") for item in planned]
    assert "productStock" in scopes or "productSummary" in scopes


def test_plan_analyser_phrase_returns_single_analyser():
    planned = ChatProductEnrichmentCompositionPlanningService.plan(
        FakeSelectionService(),
        message="análise completa do produto 90260148",
        product_code="90260148",
        allowed_action_ids=["analyser"],
        max_calls=4,
    )

    assert len(planned) == 1
