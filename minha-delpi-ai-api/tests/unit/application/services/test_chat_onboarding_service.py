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
    assert len(payload["profiles"]) >= 5
    assert len(payload["milestones"]) >= 4


def test_engineering_profile_cards():
    cards = ChatOnboardingService.starter_cards(profile_id="engineering")

    assert any("estrutura" in card["query"].lower() or "usado" in card["query"].lower() for card in cards)


def test_infer_profile_from_agent_name():
    profile = ChatOnboardingService.infer_profile_from_agent(
        agent_name="Agente de Compras",
        agent_category=None,
    )

    assert profile == "purchases"


def test_explicit_profile_overrides_agent():
    resolved = ChatOnboardingService.resolve_profile_id(
        profile_id="commercial",
        agent_name="Agente de Compras",
    )

    assert resolved == "commercial"


def test_starter_cards_have_queries():
    cards = ChatOnboardingService.starter_cards()

    assert all(card.get("query") for card in cards)
