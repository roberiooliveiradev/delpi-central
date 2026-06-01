from unittest.mock import patch

import pytest

from app.application.services.assistant_capabilities_catalog_validator import (
    AssistantCapabilitiesCatalogValidator,
)
from app.application.services.chat_assistant_identity_service import (
    ChatAssistantIdentityService,
)
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_help_error_follow_up_service import (
    ChatHelpErrorFollowUpService,
)
from app.application.services.chat_help_follow_up_service import ChatHelpFollowUpService
from tests.fixtures.chat_self_help_cases import SELF_HELP_CASES


@pytest.mark.parametrize("case", SELF_HELP_CASES, ids=[item["id"] for item in SELF_HELP_CASES])
def test_self_help_cases(case):
    message = case["message"]
    workspace = case.get("workspace") or {"agent": None, "agentId": None}
    allowed = case.get("allowed_action_ids") or []
    catalog = case.get("action_catalog") or []

    assert (
        ChatCapabilitiesService.is_capability_inquiry(message) is case["expect_capability"]
    )

    identity_category = case.get("expect_identity_category")

    if identity_category:
        assert ChatAssistantIdentityService.classify(message) == identity_category

    with patch(
        "app.domain.services.chat_web_search_intent_service.ChatWebSearchIntentService.is_feature_enabled",
        return_value=True,
    ):
        answer = ChatCapabilitiesService.resolve_capability_answer(
            message=message,
            workspace_context=workspace,
            allowed_action_ids=allowed,
            action_catalog=catalog,
        )

        if not identity_category:
            assert answer, f"{case['id']}: resposta direta ausente"
        elif answer is None:
            answer = ChatAssistantIdentityService.build_direct_answer(
                message=message,
                workspace_context=workspace,
            )

    assert answer, f"{case['id']}: resposta ausente"

    lowered = answer.lower()

    assert any(token.lower() in lowered for token in case["expect_substrings"]), (
        f"{case['id']}: resposta não contém termos esperados: {answer[:240]}"
    )

    if case.get("expect_context_intro"):
        assert "neste agente" in lowered or "produto" in lowered, (
            f"{case['id']}: intro contextual de agente ausente"
        )

    metadata: dict = {}
    ChatHelpFollowUpService.attach_to_assistant_metadata(metadata, message=message)

    if case.get("expect_chips"):
        assert metadata.get("helpFollowUpSuggestions"), (
            f"{case['id']}: chips de ajuda ausentes"
        )


def test_catalog_validator_blocks_stale_release_notes():
    assert not AssistantCapabilitiesCatalogValidator.validate()


def test_help_error_follow_up_chips():
    metadata: dict = {}
    ChatHelpErrorFollowUpService.attach_to_assistant_metadata(
        metadata,
        message="qual o estoque do produto 1?",
        answer="erro ao consultar a api",
        tool_calls=[],
        issues=["http_500"],
        workspace_context={"agent": {"name": "ERP"}},
    )

    assert metadata.get("helpErrorFollowUpSuggestions")
