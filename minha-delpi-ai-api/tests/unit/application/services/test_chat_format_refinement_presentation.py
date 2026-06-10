"""Refinamento de formato — tabela, árvore e gráfico sem reconsultar API."""

from dataclasses import dataclass

from app.application.services.chat_tool_context_service import ChatToolContextService
from app.domain.entities.tool_result import ToolResult
from app.domain.services.tool_selection_service import ToolSelectionService


@dataclass
class FakeExecuteToolRequest:
    user_id: str
    access_token: str
    tool_name: str
    arguments: dict


class NoReexecuteToolUseCase:
    def __init__(self):
        self.calls = 0

    def execute(self, request):
        self.calls += 1
        raise AssertionError("refinamento não deve reexecutar tool")


class BlockSystemTablesSelection:
    def select_action(self, *args, **kwargs):
        return {
            "name": "execute_external_action",
            "arguments": {"actionId": "system-tables", "parameters": {}},
            "reason": "tabela sistema",
        }


def _stock_assistant_metadata(*, primary_type: str, preferred: str) -> dict:
    rows = [{"branch": "01", "current_quantity": 100}]
    table = {
        "type": "table",
        "title": "Estoque",
        "columns": [
            {"key": "branch", "label": "Filial"},
            {"key": "current_quantity", "label": "Qtd."},
        ],
        "rows": rows,
    }
    chart = {
        "type": "chart",
        "chartType": "bar",
        "title": "Estoque",
        "data": [{"name": "01", "Qtd.": 100}],
    }

    presentation = chart if primary_type == "chart" else table

    return {
        "ok": True,
        "path": "/products/10080077/stock",
        "actionId": "stock-action",
        "preferredFormat": preferred,
        "availableFormats": ["text", "table", "chart"],
        "presentation": presentation,
        "tablePresentation": table,
        "chartPresentation": chart,
        "paginationConsolidation": {
            "consolidatedPayload": {
                "items": rows,
                "total": 1,
                "page": 1,
                "page_size": 1,
                "total_pages": 1,
            },
        },
    }


def _build_service() -> ChatToolContextService:
    return ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=NoReexecuteToolUseCase(),
        external_action_selection_service=BlockSystemTablesSelection(),
    )


def _history(primary_type: str, preferred: str) -> list[dict]:
    return [
        {"role": "user", "content": "estoque do produto 10080077"},
        {
            "role": "assistant",
            "content": "Estoque",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "stock-action",
                            "parameters": {"productCode": "10080077"},
                        },
                        "metadata": _stock_assistant_metadata(
                            primary_type=primary_type,
                            preferred=preferred,
                        ),
                    }
                ]
            },
        },
    ]


def test_refinement_to_table_from_text_first_table_presentations():
    execute_tool = NoReexecuteToolUseCase()
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=BlockSystemTablesSelection(),
    )
    rows = [{"branch": "01", "warehouse": "01", "current_quantity": 160242}]
    history = [
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
                            "presentationDecision": {
                                "selected": "text",
                                "layoutMode": "single",
                            },
                            "textPresentation": {
                                "type": "markdown",
                                "markdown": "Consultei o estoque...",
                            },
                            "tablePresentations": [
                                {
                                    "type": "table",
                                    "role": "list",
                                    "title": "Estoque",
                                    "columns": [
                                        {"key": "branch", "label": "Filial"},
                                        {"key": "current_quantity", "label": "Qtd. atual"},
                                    ],
                                    "rows": rows,
                                }
                            ],
                            "paginationConsolidation": {
                                "completed": True,
                                "consolidatedPayload": {
                                    "items": rows,
                                    "total": 1,
                                    "page": 1,
                                    "page_size": 1,
                                    "total_pages": 1,
                                },
                            },
                        },
                    }
                ]
            },
        },
    ]

    result = service.build_context(
        user_id="u",
        access_token="t",
        message="mostre o último resultado em tabela",
        previous_messages=history,
        allowed_action_ids=["stock-action", "system-tables"],
    )
    meta = result["toolCalls"][0]["metadata"]

    assert execute_tool.calls == 0
    assert meta["preferredFormat"] == "table"
    assert meta.get("presentation", {}).get("type") == "table"
    assert meta.get("presentationDecision", {}).get("selected") == "table"
    assert "/system/tables" not in str(meta.get("path") or "")


def test_refinement_to_table_from_chart():
    execute_tool = NoReexecuteToolUseCase()
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=BlockSystemTablesSelection(),
    )
    result = service.build_context(
        user_id="u",
        access_token="t",
        message="coloque em uma tabela",
        previous_messages=_history("chart", "chart"),
        allowed_action_ids=["stock-action", "system-tables"],
    )
    meta = result["toolCalls"][0]["metadata"]

    assert execute_tool.calls == 0
    assert meta["preferredFormat"] == "table"
    assert meta["presentation"]["type"] == "table"
    assert "/system/tables" not in str(meta.get("path") or "")


def test_apply_format_override_text_hides_kpi_primary():
    service = _build_service()
    kpi = {
        "type": "kpi",
        "title": "Indicadores de RH",
        "cards": [{"label": "PDIs ativos", "value": 29}],
    }
    meta = {
        "ok": True,
        "path": "/hr/snapshot",
        "presentationDecision": {
            "selected": "kpi",
            "availableViews": ["kpi", "text", "table", "chart"],
        },
        "presentation": kpi,
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Indicadores de RH",
        },
    }
    tool_calls = [{"name": "execute_external_action", "metadata": meta}]

    service._apply_format_override(tool_calls, "text", {"active_pdis": 29})

    assert meta["preferredFormat"] == "text"
    assert meta["presentationDecision"]["selected"] == "text"
    assert meta["presentation"] is None
    assert meta["kpiPresentation"] == kpi


def test_refinement_to_chart_from_table():
    service = _build_service()
    result = service.build_context(
        user_id="u",
        access_token="t",
        message="mostre em gráfico",
        previous_messages=_history("table", "table"),
        allowed_action_ids=["stock-action"],
    )
    meta = result["toolCalls"][0]["metadata"]

    assert meta["preferredFormat"] == "chart"
    assert (
        meta["presentation"]["type"] == "chart"
        or (meta.get("chartPresentation") or {}).get("type") == "chart"
    )


def test_refinement_to_tree_from_analyser_history():
    service = _build_service()
    history = [
        {"role": "user", "content": "me fale do produto 90260149"},
        {
            "role": "assistant",
            "content": "ok",
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
                            "preferredFormat": "table",
                            "presentation": {
                                "type": "table",
                                "title": "Roteiro",
                                "columns": [{"key": "op", "label": "Op."}],
                                "rows": [{"op": "01"}],
                            },
                            "treePresentation": {
                                "type": "tree",
                                "title": "Estrutura",
                                "root": {
                                    "id": "90260149",
                                    "label": "90260149",
                                    "children": [],
                                },
                            },
                            "tablePresentations": [
                                {
                                    "type": "table",
                                    "title": "Roteiro",
                                    "columns": [{"key": "op", "label": "Op."}],
                                    "rows": [{"op": "01"}],
                                }
                            ],
                        },
                    }
                ]
            },
        },
    ]

    result = service.build_context(
        user_id="u",
        access_token="t",
        message="mostre em árvore",
        previous_messages=history,
        allowed_action_ids=["analyser-action"],
    )
    meta = result["toolCalls"][0]["metadata"]

    assert meta["preferredFormat"] == "tree"
    assert meta["presentation"]["type"] == "tree"
