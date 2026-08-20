"""Regressão E2.S1 — matriz de famílias (web / text / API / skills)."""

from __future__ import annotations

import pytest

from app.application.services.chat_agent_skills_service import ChatAgentSkillsService
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
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

configure_domain_infrastructure_ports()


@pytest.mark.parametrize(
    "case",
    FLOW_FAMILY_MATRIX_CASES,
    ids=[str(item["id"]) for item in FLOW_FAMILY_MATRIX_CASES],
)
def test_flow_family_matrix_gates(case: dict):
    message = str(case["message"])
    expects = case["expects"]
    skills = case.get("skills")

    if "web_explicit" in expects:
        assert ChatWebSearchIntentService.is_explicit_request(message) is expects[
            "web_explicit"
        ]

    if "blocks_external_action" in expects:
        assert (
            ChatWebSearchIntentService.blocks_external_action_selection(message)
            is expects["blocks_external_action"]
        )

    if "text_task_pure" in expects:
        assert ChatTextTaskIntentService.is_pure_text_task(message) is expects[
            "text_task_pure"
        ]

    if "text_correction" in expects:
        assert ChatTextCorrectionIntentService.is_text_correction(message) is expects[
            "text_correction"
        ]

    if "operational_data_request" in expects:
        assert (
            ChatCapabilitiesService.looks_like_operational_data_request(message)
            is expects["operational_data_request"]
        )

    if "retry_or_continue" in expects:
        assert ChatFollowUpIntentService.is_retry_or_continue_request(message) is expects[
            "retry_or_continue"
        ]

    if "preserves_rag_on_fast_path" in expects:
        assert ChatAgentSkillsService.preserves_rag_on_fast_path(skills) is expects[
            "preserves_rag_on_fast_path"
        ]

    if "multi_scope_intent" in expects:
        intent = ChatProductQueryIntentService.detect(message)
        assert (intent == ChatProductQueryIntent.MULTI_SCOPE) is expects[
            "multi_scope_intent"
        ]


def test_flow_family_matrix_covers_required_families():
    families = {str(item["family"]) for item in FLOW_FAMILY_MATRIX_CASES}

    assert "web" in families
    assert "text_task" in families
    assert "operational_api" in families
    assert "skill_company_knowledge" in families
