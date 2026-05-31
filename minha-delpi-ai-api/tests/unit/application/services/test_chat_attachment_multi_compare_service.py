from app.application.services.chat_attachment_multi_compare_service import (
    ChatAttachmentMultiCompareService,
)


def _spreadsheet_attachment(name: str, columns: list[str]) -> dict:
    return {
        "original_filename": name,
        "status": "indexed",
        "metadata": {
            "indexed": True,
            "preview": {
                "kind": "spreadsheet",
                "columns": columns,
            },
        },
    }


def test_build_context_hint_with_two_spreadsheets():
    attachments = [
        _spreadsheet_attachment("a.csv", ["Produto", "Qtd"]),
        _spreadsheet_attachment("b.csv", ["Item", "Valor"]),
    ]

    hint = ChatAttachmentMultiCompareService.build_context_hint(
        message="compare as duas planilhas",
        attachments=attachments,
    )

    assert hint
    assert "a.csv" in hint
    assert "b.csv" in hint
    assert "Produto" in hint


def test_should_not_hint_single_attachment_without_compare():
    hint = ChatAttachmentMultiCompareService.build_context_hint(
        message="resuma o arquivo",
        attachments=[_spreadsheet_attachment("a.csv", ["A"])],
    )

    assert hint is None
