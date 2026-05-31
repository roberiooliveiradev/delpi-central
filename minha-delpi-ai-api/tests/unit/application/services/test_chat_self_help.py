from unittest.mock import patch

import pytest

from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_help_follow_up_service import ChatHelpFollowUpService
from tests.fixtures.chat_self_help_cases import SELF_HELP_CASES


@pytest.mark.parametrize("case", SELF_HELP_CASES, ids=[item["id"] for item in SELF_HELP_CASES])
def test_self_help_cases(case):
    message = case["message"]
    workspace = case.get("workspace") or {"agent": None, "agentId": None}
    allowed = case.get("allowed_action_ids") or []
    catalog = case.get("action_catalog") or []

    assert ChatCapabilitiesService.is_capability_inquiry(message) is case["expect_capability"]

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

    assert answer, f"{case['id']}: resposta direta ausente"

    lowered = answer.lower()

    assert any(token.lower() in lowered for token in case["expect_substrings"]), (
        f"{case['id']}: resposta não contém termos esperados: {answer[:200]}"
    )

    metadata: dict = {}
    ChatHelpFollowUpService.attach_to_assistant_metadata(metadata, message=message)

    if case["id"] in {"H1", "H3", "H5", "H8", "H9"}:
        assert metadata.get("helpFollowUpSuggestions"), f"{case['id']}: chips de ajuda ausentes"
