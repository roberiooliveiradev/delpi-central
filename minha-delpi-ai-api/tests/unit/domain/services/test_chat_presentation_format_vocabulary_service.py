from app.domain.services.chat_presentation_format_vocabulary_service import (
    ChatPresentationFormatVocabularyService,
)


def test_format_vocabulary_table_hints_loaded_from_json():
    hints = ChatPresentationFormatVocabularyService.table_hints()

    assert "em tabela" in hints
    assert "coloque em uma tabela" in hints


def test_format_vocabulary_tool_context_merges_extra_table_hints():
    base = ChatPresentationFormatVocabularyService.table_hints()
    merged = ChatPresentationFormatVocabularyService.table_hints(include_tool_context=True)

    assert len(merged) >= len(base)
    assert "tabela completa" in merged
