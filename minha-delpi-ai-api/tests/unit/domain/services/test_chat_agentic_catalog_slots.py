from app.domain.services.chat_agentic_catalog_service import ChatAgenticCatalogService
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def _drawing_action():
    return {
        "actionId": "api_delpi.products.get_product_drawing",
        "path": "/products/{code}/drawing",
        "operationId": "get_product_drawing",
        "summary": "Desenho do produto",
        "method": "GET",
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True},
        ],
    }


class FakeRepository:
    def find_candidate_actions(self, message, limit=12, allowed_action_ids=None):
        return [_drawing_action()]


def test_slim_catalog_injects_operational_focus_code():
    slim = ChatAgenticCatalogService.build_slim_catalog(
        "buscar desenho",
        ["api_delpi.products.get_product_drawing"],
        FakeRepository(),
        memory_snapshot={"operationalFocus": {"productCode": "90261899"}},
    )

    assert slim
    assert slim[0]["exampleArguments"]["code"] == "90261899"
    assert slim[0]["operationalFocusProductCode"] == "90261899"


def test_slim_catalog_hides_action_when_code_not_groundable():
    slim = ChatAgenticCatalogService.build_slim_catalog(
        "buscar desenho sem codigo",
        ["api_delpi.products.get_product_drawing"],
        FakeRepository(),
        memory_snapshot={},
    )

    assert slim == []


def test_slim_catalog_excludes_invalid_action_ids():
    slim = ChatAgenticCatalogService.build_slim_catalog(
        "buscar desenho",
        ["api_delpi.products.get_product_drawing"],
        FakeRepository(),
        memory_snapshot={"operationalFocus": {"productCode": "90261899"}},
        exclude_action_ids={"api_delpi.products.get_product_drawing"},
    )

    assert slim == []


def test_agentic_planner_content_from_json():
    assert "productCode" in ChatAssistantContentService.get(
        "agentic_planner",
        "planner",
        "systemOperationalFocus",
    )
    assert "missing_required_parameter" in ChatAssistantContentService.get(
        "agentic_planner",
        "planner",
        "systemFailures",
    )


def test_is_validation_slot_failure_helper():
    from app.application.services.chat_agentic_tool_loop_service import (
        ChatAgenticToolLoopService,
    )

    assert ChatAgenticToolLoopService._is_validation_slot_failure(
        {"errorKind": "missing_required_parameter"}
    )
    assert not ChatAgenticToolLoopService._is_validation_slot_failure(
        {"errorKind": "api_unavailable"}
    )
