"""Testes do loader de padrões de referência vaga."""

from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_reference_resolution_content_service import (
    ChatReferenceResolutionContentService,
)


def test_reference_resolution_patterns_compile():
    assert ChatReferenceResolutionContentService.compile_pattern("productRef").search(
        "esse produto"
    )
    assert ChatReferenceResolutionContentService.compile_pattern("sameBranch").search(
        "mesma filial"
    )
    assert "isso" in ChatReferenceResolutionContentService.ambiguity_text(
        "thisReferencePromptHint"
    ).lower()
