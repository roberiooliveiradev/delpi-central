"""Formatação de OCR e descrição visual — ChatDocumentVisionContextService."""

from app.domain.services.chat_document_vision_context_service import (
    ChatDocumentVisionContextService,
)


def test_format_vision_block_includes_description_and_text():
    block = ChatDocumentVisionContextService.format_vision_block(
        {
            "textExcerpt": "LINHA 1",
            "imageDescription": "Foto de um painel elétrico.",
            "filename": "foto.png",
        }
    )

    assert "Descrição visual" in block
    assert "painel elétrico" in block
    assert "Texto extraído" in block
    assert "LINHA 1" in block
    assert "foto.png" in block


def test_enrich_tool_context_appends_block_to_context():
    enriched = ChatDocumentVisionContextService.enrich_tool_context(
        {
            "context": "Contexto existente",
            "documentVision": {
                "imageDescription": "Uma máquina industrial verde.",
            },
        }
    )

    assert "Contexto existente" in enriched["context"]
    assert "máquina industrial" in enriched["context"]
