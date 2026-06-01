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
    assert root["items"] == stock_rows
    assert arguments["actionId"] == "stock-action"
    assert merged_metadata["actionId"] == "stock-action"
    assert continue_prompt is None
