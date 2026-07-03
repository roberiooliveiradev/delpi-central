from app.application.services.chat_external_action_orchestration_service import (
    ChatExternalActionOrchestrationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)


class FakeSelectionService:
    def __init__(self):
        self.product_calls: list[tuple[str, str]] = []

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
        self.product_calls.append((product_code, intent))
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": "product-structure",
                "parameters": {"code": product_code},
            },
            "reason": f"estrutura {product_code}",
        }

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
            "arguments": {"actionId": "product-stock"},
            "reason": "única",
        }


def test_plan_actions_estoque_uses_all_context_products_from_working_memory(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_external_action_orchestration_service.Settings.CHAT_MULTI_ACTION_ENABLED",
        True,
    )
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="estoque",
        allowed_action_ids=["product-stock"],
        workspace_context={
            "workingMemory": {
                "userContextItems": [
                    {
                        "id": "a",
                        "content": "90260140",
                        "extractedEntities": {"productCode": "90260140"},
                    },
                    {
                        "id": "b",
                        "content": "produto 10080014",
                        "extractedEntities": {"productCode": "10080014"},
                    },
                ],
            },
        },
        max_calls=5,
    )

    assert len(planned) == 2
    assert {call[0] for call in service.product_calls} == {"90260140", "10080014"}


def test_plan_actions_for_multiple_product_codes():
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="estrutura do produto 90260077 e do 90260088",
        allowed_action_ids=["product-structure"],
        max_calls=5,
    )

    assert len(planned) == 2
    assert service.product_calls[0][0] == "90260077"
    assert service.product_calls[1][0] == "90260088"
    assert service.product_calls[0][1] == ChatProductQueryIntent.STRUCTURE


def test_plan_actions_stock_for_multiple_product_codes_plural_phrase():
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="estoque dos produtos 10080022, 10080012?",
        allowed_action_ids=["product-stock"],
        max_calls=5,
    )

    assert len(planned) == 2
    assert service.product_calls[0] == ("10080022", ChatProductQueryIntent.STOCK)
    assert service.product_calls[1] == ("10080012", ChatProductQueryIntent.STOCK)


def test_plan_actions_parents_for_multiple_product_codes():
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="onde são usados os produtos 10080022, 10080012?",
        allowed_action_ids=["product-parents"],
        max_calls=5,
    )

    assert len(planned) == 2
    assert service.product_calls[0] == ("10080022", ChatProductQueryIntent.PARENTS)
    assert service.product_calls[1] == ("10080012", ChatProductQueryIntent.PARENTS)


def test_plan_actions_comparison_fetches_missing_structure(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_external_action_orchestration_service.Settings.CHAT_MULTI_ACTION_ENABLED",
        True,
    )
    service = FakeSelectionService()
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260077/structure",
                            "responsePreview": '{"root":{"code":"90260077","description":"A","type":"PA","unit":"MI","quantity":1},"items":[]}',
                        },
                    }
                ]
            },
        }
    ]

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="compare as estruturas",
        allowed_action_ids=["product-structure"],
        conversation_context="90260077 e 90260088",
        previous_messages=history,
        max_calls=3,
    )

    assert len(planned) == 1
    assert service.product_calls[0][0] == "90260088"


def test_plan_actions_single_code_uses_select_action():
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="estoque do produto 10080047",
        allowed_action_ids=["product-stock"],
    )

    assert len(planned) == 1
    assert planned[0]["arguments"]["actionId"] == "product-stock"
    assert not service.product_calls


def test_plan_actions_ignores_history_codes_when_message_names_product():
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="estoque do produto 10080099",
        allowed_action_ids=["product-stock"],
        conversation_context=(
            "assistant: Produto 10080001: CABO A\n"
            "assistant: Produto 10080002: CABO B\n"
            "assistant: Produto 10080003: CABO C\n"
        ),
        max_calls=5,
    )

    assert len(planned) == 1
    assert planned[0]["arguments"]["actionId"] == "product-stock"
    assert len(service.product_calls) == 0


def test_plan_actions_followup_uses_single_code_from_context():
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="busque o estoque desse produto",
        allowed_action_ids=["product-stock"],
        conversation_context="assistant: Produto 10080047: TERM. PINO RETO.",
        max_calls=5,
    )

    assert len(planned) == 1
    assert not service.product_calls


def test_plan_actions_multi_scope_structure_and_guide(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_external_action_orchestration_service.Settings.CHAT_MULTI_ACTION_ENABLED",
        True,
    )

    class ScopeSelectionService(FakeSelectionService):
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
            if intent == ChatProductQueryIntent.STRUCTURE:
                return {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": "structure",
                        "parameters": {"code": product_code},
                    },
                }

            if route_segment == "guide":
                return {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": "guide",
                        "parameters": {"code": product_code},
                    },
                }

            return None

        def select_action(self, *args, **kwargs):
            raise AssertionError("select_action não deve ser chamado")

    service = ScopeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="estrutura e roteiro do produto 90260149",
        allowed_action_ids=["structure", "guide"],
        max_calls=5,
    )

    assert len(planned) == 2
    action_ids = {item["arguments"]["actionId"] for item in planned}

    assert action_ids == {"structure", "guide"}


def test_plan_actions_pagination_follow_up_uses_pagination_refinement(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_intelligence_runtime_access.resolve_chat_intelligence_runtime",
        lambda: type("Runtime", (), {"multi_action_enabled": True})(),
    )
    class Repo:
        actions = [
            {
                "actionId": "parents-action",
                "method": "GET",
                "path": "/products/{code}/parents",
                "operationId": "get_product_parents",
                "summary": "Produtos pai",
                "parametersSchema": [
                    {"name": "code", "in": "path", "required": True},
                    {"name": "page", "in": "query"},
                    {"name": "page_size", "in": "query"},
                ],
            }
        ]

        def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
            return self.actions

    class PaginationSelectionService(FakeSelectionService):
        def __init__(self):
            super().__init__()
            self.pagination_calls = 0
            self.generic_select_calls = 0
            self._repo = Repo()

        def select_pagination_refinement(
            self,
            refinement,
            *,
            allowed_action_ids,
            message="",
        ):
            self.pagination_calls += 1
            from app.application.services.external_actions.external_action_refinement_route_selection_service import (
                ExternalActionRefinementRouteSelectionService,
            )

            return ExternalActionRefinementRouteSelectionService(self._repo).build_pagination_action(
                refinement,
                action_id=str(refinement.action_id or "parents-action"),
                allowed_action_ids=allowed_action_ids,
            )

        def select_action(
            self,
            message,
            allowed_action_ids=None,
            conversation_context=None,
            previous_messages=None,
            **kwargs,
        ):
            self.generic_select_calls += 1
            return super().select_action(
                message,
                allowed_action_ids=allowed_action_ids,
                conversation_context=conversation_context,
                previous_messages=previous_messages,
                **kwargs,
            )

    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "parents-action",
                            "parameters": {
                                "code": "10080022",
                                "page": 1,
                                "page_size": 25,
                            },
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/parents",
                            "actionId": "parents-action",
                            "dataCoverageNotice": {"kind": "pagination"},
                        },
                    }
                ]
            },
        },
    ]

    selection_service = PaginationSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        selection_service,
        message="aumente para 50 linhas",
        allowed_action_ids=["parents-action"],
        previous_messages=history,
    )

    assert selection_service.pagination_calls == 1
    assert selection_service.generic_select_calls == 0
    assert len(planned) == 1
    params = planned[0]["arguments"]["parameters"]
    assert params["code"] == "10080022"
    assert params["page_size"] == 50
    assert "branch" not in params


def test_plan_actions_proxima_pagina_uses_pagination_refinement_without_branch(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_intelligence_runtime_access.resolve_chat_intelligence_runtime",
        lambda: type("Runtime", (), {"multi_action_enabled": True})(),
    )
    class Repo:
        actions = [
            {
                "actionId": "parents-action",
                "method": "GET",
                "path": "/products/{code}/parents",
                "operationId": "get_product_parents",
                "summary": "Produtos pai",
                "parametersSchema": [
                    {"name": "code", "in": "path", "required": True},
                    {"name": "page", "in": "query"},
                    {"name": "page_size", "in": "query"},
                ],
            }
        ]

        def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
            return self.actions

    class PaginationSelectionService(FakeSelectionService):
        def __init__(self):
            super().__init__()
            self.pagination_calls = 0
            self._repo = Repo()

        def select_pagination_refinement(
            self,
            refinement,
            *,
            allowed_action_ids,
            message="",
        ):
            self.pagination_calls += 1
            from app.application.services.external_actions.external_action_refinement_route_selection_service import (
                ExternalActionRefinementRouteSelectionService,
            )

            return ExternalActionRefinementRouteSelectionService(self._repo).build_pagination_action(
                refinement,
                action_id=str(refinement.action_id or "parents-action"),
                allowed_action_ids=allowed_action_ids,
            )

    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "parents-action",
                            "parameters": {
                                "code": "10080022",
                                "page": 1,
                                "page_size": 25,
                            },
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/parents",
                            "actionId": "parents-action",
                            "dataCoverageNotice": {"kind": "pagination"},
                        },
                    }
                ]
            },
        },
    ]

    selection_service = PaginationSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        selection_service,
        message="proxima pagina",
        allowed_action_ids=["parents-action"],
        previous_messages=history,
    )

    assert selection_service.pagination_calls == 1
    assert len(planned) == 1
    params = planned[0]["arguments"]["parameters"]
    assert params["code"] == "10080022"
    assert params["page"] == 2
    assert params["page_size"] == 25
    assert "branch" not in params


def test_plan_actions_pagination_follow_up_does_not_fall_back_to_generic_select(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_intelligence_runtime_access.resolve_chat_intelligence_runtime",
        lambda: type("Runtime", (), {"multi_action_enabled": True})(),
    )

    class PaginationSelectionService(FakeSelectionService):
        def __init__(self):
            super().__init__()
            self.pagination_calls = 0
            self.generic_select_calls = 0

        def select_pagination_refinement(
            self,
            refinement,
            *,
            allowed_action_ids,
            message="",
        ):
            self.pagination_calls += 1
            return None

        def select_action(self, *args, **kwargs):
            self.generic_select_calls += 1
            return super().select_action(*args, **kwargs)

    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "parents-action",
                            "parameters": {"code": "10080022", "page": 1, "page_size": 25},
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/parents",
                            "actionId": "parents-action",
                            "dataCoverageNotice": {"kind": "pagination"},
                        },
                    }
                ]
            },
        },
    ]

    selection_service = PaginationSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        selection_service,
        message="próxima página",
        allowed_action_ids=["parents-action"],
        previous_messages=history,
    )

    assert selection_service.pagination_calls == 1
    assert selection_service.generic_select_calls == 0
    assert planned == []
