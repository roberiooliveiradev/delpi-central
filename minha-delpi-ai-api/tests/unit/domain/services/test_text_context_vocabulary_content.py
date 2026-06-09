from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_text_context_resolver_service import (
    ChatTextContextResolverService,
)
from app.domain.services.chat_text_context_vocabulary_service import (
    ChatTextContextVocabularyService,
)


def test_text_context_vocabulary_bundle_has_core_sections():
    assert ChatTextContextVocabularyService.terms("previousReferenceTerms")
    assert ChatTextContextVocabularyService.text("promptBlock", "canvasSource")


def test_previous_reference_from_json():
    resolved = ChatTextContextResolverService.resolve(
        "revise a resposta anterior com tom formal"
    )

    assert resolved["referencesPrevious"] is True
