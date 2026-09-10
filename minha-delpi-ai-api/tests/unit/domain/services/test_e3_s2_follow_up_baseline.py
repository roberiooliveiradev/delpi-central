"""E3.S2 — baseline freeze: follow-up / refinement / reference signals.

Does not cut over authority. Freezes observable multi-turn signals for families
required by plano 03 (shipping, branch filter, pagination, group_by, compare,
same product, topic switch, ordinal resolve, ambiguity).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_operational_follow_up_routing_service import (
    ChatOperationalFollowUpRoutingService,
)
from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)
from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)
from app.domain.services.chat_result_set_reference_service import (
    ChatResultSetReferenceService,
)


def _stock_previous_messages() -> list[dict[str, Any]]:
    return [
        {
            "role": "assistant",
            "content": "ok",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "acme.products.stock",
                            "parameters": {
                                "page": 1,
                                "page_size": 20,
                                "code": "10080001",
                                "branch": "01",
                            },
                        },
                        "metadata": {
                            "path": "/products/10080001/stock",
                            "actionId": "acme.products.stock",
                            "ok": True,
                        },
                    }
                ],
                "selectedExternalAction": {
                    "actionId": "acme.products.stock",
                    "path": "/products/10080001/stock",
                    "parameters": {
                        "page": 1,
                        "page_size": 20,
                        "code": "10080001",
                        "branch": "01",
                    },
                },
            },
        }
    ]


def _production_previous_messages() -> list[dict[str, Any]]:
    return [
        {
            "role": "assistant",
            "content": "ok",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "production-consumption-top-items",
                            "parameters": {
                                "group_by": "general",
                                "page": 1,
                                "page_size": 20,
                            },
                        },
                        "metadata": {
                            "path": "/production/consumption/top-items",
                            "actionId": "production-consumption-top-items",
                            "ok": True,
                        },
                    }
                ],
                "selectedExternalAction": {
                    "actionId": "production-consumption-top-items",
                    "path": "/production/consumption/top-items",
                    "parameters": {"group_by": "general"},
                },
            },
        }
    ]


def _search_tool_call() -> dict[str, Any]:
    return {
        "name": "execute_external_action",
        "arguments": {"parameters": {"description": "terminal pino"}},
        "metadata": {
            "ok": True,
            "operationId": "search_products",
            "path": "/products/search",
            "tablePresentations": [
                {
                    "title": "Produtos encontrados",
                    "rows": [
                        {"product_code": "10080001", "description": "TERMINAL PINO 6MM"},
                        {"product_code": "10080002", "description": "TERMINAL PINO 8MM"},
                        {"product_code": "10080003", "description": "TERMINAL PINO 10MM"},
                        {"product_code": "10080004", "description": "TERMINAL PINO 12MM"},
                    ],
                }
            ],
        },
    }


@dataclass(frozen=True)
class FollowUpBaselineCase:
    family: str
    message: str
    follow_segment: str | None
    follow_up_type: str | None
    intent: str
    sub_intent: str | None
    refinement_kind: str | None
    branch: str | None
    page: int | None
    page_size: int | None
    group_by: str | None
    playbook_date: bool | None
    ambiguity_reason: str | None
    ordinal_code: str | None


# Frozen 2026-09-10 against HEAD follow-up / refinement / reference services.
_CORPUS: tuple[FollowUpBaselineCase, ...] = (
    FollowUpBaselineCase(
        family="shipping_followup",
        message="e a expedição?",
        follow_segment="shipping-status",
        follow_up_type="shipping",
        intent="operational_query",
        sub_intent="shipping_status_lookup",
        refinement_kind=None,
        branch=None,
        page=None,
        page_size=None,
        group_by=None,
        playbook_date=True,
        ambiguity_reason=None,
        ordinal_code=None,
    ),
    FollowUpBaselineCase(
        family="branch_filter",
        message="agora só filial 02",
        follow_segment=None,
        follow_up_type="entity_reuse",
        intent="operational_query",
        sub_intent=None,
        refinement_kind="stock_refinement",
        branch="02",
        page=None,
        page_size=None,
        group_by=None,
        playbook_date=None,
        ambiguity_reason=None,
        ordinal_code=None,
    ),
    FollowUpBaselineCase(
        family="next_page",
        message="próxima página",
        follow_segment=None,
        follow_up_type=None,
        intent="llm_general",
        sub_intent=None,
        refinement_kind="pagination_refinement",
        branch=None,
        page=2,
        page_size=None,
        group_by=None,
        playbook_date=None,
        ambiguity_reason=None,
        ordinal_code=None,
    ),
    FollowUpBaselineCase(
        family="page_size_100",
        message="traga 100 linhas",
        follow_segment=None,
        follow_up_type=None,
        intent="operational_query",
        sub_intent="product_search",
        refinement_kind="pagination_refinement",
        branch=None,
        page=None,
        page_size=100,
        group_by=None,
        playbook_date=None,
        ambiguity_reason=None,
        ordinal_code=None,
    ),
    FollowUpBaselineCase(
        family="group_by_branch",
        message="agrupe por filial",
        follow_segment=None,
        follow_up_type=None,
        intent="operational_query",
        sub_intent=None,
        refinement_kind="operational_group_by_refinement",
        branch=None,
        page=None,
        page_size=None,
        group_by="branch_summary",
        playbook_date=None,
        ambiguity_reason=None,
        ordinal_code=None,
    ),
    FollowUpBaselineCase(
        family="compare_month",
        message="compare com o mês anterior",
        follow_segment=None,
        follow_up_type="entity_reuse",
        intent="text_task",
        sub_intent="compare",
        refinement_kind=None,
        branch=None,
        page=None,
        page_size=None,
        group_by=None,
        playbook_date=None,
        ambiguity_reason=None,
        ordinal_code=None,
    ),
    FollowUpBaselineCase(
        family="same_product",
        message="use o mesmo produto",
        follow_segment=None,
        follow_up_type=None,
        intent="operational_query",
        sub_intent="product_lookup",
        refinement_kind=None,
        branch=None,
        page=None,
        page_size=None,
        group_by=None,
        playbook_date=None,
        ambiguity_reason=None,
        ordinal_code=None,
    ),
    FollowUpBaselineCase(
        family="topic_switch_rag",
        message="agora fale sobre política de férias",
        follow_segment=None,
        follow_up_type="entity_reuse",
        intent="rag_question",
        sub_intent=None,
        refinement_kind=None,
        branch=None,
        page=None,
        page_size=None,
        group_by=None,
        playbook_date=None,
        ambiguity_reason=None,
        ordinal_code=None,
    ),
    FollowUpBaselineCase(
        family="ordinal_resolve",
        message="estoque do segundo",
        follow_segment=None,
        follow_up_type="stock",
        intent="operational_query",
        sub_intent="stock_lookup",
        refinement_kind=None,
        branch=None,
        page=None,
        page_size=None,
        group_by=None,
        playbook_date=None,
        ambiguity_reason=None,
        ordinal_code="10080002",
    ),
    FollowUpBaselineCase(
        family="ambiguous_compare_previous",
        message="compare com o anterior",
        follow_segment=None,
        follow_up_type="entity_reuse",
        intent="text_task",
        sub_intent="compare",
        refinement_kind=None,
        branch=None,
        page=None,
        page_size=None,
        group_by=None,
        playbook_date=None,
        ambiguity_reason="compare_previous",
        ordinal_code=None,
    ),
)


def _first_refinement(
    message: str,
    *,
    previous_messages: list[dict[str, Any]],
) -> Any | None:
    for planner in (
        ChatOperationalRefinementService.plan_pagination_follow_ups,
        ChatOperationalRefinementService.plan_stock_follow_ups,
        ChatOperationalRefinementService.plan_operational_group_by_follow_ups,
        ChatOperationalRefinementService.plan_operational_follow_ups,
    ):
        planned = planner(message, previous_messages=previous_messages)
        if planned:
            return planned[0]
    return None


def _observe(case: FollowUpBaselineCase) -> dict[str, Any]:
    previous = (
        _production_previous_messages()
        if case.family == "group_by_branch"
        else _stock_previous_messages()
    )
    route = ChatIntentRouterService.classify(case.message)
    refinement = _first_refinement(case.message, previous_messages=previous)

    ambiguity_reason = None
    if case.family == "ambiguous_compare_previous":
        ambiguity = ChatReferenceResolutionService.detect_ambiguity(
            case.message,
            {
                "operationalFocus": {"productCode": "10080001"},
                "previousProductCodes": ["10080002", "10080003"],
            },
        )
        ambiguity_reason = None if ambiguity is None else ambiguity.get("reason")

    ordinal_code = None
    if case.family == "ordinal_resolve":
        snapshot = {
            "resultSets": ChatResultSetReferenceService.build_result_sets(
                tool_calls=[_search_tool_call()],
            ),
        }
        codes = ChatResultSetReferenceService.resolve_codes(case.message, snapshot)
        ordinal_code = codes[0] if codes else None

    playbook_date = None
    if case.family == "shipping_followup":
        playbook_date = (
            ChatOperationalFollowUpRoutingService.looks_like_playbook_date_follow_up(
                case.message
            )
        )

    return {
        "follow_segment": ChatOperationalFollowUpRoutingService.segment_from_message(
            case.message
        ),
        "follow_up_type": ChatFollowUpIntentService.follow_up_type(case.message),
        "intent": route.intent,
        "sub_intent": route.sub_intent,
        "refinement_kind": None if refinement is None else refinement.kind,
        "branch": None if refinement is None else refinement.branch,
        "page": None if refinement is None else refinement.page,
        "page_size": None if refinement is None else refinement.page_size,
        "group_by": None if refinement is None else refinement.group_by,
        "playbook_date": playbook_date,
        "ambiguity_reason": ambiguity_reason,
        "ordinal_code": ordinal_code,
    }


def test_e3_s2_baseline_corpus_covers_required_families():
    families = {case.family for case in _CORPUS}
    required = {
        "shipping_followup",
        "branch_filter",
        "next_page",
        "page_size_100",
        "group_by_branch",
        "compare_month",
        "same_product",
        "topic_switch_rag",
        "ordinal_resolve",
        "ambiguous_compare_previous",
    }
    assert required <= families
    assert len(_CORPUS) >= 9


def test_e3_s2_follow_up_signals_match_frozen_baseline():
    mismatches: list[tuple[str, dict, dict]] = []
    for case in _CORPUS:
        observed = _observe(case)
        expected = {
            "follow_segment": case.follow_segment,
            "follow_up_type": case.follow_up_type,
            "intent": case.intent,
            "sub_intent": case.sub_intent,
            "refinement_kind": case.refinement_kind,
            "branch": case.branch,
            "page": case.page,
            "page_size": case.page_size,
            "group_by": case.group_by,
            "playbook_date": case.playbook_date,
            "ambiguity_reason": case.ambiguity_reason,
            "ordinal_code": case.ordinal_code,
        }
        if observed != expected:
            mismatches.append((case.family, expected, observed))
    assert not mismatches, mismatches


def test_e3_s2_shipping_sibling_blocks_semantic_fallback():
    assert (
        ChatOperationalFollowUpRoutingService.should_block_semantic_fallback(
            "e a expedição?"
        )
        is True
    )


def test_e3_s2_group_by_negative_without_matching_path():
    planned = ChatOperationalRefinementService.plan_operational_group_by_follow_ups(
        "agrupe por filial",
        previous_messages=_stock_previous_messages(),
    )
    assert planned == []


def test_e3_s2_ordinal_negative_without_result_sets():
    codes = ChatResultSetReferenceService.resolve_codes(
        "estoque do segundo",
        {"operationalFocus": {}},
    )
    assert codes == []
