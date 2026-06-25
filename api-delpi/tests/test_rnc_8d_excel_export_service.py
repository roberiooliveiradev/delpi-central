from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.services.quality_action_plans.rnc_8d_excel_export_service import (
    TEMPLATE_PATH,
    build_rnc_8d_workbook,
)


@pytest.mark.skipif(not TEMPLATE_PATH.is_file(), reason="Template 8D ausente")
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
            "why_1": "Falha na impressão",
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
