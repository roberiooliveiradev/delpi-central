from app.application.services.chat_interactivity_query_resolver import (
    ChatInteractivityQueryResolver,
)


def test_resolve_product_code_from_snapshot():
    query = ChatInteractivityQueryResolver.resolve(
        "Qual o estoque do produto {{productCode}}?",
        metadata={
            "contextSnapshot": {"lastEntities": {"productCode": "10080001"}},
        },
    )

    assert query == "Qual o estoque do produto 10080001?"


def test_resolve_keeps_placeholder_when_unknown():
    query = ChatInteractivityQueryResolver.resolve(
        "Busque {{searchQuery}}",
        metadata={},
    )

    assert query == "Busque {{searchQuery}}"


def test_resolve_search_query_from_web_research_metadata():
    query = ChatInteractivityQueryResolver.resolve(
        "Refaça a busca: {{searchQuery}}",
        metadata={"webSearchResearch": {"query": "IP67 norma ABNT"}},
    )

    assert query == "Refaça a busca: IP67 norma ABNT"
