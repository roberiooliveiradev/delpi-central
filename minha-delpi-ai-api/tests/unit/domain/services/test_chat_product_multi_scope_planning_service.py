from app.domain.services.chat_product_multi_scope_planning_service import (
    ChatProductMultiScopePlanningService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


class FakeScopeSelectionService:
    def select_action_for_product(
        self,
        message,
        *,
        product_code,
        allowed_action_ids=None,
        intent=None,
        route_segment=None,
        previous_messages=None,
    ):
        path = "/products/{code}/analyser"

        if intent == ChatProductQueryIntent.STRUCTURE:
            path = "/products/{code}/structure"
        elif route_segment == "guide":
            path = "/products/{code}/guide"
        elif route_segment == "inspection":
            path = "/products/{code}/inspection"
        elif intent == ChatProductQueryIntent.DESCRIPTION:
            path = "/products/{code}"
        elif intent == ChatProductQueryIntent.STOCK:
            path = "/products/{code}/stock"

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": f"action-{path}",
                "parameters": {"code": product_code},
                "path": path,
            },
        }


def test_extract_scopes_structure_and_guide():
    scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(
        "mostre estrutura e roteiro do produto 90260149",
    )

    assert scopes == ("guide", "structure")


def test_should_use_single_analyser_for_explicit_completa():
    scopes = ("guide", "structure")

    assert ChatProductMultiScopePlanningService.should_use_single_analyser(
        scopes,
        "informações completas do produto 90260149",
    )


def test_should_use_single_analyser_for_three_analyser_scopes():
    scopes = ("profile", "guide", "structure")

    assert ChatProductMultiScopePlanningService.should_use_single_analyser(
        scopes,
        "cadastro roteiro e estrutura do 90260149",
    )


def test_should_not_use_single_analyser_for_two_scopes_without_completa():
    scopes = ("guide", "structure")

    assert not ChatProductMultiScopePlanningService.should_use_single_analyser(
        scopes,
        "estrutura e roteiro do produto 90260149",
    )


def test_detect_multi_scope_intent():
    intent = ChatProductQueryIntentService.detect(
        "estrutura e roteiro do produto 90260149",
    )

    assert intent == ChatProductQueryIntent.MULTI_SCOPE


def test_detect_analyser_for_integrated_three_scopes():
    intent = ChatProductQueryIntentService.detect(
        "análise integrada do cadastro, roteiro e estrutura do 90260149",
    )

    assert intent == ChatProductQueryIntent.ANALYSER


def test_plan_fetches_two_routes():
    service = FakeScopeSelectionService()

    planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
        service,
        message="estrutura e roteiro do produto 90260149",
        product_code="90260149",
        allowed_action_ids=["a1"],
    )

    assert len(planned) == 2
    paths = {
        str(item["arguments"].get("path") or "")
        for item in planned
    }

    assert "/products/{code}/structure" in paths
    assert "/products/{code}/guide" in paths


def test_plan_fetches_single_analyser_when_completa():
    service = FakeScopeSelectionService()

    planned = ChatProductMultiScopePlanningService.plan_product_scope_fetches(
        service,
        message="informações completas do produto 90260149",
        product_code="90260149",
        allowed_action_ids=["a1"],
    )

    assert len(planned) == 1
    assert "/analyser" in str(planned[0]["arguments"].get("path") or "")
