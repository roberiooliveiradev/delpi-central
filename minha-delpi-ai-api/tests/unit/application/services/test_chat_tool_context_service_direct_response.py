from dataclasses import dataclass

from app.application.services.chat_tool_context_service import ChatToolContextService
from app.domain.entities.tool_result import ToolResult
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntent
from app.domain.services.tool_selection_service import ToolSelectionService
from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
    _analyser_payload_with_guide_and_inspection,
)


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
        **kwargs,
    ):
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": "action-1",
                "parameters": {"code": "10080055"},
            },
            "reason": "Consulta de produto",
        }


class EmptyToolSelectionService:
    def select_tools(self, message, **kwargs):
        return []


class DrawingAnalyserSelectionService:
    def __init__(self, action_id: str = "get_product_analyser"):
        self.action_id = action_id
        self.product_calls: list[dict] = []
        self.generic_calls = 0

    def select_action_for_product(
        self,
        message,
        *,
        product_code,
        allowed_action_ids=None,
        intent=None,
        route_segment=None,
        previous_messages=None,
    ):
        self.product_calls.append(
            {
                "productCode": product_code,
                "intent": intent,
                "routeSegment": route_segment,
            }
        )

        if self.action_id not in (allowed_action_ids or []):
            return None

        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": self.action_id,
                "parameters": {"code": product_code},
            },
            "reason": "Analise tecnica do desenho",
        }

    def select_action(self, *args, **kwargs):
        self.generic_calls += 1
        raise AssertionError("drawing analysis must not use generic action selection")


class DrawingAnalyserExecuteToolUseCase:
    def __init__(self):
        self.calls: list[dict] = []

    def execute(self, request):
        arguments = request.arguments or {}
        parameters = arguments.get("parameters") or {}
        product_code = str(parameters.get("code") or "")
        self.calls.append(arguments)

        payload = _analyser_payload_with_guide_and_inspection()
        payload["product"]["code"] = product_code

        return ToolResult(
            name="execute_external_action",
            data={"data": payload},
            metadata={
                "ok": True,
                "statusCode": 200,
                "actionId": arguments.get("actionId"),
                "path": "/products/{code}/analyser",
                "operationId": "get_product_analyser",
                "provider": "api_delpi",
                "authorizedResult": {"data": payload},
            },
        )


def _drawing_agent_context():
    return {
        "metadata": {
            "skills": {
                "drawing-analysis-delpi": {"engineering": True},
                "document-vision-delpi": {"enabled": True},
            }
        }
    }


def _drawing_attachment_context(product_code: str = "90264231") -> str:
    return (
        "### 90264231.pdf\n"
        f"CODIGO DO PRODUTO: {product_code}\n"
        "REV. 00\n"
        "COMPONENTE 50212194\n"
        "COMPRIMENTO TOTAL: 1400 mm\n"
    )


def _patch_document_vision(monkeypatch):
    from app.application.services.chat_document_vision_service import (
        ChatDocumentVisionService,
    )

    def enrich(parsed, **kwargs):
        payload = dict(parsed or {})
        payload.setdefault("productCode", "90264231")
        payload.setdefault("revision", "00")
        payload.setdefault("componentCodes", ["50212194"])
        payload.setdefault("charCount", 96)
        payload.setdefault("legible", True)
        payload["documentVision"] = {
            "engine": "unit_test",
            "charCount": payload.get("charCount"),
            "legible": payload.get("legible"),
        }
        return payload

    monkeypatch.setattr(
        ChatDocumentVisionService,
        "enrich_drawing_extract",
        staticmethod(enrich),
    )


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
    assert len(result["toolCalls"]) == 1

    metadata = result["toolCalls"][0]["metadata"]
    assert metadata.get("ok") is True
    summary_lines = (metadata.get("humanizedSummary") or {}).get("linhas") or []
    assert any("10080055" in line for line in summary_lines)
    assert any("| Campo | Valor |" in line for line in summary_lines)


def test_drawing_pdf_product_code_forces_product_analyser_action(monkeypatch):
    _patch_document_vision(monkeypatch)
    execute_tool = DrawingAnalyserExecuteToolUseCase()
    selection_service = DrawingAnalyserSelectionService()
    service = ChatToolContextService(
        tool_selection_service=EmptyToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=selection_service,
    )

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="analise o desenho",
        allowed_action_ids=["transforma-summary", "get_product_analyser"],
        agent_context=_drawing_agent_context(),
        attachment_ids=["attachment-1"],
        attachment_context=_drawing_attachment_context(),
    )

    assert selection_service.generic_calls == 0
    assert selection_service.product_calls == [
        {
            "productCode": "90264231",
            "intent": ChatProductQueryIntent.ANALYSER,
            "routeSegment": None,
        }
    ]
    assert execute_tool.calls == [
        {
            "actionId": "get_product_analyser",
            "parameters": {"code": "90264231"},
        }
    ]
    assert result["drawingAnalysisMode"] is True
    assert result["selectedExternalAction"]["forcedBy"] == "drawing_analysis_pdf"
    assert result["selectedExternalAction"]["productCode"] == "90264231"
    assert result["toolCalls"][0]["arguments"]["actionId"] == "get_product_analyser"
    assert result["toolCalls"][0]["metadata"]["path"] == "/products/{code}/analyser"
    assert result["drawingAnalysis"]["productCode"] == "90264231"


def test_drawing_pdf_does_not_fall_back_to_operational_action_when_analyser_missing(
    monkeypatch,
):
    _patch_document_vision(monkeypatch)
    execute_tool = DrawingAnalyserExecuteToolUseCase()
    selection_service = DrawingAnalyserSelectionService()
    service = ChatToolContextService(
        tool_selection_service=EmptyToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=selection_service,
    )

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="analise o desenho",
        allowed_action_ids=["transforma-summary"],
        agent_context=_drawing_agent_context(),
        attachment_ids=["attachment-1"],
        attachment_context=_drawing_attachment_context(),
    )

    assert selection_service.generic_calls == 0
    assert selection_service.product_calls[0]["productCode"] == "90264231"
    assert execute_tool.calls == []
    assert result["toolCalls"] == []
    assert result["skipRag"] is True
    assert "90264231" in result["directAnswer"]
    assert "/products/{code}/analyser" in result["directAnswer"]


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


def test_prefer_presentation_direct_answer_keeps_short_explanatory_summary():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "statusCode": 200,
                "path": "/products/90260142/guide",
                "presentation": {
                    "type": "table",
                    "title": "Roteiro do produto",
                    "columns": [{"key": "operation_description", "label": "Descrição operação"}],
                    "rows": [{"operation_description": "CORTAR - MANUAL"}],
                },
            },
        }
    ]
    summary = (
        "O produto **90260142** possui 3 operação(ões): "
        "**01** CORTAR - MANUAL, **02** INSERIR TUBO ISOLANTE e **03** EMBALAR."
    )

    compact = ChatToolContextService.prefer_presentation_direct_answer(
        summary,
        tool_calls,
    )

    assert "90260142" in compact
    assert "CORTAR - MANUAL" in compact


def test_prefer_presentation_direct_answer_replaces_long_markdown():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "statusCode": 200,
                "path": "/commercial/billing",
                "presentation": {
                    "type": "kpi",
                    "title": "Faturamento comercial",
                    "items": [{"label": "Total", "value": "R$ 1,00"}],
                },
            },
        }
    ]
    long_answer = "| Filial | Valor |\n| --- | --- |\n| 01 | R$ 1,00 |\n" * 5

    compact = ChatToolContextService.prefer_presentation_direct_answer(
        long_answer,
        tool_calls,
    )

    assert compact == "Faturamento comercial"


def test_build_authorized_answer_prefers_text_presentation_markdown():
    markdown = "### Informações completas do produto 90260149\n\nCHICOTE EPR SINGELO 235MM."
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90260149/analyser",
                "textPresentation": {
                    "type": "markdown",
                    "markdown": markdown,
                },
                "presentation": {
                    "type": "tree",
                    "title": "Estrutura do produto 90260149",
                    "root": {"id": "90260149", "label": "90260149", "children": []},
                },
            },
        }
    ]

    assert ChatToolContextService.build_authorized_answer_from_tool_calls(tool_calls) == markdown
    assert ChatToolContextService.should_persist_authorized_tool_answer(
        tool_calls,
        message="me fale do produto 90260149",
    )


def test_resolve_authorized_persisted_answer_replaces_llm_hallucination():
    authorized = "### Informações completas do produto 90260149\n\nCHICOTE EPR SINGELO 235MM."
    hallucinated = "Produtos Químicos e Solução Química Especializada."
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/90260149/analyser",
                "textPresentation": {
                    "type": "markdown",
                    "markdown": authorized,
                },
                "presentation": {
                    "type": "tree",
                    "title": "Estrutura do produto 90260149",
                    "root": {"id": "90260149", "label": "90260149", "children": []},
                },
            },
        }
    ]

    persisted = ChatToolContextService.resolve_authorized_persisted_answer(
        hallucinated,
        tool_calls,
        message="me fale do produto 90260149",
    )

    assert persisted == authorized
    assert "Químicos" not in persisted


def test_resolve_authorized_persisted_answer_keeps_pagination_suffix():
    authorized = "### Pais do produto 10080055\n\nResumo."
    continuation = (
        "Consolidei **2** de **6** registro(s) (páginas 1). "
        "**Deseja que eu continue buscando?** Responda *sim, continue*."
    )
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "textPresentation": {
                    "type": "markdown",
                    "markdown": authorized,
                },
                "presentation": {
                    "type": "table",
                    "title": "Pais do produto 10080055",
                    "columns": [{"key": "code", "label": "Código"}],
                    "rows": [{"code": "10080001"}],
                },
            },
        }
    ]

    persisted = ChatToolContextService.resolve_authorized_persisted_answer(
        f"{authorized}\n\n{continuation}",
        tool_calls,
        message="onde é usado o produto 10080055",
    )

    assert continuation in persisted
    assert persisted.startswith(authorized)


def test_prefer_presentation_direct_answer_keeps_pagination_prompt():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "statusCode": 200,
                "path": "/products/10080055/parents",
                "presentation": {
                    "type": "table",
                    "title": "Pais do produto 10080055",
                    "columns": [{"key": "code", "label": "Código"}],
                    "rows": [{"code": "10080001"}],
                },
            },
        }
    ]
    continuation = (
        "Consolidei **2** de **6** registro(s) (páginas 1). "
        "Ainda faltam cerca de **4** registro(s) em 2 página(s). "
        "**Deseja que eu continue buscando?** Responda *sim, continue* para trazer o restante."
    )
    long_answer = "| Código |\n| --- |\n| 10080001 |\n\n" + continuation

    compact = ChatToolContextService.prefer_presentation_direct_answer(
        long_answer,
        tool_calls,
    )

    assert compact.startswith("Pais do produto 10080055")
    assert "**Deseja que eu continue buscando?**" in compact


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
        **kwargs,
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


class _StockFormatRefinementExecuteToolUseCase:
    def __init__(self):
        self.calls = 0

    def execute(self, request):
        self.calls += 1
        raise AssertionError("não deve reexecutar consulta no refinamento com cache")


class _SystemTableSelectionService:
    def select_action(self, *args, **kwargs):
        return {
            "name": "execute_external_action",
            "arguments": {"actionId": "system-tables", "parameters": {}},
            "reason": "tabela de sistema",
        }


def test_build_context_format_refinement_without_system_tables_route():
    execute_tool = _StockFormatRefinementExecuteToolUseCase()
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=_SystemTableSelectionService(),
    )
    stock_rows = [
        {
            "branch": "01",
            "warehouse": "01",
            "current_quantity": 160242,
        }
    ]
    previous_messages = [
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
                                "columns": [
                                    {"key": "branch", "label": "Filial"},
                                    {"key": "current_quantity", "label": "Qtd. atual"},
                                ],
                                "rows": stock_rows,
                            },
                            "paginationConsolidation": {
                                "consolidatedPayload": {
                                    "items": stock_rows,
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
        user_id="user-1",
        access_token="token",
        message="mostre o último resultado em tabela",
        previous_messages=previous_messages,
        allowed_action_ids=["stock-action", "system-tables"],
    )

    assert execute_tool.calls == 0
    metadata = result["toolCalls"][0]["metadata"]
    assert metadata.get("preferredFormat") == "table"
    assert metadata.get("presentation", {}).get("type") == "table"
    assert result.get("skipRag") is True
    assert "/system/tables" not in str(metadata.get("path") or "")


def test_build_context_coloque_em_uma_tabela_without_system_tables_route():
    execute_tool = _StockFormatRefinementExecuteToolUseCase()
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=_SystemTableSelectionService(),
    )
    stock_rows = [
        {
            "branch": "01",
            "warehouse": "01",
            "current_quantity": 160242,
        }
    ]
    previous_messages = [
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
                            "preferredFormat": "chart",
                            "availableFormats": ["text", "table", "chart"],
                            "presentation": {
                                "type": "chart",
                                "title": "Estoque",
                                "data": [{"name": "01/01", "Qtd. atual": 160242}],
                            },
                            "tablePresentation": {
                                "type": "table",
                                "title": "Estoque",
                                "columns": [
                                    {"key": "branch", "label": "Filial"},
                                    {"key": "current_quantity", "label": "Qtd. atual"},
                                ],
                                "rows": stock_rows,
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
        message="coloque em uma tabela",
        previous_messages=previous_messages,
        allowed_action_ids=["stock-action", "system-tables"],
    )

    assert execute_tool.calls == 0
    metadata = result["toolCalls"][0]["metadata"]
    assert metadata.get("preferredFormat") == "table"
    assert metadata.get("presentation", {}).get("type") == "table"
    assert len(metadata.get("presentation", {}).get("rows") or []) == 1
    assert "/system/tables" not in str(metadata.get("path") or "")
