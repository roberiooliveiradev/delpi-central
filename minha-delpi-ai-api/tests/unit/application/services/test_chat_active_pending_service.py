from app.application.services.chat_active_pending_service import (
    ChatActivePendingService,
)
from app.domain.services.chat_intent_router_service import ChatIntentRouterService


def test_find_active_pending_from_assistant_metadata():
    history = [
        {
            "role": "assistant",
            "content": "Informe o código.",
            "metadata": {
                "activePending": {
                    "kind": "missing_product_code",
                    "expectedParam": "productCode",
                }
            },
        },
    ]

    pending = ChatActivePendingService.find_from_messages(history)

    assert pending is not None
    assert pending["kind"] == "missing_product_code"


def test_try_resolve_product_code_from_short_reply():
    pending = {"kind": "missing_product_code", "expectedParam": "productCode"}

    resolved = ChatActivePendingService.try_resolve("10080099", pending)

    assert resolved is not None
    assert resolved["resolvedParams"]["productCode"] == "10080099"
    assert resolved["requiresTool"] is True


def test_try_resolve_does_not_bind_year_as_product_code():
    pending = {"kind": "missing_product_code", "expectedParam": "productCode"}

    resolved = ChatActivePendingService.try_resolve(
        "Vendas por mês em 2026",
        pending,
    )

    assert resolved is None


def test_classify_resolves_active_pending_before_operational():
    history = [
        {"role": "user", "content": "qual o estoque do produto?"},
        {
            "role": "assistant",
            "content": "Informe o código.",
            "metadata": {
                "activePending": {
                    "kind": "missing_product_code",
                    "expectedParam": "productCode",
                }
            },
        },
    ]

    route = ChatIntentRouterService.classify(
        "10080099",
        previous_messages=history,
    )

    assert route.intent == "clarification"
    assert route.sub_intent == "missing_product_code"
    assert route.resolved_params == {"productCode": "10080099"}
    assert "active_pending_resolved" in route.flags


def test_classify_does_not_inherit_product_code_for_ranking_query():
    history = [
        {
            "role": "assistant",
            "content": "Resultado",
            "metadata": {
                "memory": {"operationalFocus": {"productCode": "2026"}},
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/2026/sales",
                        },
                    }
                ],
            },
        },
    ]

    route = ChatIntentRouterService.classify(
        "Ranking dos 10 clientes que mais compraram",
        previous_messages=history,
        workspace_context={
            "workingMemory": {"operationalFocus": {"productCode": "2026"}},
        },
    )

    assert route.resolved_params is None or route.resolved_params.get("productCode") != "2026"


def test_routing_snapshot_from_admin_debug():
    meta = {
        "adminDebug": {
            "intentRoute": {
                "intent": "operational_query",
                "subIntent": "stock_lookup",
            }
        }
    }

    snapshot = ChatActivePendingService.routing_snapshot_from_assistant_metadata(meta)

    assert snapshot == {
        "intent": "operational_query",
        "subIntent": "stock_lookup",
    }


def test_should_attach_routing_snapshot_for_wrong_intent():
    assert ChatActivePendingService.should_attach_routing_snapshot("wrong_intent")
    assert not ChatActivePendingService.should_attach_routing_snapshot("too_long")
