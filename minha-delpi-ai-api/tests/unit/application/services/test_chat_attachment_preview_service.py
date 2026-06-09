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


def test_reading_status_index_failed_with_legible_document_vision():
    label = ChatAttachmentPreviewService.reading_status_label(
        status="index_failed",
        parsed=False,
        metadata={
            "documentVision": {
                "engine": "tesseract",
                "legible": True,
            },
        },
    )

    assert label == "Legível por visão (tesseract)"


def test_enrich_message_attachment_snapshots_includes_vision_readable_status():
    snapshots = ChatAttachmentPreviewService.enrich_message_attachment_snapshots(
        [
            {
                "id": "att-1",
                "original_filename": "desenho.pdf",
                "status": "index_failed",
                "metadata": {
                    "documentVision": {
                        "engine": "native",
                        "legible": True,
                    },
                },
            }
        ],
    )

    assert snapshots[0]["readingStatus"] == "Legível por visão (native)"


def test_merge_tool_context_vision_into_attachments_uses_drawing_summary():
    merged = ChatAttachmentPreviewService.merge_tool_context_vision_into_attachments(
        [
            {
                "id": "att-1",
                "status": "index_failed",
                "metadata": {},
            }
        ],
        {
            "drawingPdfExtractSummary": {
                "legible": True,
                "documentVision": {
                    "engine": "tesseract",
                    "stages": ["tesseract_pdf"],
                },
            }
        },
    )

    vision = merged[0]["metadata"]["documentVision"]

    assert vision["engine"] == "tesseract"
    assert vision["legible"] is True
