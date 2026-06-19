from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
)
from app.domain.services.chat_drawing_component_code_normalization_service import (
    ChatDrawingComponentCodeNormalizationService,
)


def _payload_90264227() -> dict:
    return {
        "structure": {
            "items": [
                {"code": "10081867", "quantity": 2000.0, "components": []},
                {"code": "10091640", "quantity": 1000.0, "components": []},
                {"code": "10130091", "quantity": 16.0, "components": []},
                {"code": "10140027", "quantity": 0.6, "components": []},
                {
                    "code": "50215425",
                    "description": "CT26VERM-00036/04/06-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10440133", "quantity": 36.0}],
                },
                {
                    "code": "50215426",
                    "description": "CT26PRET-000062/04/06-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10440134", "quantity": 62.0}],
                },
                {
                    "code": "50215433",
                    "description": "CT26PRET-00050/2,5/06-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10440134", "quantity": 50.0}],
                },
                {
                    "code": "50215434",
                    "description": "CT26VERM-00040/2,5/06-0000-0000",
                    "quantity": 1.0,
                    "components": [{"code": "10440133", "quantity": 40.0}],
                },
            ]
        },
        "guide": {
            "items": [
                {
                    "product_code": "50225933",
                    "bom_level": 1,
                    "work_center": "CT-01A",
                }
            ]
        },
    }


def test_reconcile_ocr_component_codes():
    known = {"10091640", "10130091"}

    assert (
        ChatDrawingComponentCodeNormalizationService.reconcile_with_known(
            "40091640", known
        )
        == "10091640"
    )
    assert (
        ChatDrawingComponentCodeNormalizationService.reconcile_with_known(
            "1013091", known
        )
        == "10130091"
    )


def test_child_cable_codes_not_counted_as_extra_when_parent_present():
    root = _payload_90264227()
    pdf_extract = {
        "componentCodes": [
            "10081867",
            "40091640",
            "1013091",
            "10140027",
            "50215425",
            "10440133",
            "50215426",
            "10440134",
            "50215433",
        ],
        "intermediateCodes": ["50215425", "50215426", "50215433"],
    }

    result = ChatDrawingBomComparisonService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90264227",
    )

    assert "10440133" not in result.extra_in_pdf
    assert "10440134" not in result.extra_in_pdf
    assert "50215434" in result.missing_in_pdf
    assert "50225933" not in result.missing_in_pdf
    assert "10091640" not in result.missing_in_pdf
    assert "10130091" not in result.missing_in_pdf
