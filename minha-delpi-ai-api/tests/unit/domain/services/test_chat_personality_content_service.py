from app.domain.services.chat_personality_content_service import ChatPersonalityContentService
from app.infrastructure.content.content_service import ContentService


def test_pick_phrase_is_deterministic_for_same_seed():
    first = ChatPersonalityContentService.pick_phrase("start", seed="sessao-1")
    second = ChatPersonalityContentService.pick_phrase("start", seed="sessao-1")
    third = ChatPersonalityContentService.pick_phrase("start", seed="sessao-2")

    assert first
    assert first == second
    assert third


def test_pick_variant_from_small_talk_content():
    content = ContentService.load_json("assistant/small_talk")
    variants = content.get("responseVariants") or {}

    answer = ChatPersonalityContentService.pick_variant(
        variants,
        scope="platform",
        category="greeting",
        seed="ola",
    )

    assert "olá" in answer.lower() or "oi" in answer.lower()


def test_personality_playbook_loads_home_starters():
    playbook = ContentService.personality_playbook()

    starters = playbook.get("homeStarters") or []

    assert len(starters) >= 4
    assert starters[0].get("label")
    assert starters[0].get("query")
