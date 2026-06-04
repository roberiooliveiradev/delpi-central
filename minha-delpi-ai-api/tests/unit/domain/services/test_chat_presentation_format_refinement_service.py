"""Reapresentação do último resultado (tabela/gráfico) sem rota /system/tables."""

from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_presentation_format_refinement_service import (
    ChatPresentationFormatRefinementService,
)

_STOCK_HISTORY = [
    {"role": "user", "content": "estoque do produto 10080077"},
    {
        "role": "assistant",
        "content": "Estoque do produto",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": "stock-action",
                        "parameters": {"productCode": "10080077"},
                    },
                    "metadata": {
                        "ok": True,
                        "path": "/products/10080077/stock",
                        "actionId": "stock-action",
                        "preferredFormat": "text",
                        "availableFormats": ["text", "table", "chart"],
                        "tablePresentation": {
                            "type": "table",
                            "title": "Estoque",
                            "columns": [{"key": "branch", "label": "Filial"}],
                            "rows": [{"branch": "01"}],
                        },
                    },
                }
            ]
        },
    },
]


def test_looks_like_format_refinement_with_reference_and_table():
    assert ChatPresentationFormatRefinementService.looks_like_format_refinement(
        "mostre os dados acima em tabela",
    )


def test_looks_like_format_refinement_with_last_result_phrase():
    assert ChatPresentationFormatRefinementService.looks_like_format_refinement(
        "mostre o último resultado em tabela",
    )


def test_looks_like_format_refinement_with_same_data_phrase():
    assert ChatPresentationFormatRefinementService.looks_like_format_refinement(
        "mostre os mesmos dados em tabela",
    )


def test_looks_like_format_refinement_coloque_em_uma_tabela():
    assert ChatPresentationFormatRefinementService.looks_like_format_refinement(
        "coloque em uma tabela",
    )


def test_intent_router_skips_presentation_task_for_coloque_em_tabela():
    result = ChatIntentRouterService.classify("coloque em uma tabela")

    assert result.intent != "presentation_task"


def test_collect_last_successful_operation_skips_system_tables():
    history = _STOCK_HISTORY + [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/system/tables/foo",
                            "actionId": "tables-action",
                        },
                    }
                ]
            },
        }
    ]

    op = ChatPresentationFormatRefinementService.collect_last_successful_operation(
        history,
    )

    assert op is not None
    assert op["actionId"] == "stock-action"
    assert "/stock" in op["path"]


def test_intent_router_skips_presentation_task_for_format_refinement():
    result = ChatIntentRouterService.classify("mostre os dados acima em tabela")

    assert result.intent != "presentation_task"


def test_looks_like_format_refinement_tree_and_chart():
    assert ChatPresentationFormatRefinementService.looks_like_format_refinement(
        "mostre em árvore",
    )
    assert ChatPresentationFormatRefinementService.looks_like_format_refinement(
        "coloque em gráfico",
    )
    assert (
        ChatPresentationFormatRefinementService.detect_requested_format(
            "exiba em gráfico"
        )
        == "chart"
    )
    assert (
        ChatPresentationFormatRefinementService.detect_requested_format(
            "mostre em árvore"
        )
        == "tree"
    )


_ANALYSER_HISTORY = [
    {"role": "user", "content": "me fale do produto 90260149"},
    {
        "role": "assistant",
        "content": "Produto consultado",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": "analyser-action",
                        "parameters": {"code": "90260149"},
                    },
                    "metadata": {
                        "ok": True,
                        "path": "/products/90260149/analyser",
                        "actionId": "analyser-action",
                        "preferredFormat": "tree",
                        "presentation": {
                            "type": "tree",
                            "title": "Estrutura",
                            "root": {"id": "90260149", "label": "90260149", "children": []},
                        },
                        "tablePresentations": [
                            {
                                "type": "table",
                                "title": "Roteiro",
                                "columns": [{"key": "op", "label": "Op."}],
                                "rows": [{"op": "01"}],
                            }
                        ],
                        "textPresentation": {
                            "type": "markdown",
                            "markdown": "**Destaques**\n\n- Item.",
                        },
                    },
                }
            ]
        },
    },
]


def test_collect_last_operation_after_analyser_skips_system_tables():
    history = _ANALYSER_HISTORY + [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/system/tables/SA1",
                            "actionId": "tables-action",
                        },
                    }
                ]
            },
        }
    ]

    op = ChatPresentationFormatRefinementService.collect_last_successful_operation(
        history,
    )

    assert op is not None
    assert op["actionId"] == "analyser-action"
    assert "/analyser" in op["path"]
