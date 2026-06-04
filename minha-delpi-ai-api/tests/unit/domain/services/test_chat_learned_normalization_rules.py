from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


def teardown_function(_):
    ChatMessageNormalizationService.clear_learned_rules()


def test_learned_rule_applied_after_static():
    ChatMessageNormalizationService.set_learned_rules([("transforma", "modulo de engenharia")])

    result = ChatMessageNormalizationService.normalize_for_matching("falar do transforma")

    assert "modulo de engenharia" in result
    assert "transforma" not in result


def test_learned_rule_ignores_noop_and_invalid():
    ChatMessageNormalizationService.set_learned_rules(
        [("igual", "igual"), ("", "x"), ("y", "")]
    )

    # Nenhuma regra válida aplicada.
    assert ChatMessageNormalizationService.normalize_for_matching("igual") == "igual"


def test_clear_learned_rules_restores_static_behavior():
    ChatMessageNormalizationService.set_learned_rules([("foo", "bar")])
    ChatMessageNormalizationService.clear_learned_rules()

    assert ChatMessageNormalizationService.normalize_for_matching("foo") == "foo"
