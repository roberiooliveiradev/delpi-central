from dataclasses import dataclass

from app.application.services.chat_paginated_external_action_service import (
    ChatPaginatedExternalActionService,
)
from app.domain.entities.tool_result import ToolResult
from app.domain.services.chat_pagination_consolidation_service import (
    ChatPaginationConsolidationService,
)


def _page_payload(page: int, *, page_size: int = 2, total: int = 6):
    return {
        "items": [{"code": f"item-{page}-{index}"} for index in range(page_size)],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total // page_size,
    }


@dataclass
class FakeExternalActionUseCase:
    def build_metadata_for_data(self, *, action_id, data, parameters=None):
        return {
            "ok": True,
            "actionId": action_id,
            "path": "/products/{code}/parents",
            "operationId": "product_parents",
        }


class FakeExecuteToolUseCase:
    def __init__(self):
        self.calls: list[int] = []
        self.tools = {
            "execute_external_action": type(
                "Tool",
                (),
                {"use_case": FakeExternalActionUseCase()},
            )()
        }

    def execute(self, request):
        page = int((request.arguments.get("parameters") or {}).get("page") or 1)
        self.calls.append(page)
        return ToolResult(
            name="execute_external_action",
            data={"data": _page_payload(page)},
            metadata={
                "ok": True,
                "actionId": request.arguments.get("actionId"),
                "path": "/products/{code}/parents",
            },
        )


def test_maybe_consolidate_fetches_remaining_pages():
    execute_tool = FakeExecuteToolUseCase()
    service = ChatPaginatedExternalActionService(execute_tool)

    merged_data, merged_metadata, continue_prompt = service.maybe_consolidate(
        user_id="user-1",
        access_token="token",
        message="traga tudo",
        previous_messages=[],
        base_arguments={
            "actionId": "parents-action",
            "parameters": {"code": "10080047", "page": 1},
        },
        base_metadata={
            "ok": True,
            "actionId": "parents-action",
            "path": "/products/{code}/parents",
        },
        base_data={"data": _page_payload(1)},
    )

    assert execute_tool.calls == [2, 3]
    root = ChatPaginationConsolidationService._unwrap(merged_data)
    assert len(root["items"]) == 6
    assert merged_metadata.get("paginationConsolidation", {}).get("completed") is True
    assert continue_prompt is None


def test_fetch_continue_plan_resumes_from_previous_state():
    execute_tool = FakeExecuteToolUseCase()
    service = ChatPaginatedExternalActionService(execute_tool)
    previous_messages = [
        {
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "actionId": "parents-action",
                            "path": "/products/{code}/parents",
                            "paginationConsolidation": {
                                "actionId": "parents-action",
                                "path": "/products/{code}/parents",
                                "parameters": {"code": "10080047"},
                                "fetchedPages": [1, 2],
                                "mergedCount": 4,
                                "apiTotal": 6,
                                "totalPages": 3,
                                "completed": False,
                                "consolidatedPayload": _page_payload(1)
                                | {"items": _page_payload(1)["items"] + _page_payload(2)["items"]},
                            },
                        },
                    }
                ]
            }
        }
    ]

    result = service.fetch_continue_plan(
        user_id="user-1",
        access_token="token",
        message="sim, continue",
        previous_messages=previous_messages,
    )

    assert result is not None
    merged_data, merged_metadata, arguments, continue_prompt = result
    assert execute_tool.calls == [3]
    root = ChatPaginationConsolidationService._unwrap(merged_data)
    assert len(root["items"]) == 6
    assert merged_metadata["paginationConsolidation"]["completed"] is True
    assert arguments["actionId"] == "parents-action"
    assert continue_prompt is None


def test_fetch_format_refinement_reuses_cached_stock_payload():
    execute_tool = FakeExecuteToolUseCase()
    service = ChatPaginatedExternalActionService(execute_tool)
    stock_rows = [{"branch": "01", "current_quantity": 100}]
    previous_messages = [
        {
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
                            "actionId": "stock-action",
                            "path": "/products/10080077/stock",
                            "paginationConsolidation": {
                                "consolidatedPayload": {
                                    "items": stock_rows,
                                    "total": 1,
                                    "page": 1,
                                    "page_size": 1,
                                    "total_pages": 1,
                                },
                            },
                            "tablePresentation": {
                                "type": "table",
                                "columns": [{"key": "branch", "label": "Filial"}],
                                "rows": stock_rows,
                            },
                        },
                    }
                ]
            }
        }
    ]

    result = service.fetch_format_refinement_from_history(
        user_id="user-1",
        access_token="token",
        message="mostre o último resultado em tabela",
        previous_messages=previous_messages,
    )

    assert result is not None
    merged_data, merged_metadata, arguments, continue_prompt = result
    assert execute_tool.calls == []
    root = ChatPaginationConsolidationService._unwrap(merged_data)
    items_root = root.get("stock") if isinstance(root.get("stock"), dict) else root
    assert items_root["items"] == stock_rows
    assert arguments["actionId"] == "stock-action"
    assert merged_metadata["actionId"] == "stock-action"
    assert continue_prompt is None


_PRODUCTION_SQL_ROWS = [
    {
        "COD_PRODUTO": "90264130",
        "DESCRICAO_PRODUTO": "PARAFUSO M8",
        "QTD_PLANEJADA": 1200,
        "UNIDADE": "UN",
    },
    {
        "COD_PRODUTO": "10080047",
        "DESCRICAO_PRODUTO": "TERMINAL PINO",
        "QTD_PLANEJADA": 500,
        "UNIDADE": "UN",
    },
]


class _SqlFormatRefinementExternalUseCase:
    def build_metadata_for_data(self, *, action_id, data, parameters=None):
        from app.application.use_cases.execute_external_action_use_case import (
            ExecuteExternalActionUseCase,
        )

        use_case = ExecuteExternalActionUseCase(
            repository=None,
            gateway=None,
            policy=None,
            audit_repository=None,
        )

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


class _SqlFormatRefinementExecuteToolUseCase:
    def __init__(self):
        self.calls: list[int] = []
        self.tools = {
            "execute_external_action": type(
                "Tool",
                (),
                {"use_case": _SqlFormatRefinementExternalUseCase()},
            )()
        }

    def execute(self, request):
        raise AssertionError("não deve reexecutar SQL no refinamento com cache")


def test_fetch_format_refinement_reuses_cached_sql_payload():
    execute_tool = _SqlFormatRefinementExecuteToolUseCase()
    service = ChatPaginatedExternalActionService(execute_tool)
    previous_messages = [
        {
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "api_delpi.data.execute_readonly_sql",
                            "parameters": {"body": {"sql": "SELECT 1"}},
                        },
                        "metadata": {
                            "ok": True,
                            "actionId": "api_delpi.data.execute_readonly_sql",
                            "path": "/data/sql",
                            "sensitivity": "sql",
                            "operationId": "execute_readonly_sql",
                            "preferredFormat": "text",
                            "tablePresentation": {
                                "type": "table",
                                "title": "Produtos programados para produção",
                                "columns": [
                                    {"key": "COD_PRODUTO", "label": "Código"},
                                    {"key": "DESCRICAO_PRODUTO", "label": "Descrição"},
                                ],
                                "rows": _PRODUCTION_SQL_ROWS,
                            },
                        },
                    }
                ]
            }
        }
    ]

    result = service.fetch_format_refinement_from_history(
        user_id="user-1",
        access_token="token",
        message="mostre o último resultado em tabela",
        previous_messages=previous_messages,
    )

    assert result is not None
    merged_data, merged_metadata, arguments, continue_prompt = result
    assert execute_tool.calls == []
    root = ChatPaginationConsolidationService._unwrap(merged_data)
    assert root["rows"] == _PRODUCTION_SQL_ROWS
    assert arguments["actionId"] == "api_delpi.data.execute_readonly_sql"
    assert merged_metadata.get("preferredFormat") == "table"
    assert merged_metadata.get("presentation", {}).get("type") == "table"
    assert merged_metadata.get("presentation", {}).get("rows") == _PRODUCTION_SQL_ROWS
    assert continue_prompt is None
