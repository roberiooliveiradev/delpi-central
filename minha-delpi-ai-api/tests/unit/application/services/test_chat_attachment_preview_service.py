from app.application.services.chat_attachment_preview_service import (
    ChatAttachmentPreviewService,
)
from app.application.services.chat_attachment_welcome_service import (
    ChatAttachmentWelcomeService,
)


def test_build_preview_spreadsheet_columns():
    extracted = {
        "supported": True,
        "content": "# Planilha: Vendas\nProduto | Descrição | Quantidade\nA1 | Item | 10",
        "metadata": {"extractor": "openpyxl", "extension": ".xlsx"},
    }

    preview = ChatAttachmentPreviewService.build_from_extracted(
        extracted,
        filename="dados.xlsx",
    )

    assert preview["kind"] == "spreadsheet"
    assert preview["columns"] == ["Produto", "Descrição", "Quantidade"]
    assert preview["sheetTitle"] == "Vendas"


def test_welcome_includes_column_preview():
    answer = ChatAttachmentWelcomeService.build_direct_answer(
        attachments=[
            {
                "original_filename": "dados.csv",
                "status": "indexed",
                "metadata": {
                    "indexed": True,
                    "preview": {
                        "kind": "spreadsheet",
                        "columns": ["Produto", "Valor"],
                    },
                },
            }
        ],
    )

    assert answer
    assert "Colunas:" in answer
    assert "Produto" in answer
