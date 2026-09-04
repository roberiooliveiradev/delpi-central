"""Correção fuzzy não deve reescrever vocabulário de preferência do usuário.

Regressão: «responda curto» virava «responda custo» (distância 1 do termo
operacional «custo»), então a preferência de resposta curta nunca era detectada.
"""

from __future__ import annotations

import pytest

from app.domain.services.chat_behavior_instruction_service import (
    ChatBehaviorInstructionService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


@pytest.mark.parametrize(
    "word",
    ["curto", "curta", "curtos", "curtas", "conciso", "concisa"],
)
def test_preference_adjectives_survive_fuzzy_correction(word: str):
    assert ChatMessageNormalizationService.normalize_for_matching(word) == word


@pytest.mark.parametrize(
    "message",
    [
        "daqui pra frente responda curto",
        "sempre respostas curtas",
        "de agora em diante seja conciso",
    ],
)
def test_short_answer_preference_is_detected(message: str):
    detected = ChatBehaviorInstructionService.detect(message)

    assert detected.get("answerLength") == "short"


def test_operational_typo_still_corrected_to_cost_term():
    assert "custo" in ChatMessageNormalizationService.normalize_for_matching(
        "qual o cust do produto"
    )


@pytest.mark.parametrize("word", ["preciso", "precisa", "precisamos", "precisaria"])
def test_preciso_survives_fuzzy_and_does_not_become_preco(word: str):
    """Regressão: 'Preciso entender a carteira…' virava pricing via preco."""
    text = f"{word} entender a carteira de pedidos"
    normalized = ChatMessageNormalizationService.normalize_for_matching(text)
    assert "preco" not in normalized
    assert word in normalized
    assert "carteira" in normalized
