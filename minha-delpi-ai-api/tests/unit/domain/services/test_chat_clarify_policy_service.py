from app.domain.services.chat_clarify_policy_service import (
    ChatClarifyPolicyKind,
    ChatClarifyPolicyService,
)
from app.domain.services.chat_turn_grounding_service import (
    ChatTurnGrounding,
    ChatTurnGroundingStatus,
)


def _grounded() -> ChatTurnGrounding:
    return ChatTurnGrounding(
        status=ChatTurnGroundingStatus.GROUNDED,
        reason="last_result_excerpt",
        referring_label="Estrutura 90260149 · 6 itens",
    )


def test_resolve_none_when_grounded():
    policy = ChatClarifyPolicyService.resolve(_grounded())

    assert policy.kind == ChatClarifyPolicyKind.NONE
    assert policy.answer is None


def test_resolve_slot_when_missing_parameter():
    policy = ChatClarifyPolicyService.resolve(
        ChatTurnGrounding(
            status=ChatTurnGroundingStatus.UNGROUNDED,
            reason="no_referent",
        ),
        missing_slot_answer="Informe o código do produto.",
    )

    assert policy.kind == ChatClarifyPolicyKind.SLOT
    assert policy.answer == "Informe o código do produto."


def test_resolve_ungrounded_without_slot():
    policy = ChatClarifyPolicyService.resolve(
        ChatTurnGrounding(
            status=ChatTurnGroundingStatus.UNGROUNDED,
            reason="no_referent",
        )
    )

    assert policy.kind == ChatClarifyPolicyKind.UNGROUNDED
