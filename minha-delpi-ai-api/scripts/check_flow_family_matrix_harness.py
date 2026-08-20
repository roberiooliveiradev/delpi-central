#!/usr/bin/env python3
"""Harness E5 — percorre FLOW_FAMILY_MATRIX_CASES e falha se gate divergir.

Uso:
  cd minha-delpi-ai-api
  PYTHONPATH=. .venv/bin/python scripts/check_flow_family_matrix_harness.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.application.services.chat_agent_skills_service import ChatAgentSkillsService
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_conversation_message_search_service import (
    ChatConversationMessageSearchService,
)
from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService
from tests.fixtures.chat_intelligence_regression_cases import FLOW_FAMILY_MATRIX_CASES


REQUIRED_FAMILIES = {
    "web",
    "text_task",
    "operational_api",
    "skill_company_knowledge",
    "message_search",
}


def _check_case(case: dict) -> list[str]:
    errors: list[str] = []
    message = str(case["message"])
    expects = case.get("expects") or {}
    skills = case.get("skills")
    case_id = str(case.get("id") or "?")

    def _fail(label: str, actual, expected) -> None:
        errors.append(f"{case_id}: {label} actual={actual!r} expected={expected!r}")

    if "web_explicit" in expects:
        actual = ChatWebSearchIntentService.is_explicit_request(message)
        if actual is not expects["web_explicit"]:
            _fail("web_explicit", actual, expects["web_explicit"])

    if "blocks_external_action" in expects:
        actual = ChatWebSearchIntentService.blocks_external_action_selection(message)
        if actual is not expects["blocks_external_action"]:
            _fail("blocks_external_action", actual, expects["blocks_external_action"])

    if "text_task_pure" in expects:
        actual = ChatTextTaskIntentService.is_pure_text_task(message)
        if actual is not expects["text_task_pure"]:
            _fail("text_task_pure", actual, expects["text_task_pure"])

    if "text_correction" in expects:
        actual = ChatTextCorrectionIntentService.is_text_correction(message)
        if actual is not expects["text_correction"]:
            _fail("text_correction", actual, expects["text_correction"])

    if "operational_data_request" in expects:
        actual = ChatCapabilitiesService.looks_like_operational_data_request(message)
        if actual is not expects["operational_data_request"]:
            _fail(
                "operational_data_request",
                actual,
                expects["operational_data_request"],
            )

    if "retry_or_continue" in expects:
        actual = ChatFollowUpIntentService.is_retry_or_continue_request(message)
        if actual is not expects["retry_or_continue"]:
            _fail("retry_or_continue", actual, expects["retry_or_continue"])

    if "preserves_rag_on_fast_path" in expects:
        actual = ChatAgentSkillsService.preserves_rag_on_fast_path(skills)
        if actual is not expects["preserves_rag_on_fast_path"]:
            _fail(
                "preserves_rag_on_fast_path",
                actual,
                expects["preserves_rag_on_fast_path"],
            )

    if "multi_scope_intent" in expects:
        intent = ChatProductQueryIntentService.detect(message)
        actual = intent == ChatProductQueryIntent.MULTI_SCOPE
        if actual is not expects["multi_scope_intent"]:
            _fail("multi_scope_intent", actual, expects["multi_scope_intent"])

    if "session_review" in expects:
        actual = ChatConversationMessageSearchService.is_session_review_request(message)
        if actual is not expects["session_review"]:
            _fail("session_review", actual, expects["session_review"])

    if "intent" in expects:
        route = ChatIntentRouterService.classify(
            message,
            previous_messages=case.get("history"),
            workspace_context=case.get("workspace_context"),
            allowed_action_ids=case.get("allowed_action_ids") or ["action-1"],
        )
        if route.intent != expects["intent"]:
            _fail("intent", route.intent, expects["intent"])
        if "requires_tool" in expects and route.requires_tool is not expects["requires_tool"]:
            _fail("requires_tool", route.requires_tool, expects["requires_tool"])

    return errors


def main() -> int:
    configure_domain_infrastructure_ports()
    families = {str(item.get("family") or "") for item in FLOW_FAMILY_MATRIX_CASES}
    missing = REQUIRED_FAMILIES - families
    if missing:
        print(f"FAIL missing families: {sorted(missing)}", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for case in FLOW_FAMILY_MATRIX_CASES:
        all_errors.extend(_check_case(case))

    if all_errors:
        for line in all_errors:
            print(f"FAIL {line}", file=sys.stderr)
        print(f"check_flow_family_matrix_harness: {len(all_errors)} error(s)", file=sys.stderr)
        return 1

    print(
        f"OK check_flow_family_matrix_harness "
        f"({len(FLOW_FAMILY_MATRIX_CASES)} cases, families={sorted(families)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
