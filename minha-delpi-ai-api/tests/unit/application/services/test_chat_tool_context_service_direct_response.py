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


class FakeExternalActionExecuteToolUseCase:
    def execute(self, request):
        return ToolResult(
            name="execute_external_action",
            data={
                "success": True,
                "data": {
                    "product": {
                        "code": "10080055",
                        "description": "TERM. FASTON 4,80X0,50",
                        "type": "ME",
                        "unit": "UN",
                        "group_code": "1008",
                        "active": True,
                    }
                },
            },
            metadata={
                "ok": True,
                "statusCode": 200,
                "actionId": "action-1",
                "path": "/products/{code}/analyser",
                "provider": "api_delpi",
            },
        )


class FakeExternalActionSelectionService:
    def select_action(
        self,
        message,
        allowed_action_ids=None,
        conversation_context=None,
        previous_messages=None,
    ):
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": "action-1",
                "parameters": {"code": "10080055"},
            },
            "reason": "Consulta de produto",
        }


def test_build_context_sets_direct_answer_for_successful_external_action():
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=FakeExternalActionExecuteToolUseCase(),
        external_action_selection_service=FakeExternalActionSelectionService(),
    )

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="descrição do produto 10080055",
        allowed_action_ids=["action-1"],
    )

    assert result["skipRag"] is True
    assert "10080055" in result["directAnswer"]
    assert "TERM. FASTON" in result["directAnswer"]
    assert "Tipo ME" not in result["directAnswer"]
    assert len(result["toolCalls"]) == 1


def test_compact_direct_answer_for_rich_presentation_keeps_title_only():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "presentation": {
                    "type": "chart",
                    "title": "CPV por filial",
                },
                "tablePresentation": {
                    "type": "table",
                    "title": "CPV por filial",
                },
            },
        }
    ]

    markdown_body = (
        "### CPV por filial\n\n"
        "| Filial | Valor |\n"
        "|---|---|\n"
        "| 01 | 100 |\n"
        "| 02 | 200 |\n"
    )

    compact = ChatToolContextService._compact_direct_answer_for_rich_presentation(
        markdown_body,
        tool_calls,
    )

    assert compact == "CPV por filial"


def test_compact_direct_answer_for_rich_presentation_keeps_short_text():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "presentation": {"type": "table", "title": "Estoque"},
            },
        }
    ]

    compact = ChatToolContextService._compact_direct_answer_for_rich_presentation(
        "Saldo disponível na filial 02.",
        tool_calls,
    )

    assert compact == "Saldo disponível na filial 02."


def test_resolve_presentation_only_answer_for_kpi():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "statusCode": 200,
                "presentation": {
                    "type": "kpi",
                    "title": "Valor Total de Estoque",
                    "cards": [{"label": "Valor Total", "value": 1}],
                },
            },
        }
    ]

    assert ChatToolContextService.should_answer_with_presentation_only(tool_calls)
    assert (
        ChatToolContextService.resolve_presentation_only_answer(tool_calls)
        == "Valor Total de Estoque"
    )


def test_resolve_presentation_only_answer_requires_successful_tools():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": False,
                "presentation": {
                    "type": "kpi",
                    "title": "Valor Total de Estoque",
                },
            },
        }
    ]

    assert not ChatToolContextService.should_answer_with_presentation_only(tool_calls)
    assert ChatToolContextService.resolve_presentation_only_answer(tool_calls) is None


def test_resolve_presentation_only_answer_for_tree():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "statusCode": 200,
                "path": "/products/10080055/analyser",
                "presentation": {
                    "type": "tree",
                    "title": "Informações completas do produto 10080055",
                    "nodes": [],
                },
            },
        }
    ]

    assert ChatToolContextService.should_answer_with_presentation_only(tool_calls)
    assert (
        ChatToolContextService.resolve_presentation_only_answer(tool_calls)
        == "Informações completas do produto 10080055"
    )


def _parents_page(page: int, *, page_size: int = 2, total: int = 6):
    return {
        "items": [{"code": f"parent-{page}-{index}", "description": f"P{page}-{index}"} for index in range(page_size)],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total // page_size,
    }


class PaginatedParentsExecuteToolUseCase:
    def __init__(self):
        self.calls: list[int] = []
        self.tools = {
            "execute_external_action": type(
                "Tool",
                (),
                {
                    "use_case": type(
                        "UseCase",
                        (),
                        {
                            "build_metadata_for_data": staticmethod(
                                lambda *, action_id, data, parameters=None: {
                                    "ok": True,
                                    "actionId": action_id,
                                    "path": "/products/{code}/parents",
                                    "operationId": "product_parents",
                                }
                            )
                        },
                    )()
                },
            )()
        }

    def execute(self, request):
        page = int((request.arguments.get("parameters") or {}).get("page") or 1)
        self.calls.append(page)
        return ToolResult(
            name="execute_external_action",
            data={"data": _parents_page(page)},
            metadata={
                "ok": True,
                "statusCode": 200,
                "actionId": "parents-action",
                "path": "/products/{code}/parents",
                "operationId": "product_parents",
            },
        )


class PaginatedParentsSelectionService:
    def select_action(
        self,
        message,
        allowed_action_ids=None,
        conversation_context=None,
        previous_messages=None,
    ):
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": "parents-action",
                "parameters": {"code": "10080047", "page": 1},
            },
            "reason": "Produtos pai",
        }


def test_build_context_consolidates_when_user_asks_for_full_list():
    execute_tool = PaginatedParentsExecuteToolUseCase()
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=PaginatedParentsSelectionService(),
    )

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="traga tudo",
        allowed_action_ids=["parents-action"],
    )

    assert execute_tool.calls == [1, 2, 3]
    consolidation = result["toolCalls"][0]["metadata"].get("paginationConsolidation") or {}
    assert consolidation.get("completed") is True
    assert consolidation.get("mergedCount") == 6
    assert result.get("directAnswer")


def test_build_context_continue_fetch_without_new_selection():
    execute_tool = PaginatedParentsExecuteToolUseCase()
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=PaginatedParentsSelectionService(),
    )
    previous_messages = [
        {
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "actionId": "parents-action",
                            "path": "/products/{code}/parents",
                            "operationId": "product_parents",
                            "paginationConsolidation": {
                                "actionId": "parents-action",
                                "path": "/products/{code}/parents",
                                "parameters": {"code": "10080047"},
                                "fetchedPages": [1, 2],
                                "mergedCount": 4,
                                "apiTotal": 6,
                                "totalPages": 3,
                                "completed": False,
                                "consolidatedPayload": {
                                    "items": _parents_page(1)["items"] + _parents_page(2)["items"],
                                    "total": 6,
                                    "page": 1,
                                    "page_size": 4,
                                    "total_pages": 1,
                                },
                            },
                        },
                    }
                ]
            }
        }
    ]

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="sim, continue",
        previous_messages=previous_messages,
        allowed_action_ids=["parents-action"],
    )

    assert execute_tool.calls == [3]
    consolidation = result["toolCalls"][0]["metadata"].get("paginationConsolidation") or {}
    assert consolidation.get("completed") is True
    assert consolidation.get("mergedCount") == 6
    assert result.get("skipRag") is True


def test_build_context_full_fetch_from_previous_paginated_turn():
    execute_tool = PaginatedParentsExecuteToolUseCase()
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=PaginatedParentsSelectionService(),
    )
    previous_messages = [
        {"role": "user", "content": "onde é usado o 10080047"},
        {
            "role": "assistant",
            "content": "Produtos pai parcial",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "parents-action",
                            "parameters": {
                                "code": "10080047",
                                "page": 1,
                                "page_size": 25,
                            },
                        },
                        "metadata": {
                            "ok": True,
                            "statusCode": 200,
                            "path": "/products/10080047/parents",
                            "actionId": "parents-action",
                            "operationId": "product_parents",
                            "dataCoverageNotice": {
                                "kind": "pagination",
                                "message": "Produtos pai parcial: página 1 de 3.",
                                "details": {
                                    "pagination": {
                                        "page": 1,
                                        "pageSize": 25,
                                        "total": 6,
                                        "totalPages": 3,
                                    }
                                },
                            },
                        },
                    }
                ]
            },
        },
    ]

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="arvore completa",
        previous_messages=previous_messages,
        allowed_action_ids=["parents-action"],
    )

    assert execute_tool.calls == [1, 2, 3]
    consolidation = result["toolCalls"][0]["metadata"].get("paginationConsolidation") or {}
    assert consolidation.get("completed") is True
    assert consolidation.get("mergedCount") == 6
    assert result.get("skipRag") is True


def test_build_context_full_fetch_table_from_previous_paginated_turn():
    execute_tool = PaginatedParentsExecuteToolUseCase()
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=PaginatedParentsSelectionService(),
    )
    previous_messages = [
        {"role": "user", "content": "onde é usado o 10080047"},
        {
            "role": "assistant",
            "content": "Produtos pai parcial",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "parents-action",
                            "parameters": {
                                "code": "10080047",
                                "page": 1,
                                "page_size": 25,
                            },
                        },
                        "metadata": {
                            "ok": True,
                            "statusCode": 200,
                            "path": "/products/10080047/parents",
                            "actionId": "parents-action",
                            "operationId": "product_parents",
                            "preferredFormat": "tree",
                            "dataCoverageNotice": {
                                "kind": "pagination",
                                "message": "Produtos pai parcial: página 1 de 3.",
                                "details": {
                                    "pagination": {
                                        "page": 1,
                                        "pageSize": 25,
                                        "total": 6,
                                        "totalPages": 3,
                                    }
                                },
                            },
                        },
                    }
                ]
            },
        },
    ]

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="tabela completa",
        previous_messages=previous_messages,
        allowed_action_ids=["parents-action"],
    )

    metadata = result["toolCalls"][0]["metadata"]
    assert execute_tool.calls == [1, 2, 3]
    assert metadata.get("preferredFormat") == "table"
    assert metadata.get("presentation", {}).get("type") == "table"
    assert metadata.get("paginationConsolidation", {}).get("completed") is True

