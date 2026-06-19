"""Bundle learning_content.json — ChatLearningContentService."""

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_learning_content_service import ChatLearningContentService

configure_domain_infrastructure_ports()


def test_learning_content_term_confirmation_templates():
    assert ChatLearningContentService.format(
        "termConfirmation",
        "knownDefinition",
        term="OP",
        meaning="ordem de produção",
    )


def test_learning_content_patterns_compile():
    assert ChatLearningContentService.compile_pattern("explicitWhen").search(
        "quando eu falar TRANSFORMA, estou falando do módulo"
    )
    assert ChatLearningContentService.compile_pattern_list("secretPatterns")
    assert ChatLearningContentService.setting_float("confirmationThreshold", 0.5) == 0.5


def test_learning_content_term_meaning_pattern():
    pattern = ChatLearningContentService.compile_term_meaning_pattern("OP")
    match = pattern.match("OP significa ordem de produção")

    assert match
    assert match.group("meaning") == "ordem de produção"
