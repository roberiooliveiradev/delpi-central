from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.domain.services.chat_capabilities_catalog_answer_service import (
    ChatCapabilitiesCatalogAnswerService,
)
from app.domain.services.chat_capabilities_detection_service import (
    ChatCapabilitiesDetectionService,
)


def test_is_api_action_routes_inquiry_matches_chat_routes_question():
    assert ChatCapabilitiesDetectionService.is_api_action_routes_inquiry(
        "quais rotas vc acessa?"
    )


def test_is_api_action_routes_inquiry_prefers_portal_menus_terms():
    assert not ChatCapabilitiesDetectionService.is_api_action_routes_inquiry(
        "quais menus do portal estão autorizados?"
    )


def test_build_action_routes_answer_lists_openapi_paths():
    catalog = [
        {
            "actionId": "api_delpi.products.get_product_parents",
            "method": "GET",
            "path": "/products/{code}/parents",
            "summary": "Onde o produto é usado",
        },
        {
            "actionId": "api_delpi.products.get_stock",
            "method": "GET",
            "path": "/products/{code}/stock",
            "summary": "Estoque do produto",
        },
    ]

    answer = ChatCapabilitiesCatalogAnswerService.build_action_routes_answer(
        workspace_context={"agent": {"name": "Agente Minha DELPI"}},
        allowed_action_ids=[
            "api_delpi.products.get_product_parents",
            "api_delpi.products.get_stock",
        ],
        action_catalog=catalog,
    )

    assert answer is not None
    assert "Rotas das actions" in answer
    assert "GET /products/{code}/parents" in answer
    assert "GET /products/{code}/stock" in answer
    assert answer.count("/apps/") <= 1


def test_resolve_capability_answer_uses_action_routes_for_routes_question():
    answer = ChatCapabilitiesService.resolve_capability_answer(
        message="quais rotas vc acessa?",
        workspace_context={"agent": {"name": "Agente Minha DELPI"}},
        allowed_action_ids=["api_delpi.products.get_product_parents"],
        action_catalog=[
            {
                "actionId": "api_delpi.products.get_product_parents",
                "method": "GET",
                "path": "/products/{code}/parents",
                "summary": "Onde o produto é usado",
            }
        ],
    )

    assert answer is not None
    assert "GET /products/{code}/parents" in answer
    assert ChatCapabilitiesService.is_api_action_routes_inquiry("quais rotas vc acessa?")
