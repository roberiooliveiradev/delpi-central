from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

from app.domain.services.quality_action_plans.pac_evidence_text_extraction_service import (
    extract_evidence_text,
)


def _sample_xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "RNC"
    sheet["A1"] = "Cliente"
    sheet["B1"] = "WEG"
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_extract_evidence_text_from_xlsx() -> None:
    payload = extract_evidence_text(
        content=_sample_xlsx_bytes(),
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        file_name="RNC 217383667.xlsx",
    )

    assert payload["format"] == "spreadsheet"
    assert "WEG" in payload["text_content"]
    assert payload["extractable"] is True


def test_extract_evidence_text_from_plain_text() -> None:
    payload = extract_evidence_text(
        content=b"Relato da NC interna",
        mime_type="text/plain",
        file_name="relato.txt",
    )

    assert payload["format"] == "text"
    assert "Relato" in payload["text_content"]
