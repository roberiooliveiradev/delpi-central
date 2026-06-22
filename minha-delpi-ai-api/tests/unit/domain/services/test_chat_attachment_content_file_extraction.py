from app.domain.services.chat_attachment_content_service import ChatAttachmentContentService


def test_file_extraction_limits_from_json():
    assert ChatAttachmentContentService.file_extraction_csv_max_rows() == 300
    assert ChatAttachmentContentService.file_extraction_xlsx_max_sheets() == 10
    assert ChatAttachmentContentService.file_extraction_xlsx_max_rows_per_sheet() == 300
    assert ChatAttachmentContentService.file_extraction_subprocess_timeout_seconds() == 30


def test_file_extraction_legacy_doc_hint():
    legacy = ChatAttachmentContentService.file_extraction_legacy_format(".doc")

    assert legacy["reason"] == "legacy_doc_format"
    assert "docx" in legacy["userHint"].lower()
