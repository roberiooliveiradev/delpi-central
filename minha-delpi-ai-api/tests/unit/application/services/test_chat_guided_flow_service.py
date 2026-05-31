from app.application.services.chat_guided_flow_service import ChatGuidedFlowService


def test_build_flow_stock():
    flow = ChatGuidedFlowService.build_flow("stock")

    assert flow is not None
    assert flow["id"] == "stock"
    assert len(flow["steps"]) >= 2


def test_build_for_message_como_consultar_estoque():
    flow = ChatGuidedFlowService.build_for_message("como consultar estoque de um produto?")

    assert flow is not None
    assert flow["id"] == "stock"


def test_attach_capability_cards():
    metadata: dict = {}

    ChatGuidedFlowService.attach_to_assistant_metadata(
        metadata,
        message="o que você pode fazer?",
    )

    assert metadata.get("guidedFlowCards")
    assert len(metadata["guidedFlowCards"]) >= 3


def test_attach_guided_flow_suggestions():
    metadata: dict = {}

    ChatGuidedFlowService.attach_to_assistant_metadata(
        metadata,
        message="me guie na pesquisa na web",
    )

    assert metadata.get("guidedFlow", {}).get("id") == "web"
    assert metadata.get("guidedFlowSuggestions")
