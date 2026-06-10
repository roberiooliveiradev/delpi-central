from app.domain.services.chat_learning_term_ambiguity_service import (
    ChatLearningTermAmbiguityService,
)


def test_needs_confirmation_for_low_confidence():
    assert ChatLearningTermAmbiguityService.needs_confirmation(0.3) is True
    assert ChatLearningTermAmbiguityService.needs_confirmation(0.49) is True
    assert ChatLearningTermAmbiguityService.needs_confirmation(0.5) is False


def test_parse_confirmation_reply():
    assert ChatLearningTermAmbiguityService.parse_confirmation_reply("sim") == "confirm"
    assert ChatLearningTermAmbiguityService.parse_confirmation_reply("não") == "reject"


def test_extract_explicit_meaning_for_pending_term():
    meaning = ChatLearningTermAmbiguityService.extract_explicit_meaning_for_term(
        "OP significa ordem de produção",
        term="OP",
    )
    assert meaning == "ordem de produção"


def test_build_pending_patch_roundtrip():
    patch = ChatLearningTermAmbiguityService.build_pending_patch(
        term="OP",
        proposed_meaning="ordem de produção",
        confidence=0.35,
        sources=["https://example.com"],
    )
    pending = ChatLearningTermAmbiguityService.get_pending(patch)
    assert pending is not None
    assert pending["term"] == "OP"
    assert pending["proposedMeaning"] == "ordem de produção"
