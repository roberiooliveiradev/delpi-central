"""Testes de resolução de produto por descrição (drill-down / estrutura)."""

from app.domain.services.chat_product_description_resolution_service import (
    ChatProductDescriptionResolutionService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


def test_extract_description_query_from_mais_informacoes():
    query = ChatProductDescriptionResolutionService.extract_description_query(
        "Mais informações sobre TERM. FASTON 6,30X0,80 1,00-2,60MM2 NU S/ISOLACAO FITADO UL - ROHS",
    )

    assert query is not None
    assert "term" in query.lower()
    assert "faston" in query.lower()


def test_extract_code_from_drilldown_message():
    code = ChatProductDescriptionResolutionService.extract_code_from_drilldown_message(
        "Detalhe do item 10080109 (TERM. FASTON 6,30X0,80 0,30-0,80MM2 NU S/ISOLACAO FITADO UL ROHS)",
    )

    assert code == "10080109"


def test_resolve_code_from_structure_tree_history():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260143/structure",
                            "presentation": {
                                "type": "tree",
                                "title": "Estrutura do produto 90260143",
                                "root": {
                                    "id": "90260143",
                                    "label": "90260143",
                                    "subtitle": "CHICOTE EPR SINGELO 315MM",
                                    "children": [
                                        {
                                            "id": "10080109",
                                            "label": "10080109",
                                            "subtitle": "TERM. FASTON 6,30X0,80 0,30-0,80MM2 NU S/ISOLACAO FITADO UL ROHS",
                                        },
                                        {
                                            "id": "50230216",
                                            "label": "50230216",
                                            "subtitle": "CB18AZUL-00305/06/10-6314-0000",
                                            "children": [
                                                {
                                                    "id": "10380012",
                                                    "label": "10380012",
                                                    "subtitle": "CABO EPR 125/150°C 20AWG VM 600V STYLE 3400 CSA NBR 9114 - UL",
                                                }
                                            ],
                                        },
                                    ],
                                },
                            },
                        },
                    }
                ]
            },
        }
    ]

    code = ChatProductDescriptionResolutionService.resolve_code_from_history(
        "TERM. FASTON 6,30X0,80 1,00-2,60MM2 NU S/ISOLACAO FITADO UL - ROHS",
        previous_messages=history,
    )

    assert code == "10080109"


def test_extract_product_code_ignores_dimension_tokens():
    assert (
        ChatProductQueryIntentService.extract_product_code(
            "Mais informações sobre TERM. FASTON 6,30X0,80 1,00-2,60MM2 NU S/ISOLACAO FITADO UL - ROHS",
        )
        is None
    )


def test_resolve_product_code_uses_structure_description():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260143/structure",
                            "treePresentation": {
                                "type": "tree",
                                "root": {
                                    "id": "10080109",
                                    "label": "10080109",
                                    "subtitle": "TERM. FASTON 6,30X0,80 0,30-0,80MM2 NU S/ISOLACAO FITADO UL ROHS",
                                },
                            },
                        },
                    }
                ]
            },
        }
    ]

    code = ChatProductQueryIntentService.resolve_product_code(
        "Mais informações sobre TERM. FASTON 6,30X0,80 1,00-2,60MM2 NU S/ISOLACAO FITADO UL - ROHS",
        previous_messages=history,
    )

    assert code == "10080109"


def test_resolve_product_intent_for_description_lookup_is_full():
    intent = ChatProductQueryIntentService.resolve_product_intent(
        "Mais informações sobre TERM. FASTON 6,30X0,80 1,00-2,60MM2",
    )

    assert intent == ChatProductQueryIntent.FULL
