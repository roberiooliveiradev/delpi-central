from app.domain.services.chat_drawing_bom_comparison_service import (
    ChatDrawingBomComparisonService,
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
    assert "40091640" in result.extra_in_pdf
    assert "10091640" in result.missing_in_pdf
    assert "1013091" in result.extra_in_pdf
    assert "10130091" in result.missing_in_pdf


def test_intermediate_codes_matched_by_description_fill_missing_ocr():
    root = {
        "structure": {
            "items": [
                {
                    "code": "50233301",
                    "description": "CB20AZUL-00240/11/06",
                    "components": [],
                },
                {
                    "code": "50233302",
                    "description": "CB20BRAN-00240/11/06",
                    "components": [],
                },
            ]
        }
    }
    pdf_extract = {
        "componentCodes": ["50233301"],
        "intermediateCodes": ["50233301"],
        "fullText": "BOM CB20BRAN-00240/11/06 e CB20AZUL-00240/11/06",
    }

    result = ChatDrawingBomComparisonService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90263396",
    )

    assert "50233302" not in result.missing_in_pdf
    assert "50233301" not in result.missing_in_pdf


def test_structured_bom_rows_ignore_noisy_component_codes():
    root = {
        "structure": {
            "items": [
                {"code": "10080010", "quantity": 1.0, "components": []},
                {"code": "10090050", "quantity": 1.0, "components": []},
                {"code": "50212969", "quantity": 1.0, "components": []},
            ]
        }
    }
    pdf_extract = {
        "componentCodes": [
            "10080010",
            "10090050",
            "50212969",
            "10020028",
            "10020029",
            "50232599",
        ],
        "bomRows": [
            {
                "code": "10080010",
                "quantity": "1",
                "quantitySource": "column",
                "quantityTrusted": True,
            },
            {
                "code": "10090050",
                "quantity": "1",
                "quantitySource": "refined_column",
                "quantityTrusted": True,
            },
            {
                "code": "50212969",
                "quantity": "1",
                "quantitySource": "column_inferred",
                "quantityTrusted": True,
            },
        ],
        "bomVisionRefinement": {"columnRowCount": 3},
    }

    result = ChatDrawingBomComparisonService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90263149",
    )

    assert "10020028" not in result.extra_in_pdf
    assert "10020029" not in result.extra_in_pdf
    assert not result.extra_in_pdf


def test_structured_bom_rows_skip_untrusted_row_codes():
    root = {
        "structure": {
            "items": [
                {"code": "10080010", "quantity": 1.0, "components": []},
            ]
        }
    }
    pdf_extract = {
        "componentCodes": ["10080010", "10080106"],
        "bomRows": [
            {
                "code": "10080010",
                "quantity": "1",
                "quantitySource": "column",
                "quantityTrusted": True,
            },
            {
                "code": "10080106",
                "quantity": "1",
                "quantitySource": "column_inferred",
                "quantityTrusted": False,
            },
        ],
        "bomVisionRefinement": {"columnRowCount": 2},
    }

    result = ChatDrawingBomComparisonService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90263149",
    )

    assert "10080106" not in result.extra_in_pdf


def test_structured_bom_supplements_presence_from_component_codes():
    root = {
        "structure": {
            "items": [
                {"code": "10080308", "quantity": 1.0, "components": []},
                {"code": "10130006", "quantity": 30.0, "components": []},
            ]
        }
    }
    pdf_extract = {
        "componentCodes": ["10080308", "10130006"],
        "bomRows": [
            {
                "code": "10080308",
                "quantity": "1",
                "quantitySource": "column",
                "quantityTrusted": True,
            },
            {
                "code": "10130006",
                "quantity": "30",
                "quantitySource": "column_inferred",
                "quantityTrusted": False,
            },
        ],
        "bomVisionRefinement": {"columnRowCount": 2},
    }

    result = ChatDrawingBomComparisonService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90264243",
    )

    assert "10130006" not in result.missing_in_pdf
    assert not result.missing_in_pdf


def test_nested_mp_under_pi_not_extra_when_only_in_stamp_bom_table():
    root = {
        "structure": {
            "items": [
                {"code": "10120073", "quantity": 650.0, "components": []},
                {
                    "code": "50225426",
                    "description": "CA0,75VERM-00792/04/14-3800-0000",
                    "components": [
                        {"code": "10020006", "quantity": 792.0},
                        {"code": "10080138", "quantity": 1000.0},
                    ],
                },
            ]
        }
    }
    pdf_extract = {
        "componentCodes": ["10020006", "10080138", "10120073"],
        "bomRows": [{"code": "10020006"}, {"code": "10080138"}, {"code": "10120073"}],
        "validationScopes": {"bom": {"sourceKey": "stamp_bom_table", "available": True}},
    }

    result = ChatDrawingBomComparisonService.compare(
        root=root,
        pdf_extract=pdf_extract,
        product_code="90262008",
    )

    assert "10020006" not in result.extra_in_pdf
    assert "10080138" not in result.extra_in_pdf
