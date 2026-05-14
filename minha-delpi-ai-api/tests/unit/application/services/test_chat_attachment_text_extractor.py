from app.application.services.chat_attachment_text_extractor import (
    ChatAttachmentTextExtractor,
)


def test_supported_extensions_include_knowledge_document_formats():
    assert ChatAttachmentTextExtractor.supported_extensions() == {
        ".txt",
        ".md",
        ".markdown",
        ".csv",
        ".json",
        ".docx",
        ".xlsx",
        ".pdf",
    }


def test_extract_markdown_file(tmp_path):
    path = tmp_path / "manual.md"
    path.write_text("# Manual\n\nConteúdo de teste.", encoding="utf-8")

    result = ChatAttachmentTextExtractor().extract(
        storage_path=str(path),
        filename="manual.md",
        content_type="text/markdown",
    )

    assert result["supported"] is True
    assert result["content"] == "# Manual\n\nConteúdo de teste."
    assert result["metadata"]["extractor"] == "plain_text"
    assert result["metadata"]["extension"] == ".md"


def test_extract_markdown_long_extension_file(tmp_path):
    path = tmp_path / "manual.markdown"
    path.write_text("# Manual\n\nConteúdo de teste.", encoding="utf-8")

    result = ChatAttachmentTextExtractor().extract(
        storage_path=str(path),
        filename="manual.markdown",
        content_type="text/markdown",
    )

    assert result["supported"] is True
    assert result["content"] == "# Manual\n\nConteúdo de teste."
    assert result["metadata"]["extractor"] == "plain_text"
    assert result["metadata"]["extension"] == ".markdown"


def test_extract_txt_file(tmp_path):
    path = tmp_path / "notas.txt"
    path.write_text("Notas de teste.", encoding="utf-8")

    result = ChatAttachmentTextExtractor().extract(
        storage_path=str(path),
        filename="notas.txt",
        content_type="text/plain",
    )

    assert result["supported"] is True
    assert result["content"] == "Notas de teste."
    assert result["metadata"]["extractor"] == "plain_text"
    assert result["metadata"]["extension"] == ".txt"
