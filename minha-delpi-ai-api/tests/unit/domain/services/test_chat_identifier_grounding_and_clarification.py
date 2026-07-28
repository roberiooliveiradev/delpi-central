"""Grounding e clarificação de identificador não-canônico."""

from __future__ import annotations

import json

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_identifier_resolution_service import (
    ChatOperationalIdentifierResolutionService,
)
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_clarification_when_part_number_hint_without_token() -> None:
    answer = ChatOperationalIdentifierResolutionService.resolve_clarification_answer(
        "liste produto com part number do fornecedor"
    )
    assert answer
    assert "part number" in answer.lower()


def test_classify_supplier_part_number_lookup_sub_intent() -> None:
    from app.domain.services.chat_intent_router_service import ChatIntentRouterService

    route = ChatIntentRouterService.classify(
        "liste produto com part number do fornecedor 008700056"
    )
    assert route.sub_intent == "product_by_supplier_part_number"
    assert route.resolved_params == {"supplierPartNumber": "008700056"}


def test_post_turn_does_not_store_supplier_part_number_as_product_code() -> None:
    snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
        message="liste produto com part number do fornecedor 008700056",
        previous_messages=[],
        tool_calls=[],
        pre_snapshot={},
    )
    focus = snapshot.get("operationalFocus") or {}
    assert focus.get("productCode") != "008700056"


def test_post_turn_promotes_product_code_from_supplier_part_number_result() -> None:
    preview = {
        "success": True,
        "data": {
            "items": [
                {
                    "product_code": "10080160",
                    "supplier_part_number": "008700056",
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 50,
        },
    }
    tool_calls = [
        {
            "name": "execute_external_action",
            "arguments": {
                "actionId": "api_delpi.products.search_products_by_supplier_part_number",
                "parameters": {
                    "supplier_part_number": "008700056",
                    "page": 1,
                    "page_size": 50,
                },
            },
            "metadata": {
                "path": "/products/by-supplier-part-number",
                "responsePreview": json.dumps(preview),
            },
        }
    ]
    snapshot = ChatWorkingMemoryService.build_post_turn_snapshot(
        message="liste produto com part number do fornecedor 008700056",
        previous_messages=[],
        tool_calls=tool_calls,
        pre_snapshot={},
    )
    focus = snapshot.get("operationalFocus") or {}
    assert focus.get("productCode") == "10080160"
