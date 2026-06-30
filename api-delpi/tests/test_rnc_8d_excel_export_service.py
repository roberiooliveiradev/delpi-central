from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from app.domain.services.quality_action_plans.rnc_8d_excel_export_service import (
    build_rnc_8d_workbook,
    is_image_evidence,
    resolve_rnc_8d_template_path,
)

_TEMPLATE_PATH = resolve_rnc_8d_template_path()


def _minimal_png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color=(200, 40, 40)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_is_image_evidence_detects_mime_and_type():
    assert is_image_evidence({"mime_type": "image/png", "type": "other"})
    assert is_image_evidence({"type": "image"})
    assert not is_image_evidence({"mime_type": "application/pdf", "type": "pdf"})


@pytest.mark.skipif(not _TEMPLATE_PATH.is_file(), reason="Template 8D ausente")
def test_build_rnc_8d_workbook_fills_registry_cell():
    detail = {
        "plan": {
            "client_nc_registry": "215571003",
            "customer_name": "Cliente industrial",
            "product_code": "14297268",
            "product_description": "CHICOTE 3 SILICONE 150mm",
            "batch_number": "90262776",
            "branch_code": "01",
            "template_payload": {
                "purchase_order": "5500044658 / 09770",
                "invoice_number": "000092387-1",
                "client_batch": "10019632175",
                "disposition": "Rejeitado",
            },
        },
        "five_whys": {
            "occurrence_whys": ["Falha na impressão"],
        },
        "team_members": [
            {"member_name": "Rodrigo J. Cozer", "department": "Qualidade", "is_leader": True},
        ],
        "actions": [],
    }

    content = build_rnc_8d_workbook(detail)
    assert isinstance(content, bytes)
    assert len(content) > 10_000

    from openpyxl import load_workbook
    import io

    wb = load_workbook(io.BytesIO(content), data_only=True)
    ws = wb["R8D"]
    assert ws["I4"].value == "215571003"
    assert "14297268" in str(ws["E6"].value)
    assert ws["J8"].value == "10019632175"


@pytest.mark.skipif(not _TEMPLATE_PATH.is_file(), reason="Template 8D ausente")
def test_build_rnc_8d_workbook_embeds_annex_images():
    detail = {
        "plan": {"client_nc_registry": "215571003", "branch_code": "01", "template_payload": {}},
        "team_members": [],
        "actions": [],
    }
    content = build_rnc_8d_workbook(
        detail,
        image_annexes=[
            {
                "file_name": "foto-nc.png",
                "description": "Evidência da não conformidade",
                "content": _minimal_png_bytes(),
            }
        ],
    )
    from openpyxl import load_workbook

    wb = load_workbook(io.BytesIO(content))
    assert "Anexos(Evidencias)" in wb.sheetnames
    annex = wb["Anexos(Evidencias)"]
    assert annex["D3"].value == "foto-nc.png"
    assert len(annex._images) >= 1
