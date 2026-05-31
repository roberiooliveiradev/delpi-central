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
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
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


def test_extract_legacy_doc_returns_hint(tmp_path):
    path = tmp_path / "ata.doc"
    path.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")

    result = ChatAttachmentTextExtractor().extract(
        storage_path=str(path),
        filename="ata.doc",
        content_type="application/msword",
    )

    assert result["supported"] is False
    assert result["metadata"]["reason"] == "legacy_doc_format"
    assert "docx" in result["metadata"]["userHint"].lower()


def test_extract_legacy_xls_returns_hint(tmp_path):
    path = tmp_path / "planilha.xls"
    path.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")

    result = ChatAttachmentTextExtractor().extract(
        storage_path=str(path),
        filename="planilha.xls",
        content_type="application/vnd.ms-excel",
    )

    assert result["supported"] is False
    assert result["metadata"]["reason"] == "legacy_xls_format"
    assert "xlsx" in result["metadata"]["userHint"].lower()


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
