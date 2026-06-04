from app.application.services.chat_learning_promotion_gate_service import (
    ChatLearningPromotionGateService,
)
from app.infrastructure.config.settings import Settings


class _FakeEvalRepo:
    def list_active(self, *, categories=None):
        return [
            {
                "id": 1,
                "input": "como vc s chama",
                "expectedIntent": "assistant_identity",
                "mustNotUseTools": True,
                "mustNotUseRag": True,
            }
        ]


class _FakeVocabRepo:
    def list_active_normalization_rules(self, **kwargs):
        return []


def test_gate_blocks_bad_normalization_rule(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_EVALUATION_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_EVALUATION_BLOCK_PROMOTION", True, raising=False)

    gate = ChatLearningPromotionGateService(
        evaluation_repository=_FakeEvalRepo(),
        vocabulary_repository=_FakeVocabRepo(),
    )

    # Após typos estáticos, "como vc s chama" vira "como voce se chama"; a regra ruim
    # substitui essa forma e quebra o roteamento de identidade.
    result = gate.validate_promotion(
        {
            "candidateType": "normalization_rule",
            "inputText": "como vc s chama",
            "proposedRule": "estoque do produto 10080001",
        },
        term_override="como voce se chama",
        normalized_override="estoque do produto 10080001",
    )

    assert result["allowed"] is False
    assert result.get("failures")


def test_gate_disabled_allows(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_EVALUATION_ENABLED", False, raising=False)

    gate = ChatLearningPromotionGateService(
        evaluation_repository=_FakeEvalRepo(),
        vocabulary_repository=_FakeVocabRepo(),
    )

    assert gate.validate_promotion({"candidateType": "normalization_rule"})["allowed"] is True
