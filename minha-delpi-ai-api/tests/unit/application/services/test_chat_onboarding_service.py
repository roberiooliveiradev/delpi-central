from app.application.services.chat_onboarding_service import ChatOnboardingService


def test_training_request_detected():
    assert ChatOnboardingService.is_training_request("me ensine a usar")
    assert ChatOnboardingService.is_training_request("Me ensine a usar o chat")


def test_training_request_not_operational():
    assert not ChatOnboardingService.is_training_request(
        "qual o estoque do produto 10080001?"
    )


def test_build_training_answer_has_sections():
    answer = ChatOnboardingService.build_training_answer()

    assert "Guia rápido" in answer
    assert "Consultas operacionais" in answer
    assert "Agentes" in answer


def test_payload_for_catalog():
    payload = ChatOnboardingService.payload_for_catalog()

    assert payload["welcome"]["title"]
    assert len(payload["starterCards"]) >= 5
    assert len(payload["tourSteps"]) == 5


def test_starter_cards_have_queries():
    cards = ChatOnboardingService.starter_cards()

    assert all(card.get("query") for card in cards)
