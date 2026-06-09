"""Bundle document_vision.json — ChatDocumentVisionContentService."""

from app.domain.services.chat_attachment_document_intent_service import (
    ChatAttachmentDocumentIntentService,
)
from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)


def test_read_content_patterns_loaded():
    patterns = ChatDocumentVisionContentService.read_content_patterns()

    assert patterns
    assert any(pattern.search("ler o pdf anexo") for pattern in patterns)


def test_describe_image_patterns_loaded():
    patterns = ChatDocumentVisionContentService.describe_image_patterns()

    assert patterns
    assert any(pattern.search("descreva a foto anexada") for pattern in patterns)


def test_vlm_prompt_describe_image_from_bundle():
    prompt = ChatDocumentVisionContentService.vlm_prompt("describe", is_image=True)

    assert "conteúdo visual" in prompt.lower()


def test_attachment_intent_uses_bundle_patterns():
    assert ChatAttachmentDocumentIntentService.is_document_content_question(
        "extrair texto deste pdf anexo"
    )
    assert ChatAttachmentDocumentIntentService.is_document_content_question(
        "ler a imagem anexada"
    )
    assert not ChatAttachmentDocumentIntentService.is_document_content_question("oi")
