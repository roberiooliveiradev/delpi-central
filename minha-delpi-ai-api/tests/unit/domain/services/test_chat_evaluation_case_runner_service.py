from app.domain.services.chat_evaluation_case_runner_service import (
    ChatEvaluationCaseRunnerService,
)


def test_passes_assistant_identity_intent():
    result = ChatEvaluationCaseRunnerService.run(
        {
            "input": "como vc s chama?",
            "expectedIntent": "assistant_identity",
            "mustNotUseTools": True,
            "mustNotUseRag": True,
        }
    )

    assert result.passed is True


def test_fails_wrong_intent():
    result = ChatEvaluationCaseRunnerService.run(
        {
            "input": "estoque do produto 10080001",
            "expectedIntent": "small_talk",
        }
    )

    assert result.passed is False
    assert any("intenção" in failure for failure in result.failures)


def test_expected_normalized_after_typo_rule():
    from app.domain.services.chat_message_normalization_service import (
        ChatMessageNormalizationService,
    )

    ChatMessageNormalizationService.set_learned_rules([("como vc s chama", "como voce se chama")])

    try:
        result = ChatEvaluationCaseRunnerService.run(
            {
                "input": "como vc s chama?",
                "expectedNormalized": "como voce se chama?",
            }
        )
        assert result.passed is True
    finally:
        ChatMessageNormalizationService.clear_learned_rules()
