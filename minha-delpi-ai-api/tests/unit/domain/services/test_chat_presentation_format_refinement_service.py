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


def test_resolve_payload_from_table_presentations_list_role():
    rows = [
        {"branch": "01", "warehouse": "01", "current_quantity": 10},
        {"branch": "02", "warehouse": "01", "current_quantity": 5},
    ]
    operation = {
        "actionId": "stock-action",
        "path": "/products/10080001/stock",
        "metadata": {
            "preferredFormat": "text",
            "presentation": None,
            "tablePresentations": [
                {
                    "type": "table",
                    "role": "list",
                    "title": "Estoque",
                    "columns": [{"key": "branch", "label": "Filial"}],
                    "rows": rows,
                }
            ],
        },
    }

    payload = ChatPresentationFormatRefinementService.resolve_payload(
        [],
        operation=operation,
    )

    assert payload == {
        "data": {
            "stock": {
                "items": rows,
                "total": 2,
                "page": 1,
                "page_size": 2,
                "total_pages": 1,
            }
        }
    }


def test_wrap_payload_for_non_stock_keeps_flat_items():
    operation = {"path": "/products/90260149/analyser"}
    root = {"items": [{"op": "01"}], "total": 1, "page": 1, "page_size": 1, "total_pages": 1}

    payload = ChatPresentationFormatRefinementService.wrap_payload_for_operation(
        operation,
        root,
    )

    assert payload == {"data": root}


_PRODUCTION_SQL_ROWS = [
    {
        "COD_PRODUTO": "90264130",
        "DESCRICAO_PRODUTO": "PARAFUSO M8",
        "QTD_PLANEJADA": 1200,
        "UNIDADE": "UN",
        "DATA_INICIO_OPERACAO": "20260610",
    },
    {
        "COD_PRODUTO": "10080047",
        "DESCRICAO_PRODUTO": "TERMINAL PINO",
        "QTD_PLANEJADA": 500,
        "UNIDADE": "UN",
        "DATA_INICIO_OPERACAO": "20260610",
    },
]


def test_wrap_payload_for_sql_maps_table_items_to_rows():
    operation = {
        "actionId": "api_delpi.data.execute_readonly_sql",
        "path": "/data/sql",
        "metadata": {
            "sensitivity": "sql",
            "operationId": "execute_readonly_sql",
        },
    }
    root = {
        "items": _PRODUCTION_SQL_ROWS,
        "total": len(_PRODUCTION_SQL_ROWS),
        "page": 1,
        "page_size": len(_PRODUCTION_SQL_ROWS),
        "total_pages": 1,
    }

    payload = ChatPresentationFormatRefinementService.wrap_payload_for_operation(
        operation,
        root,
    )

    assert payload == {
        "data": {
            "rows": _PRODUCTION_SQL_ROWS,
            "total": len(_PRODUCTION_SQL_ROWS),
        }
    }


def test_rebuild_metadata_sql_format_refinement_does_not_crash():
    from app.application.use_cases.execute_external_action_use_case import (
        ExecuteExternalActionUseCase,
    )
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    operation = {
        "actionId": "api_delpi.data.execute_readonly_sql",
        "path": "/data/sql",
        "parameters": {},
        "metadata": {
            "ok": True,
            "path": "/data/sql",
            "sensitivity": "sql",
            "operationId": "execute_readonly_sql",
            "actionId": "api_delpi.data.execute_readonly_sql",
        },
    }
    payload = ChatPresentationFormatRefinementService.wrap_payload_for_operation(
        operation,
        {
            "items": _PRODUCTION_SQL_ROWS,
            "total": len(_PRODUCTION_SQL_ROWS),
            "page": 1,
            "page_size": len(_PRODUCTION_SQL_ROWS),
            "total_pages": 1,
        },
    )

    presenter = ExternalActionResultPresenter()
    humanized = presenter.present(payload, path="/data/sql")

    assert humanized["linhas"]
    assert humanized.get("sqlRows") == _PRODUCTION_SQL_ROWS

    use_case = ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )

    class _SqlRefinementUseCase:
        def build_metadata_for_data(self, *, action_id, data, parameters=None):
            return use_case._build_presentation_metadata(
                action={
                    "path": "/data/sql",
                    "actionId": action_id,
                    "sensitivity": "sql",
                    "operationId": "execute_readonly_sql",
                },
                sanitized_data=data,
                resolved_path="/data/sql",
                request_parameters=dict(parameters or {}),
            )

    rebuilt = ChatPresentationFormatRefinementService.rebuild_metadata_for_refinement(
        external_use_case=_SqlRefinementUseCase(),
        operation=operation,
        payload=payload,
        requested_format="table",
        user_message="mostre o último resultado em tabela",
    )

    assert rebuilt is not None
    assert rebuilt.get("preferredFormat") == "table"
    assert rebuilt.get("presentation", {}).get("type") == "table"
    assert rebuilt.get("presentation", {}).get("rows") == _PRODUCTION_SQL_ROWS
