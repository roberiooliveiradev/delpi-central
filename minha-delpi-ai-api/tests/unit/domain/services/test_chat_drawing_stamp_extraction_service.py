from app.domain.services.chat_drawing_stamp_extraction_service import (
    ChatDrawingStampExtractionService,
)


def test_labeled_stamp_extracts_product_code():
    extract = ChatDrawingStampExtractionService.extract(
        stamp_text="CÓDIGO DELPI 90264234\nREV. 01\nCLIENTE WEG",
    )

    assert extract["productCode"] == "90264234"
    assert extract["productCodeSource"] == "stamp_labeled"


def test_customer_cod_des_not_promoted_to_product_code():
    extract = ChatDrawingStampExtractionService.extract(
        stamp_text=(
            "CÓDIGO DELPI 90264234\n"
            "COD: 19402706\n"
            "DES: 10014608724\n"
            "REV. 01"
        ),
    )

    assert extract["productCode"] == "90264234"
    assert extract.get("customerCode") == "19402706"


def test_title_pattern_chicote_de_ligacao():
    extract = ChatDrawingStampExtractionService.extract(
        title_text="CHICOTE DE LIGAÇÃO90264236 COD:DES:REV:00",
    )

    assert extract["productCode"] == "90264236"
    assert extract["productCodeSource"] == "title_pattern"


def test_title_pattern_ocr_spaced_code():
    extract = ChatDrawingStampExtractionService.extract(
        title_text="CHICOTE DE LIGAÇÃO / 902642 36",
    )

    assert extract["productCode"] == "90264236"


def test_intermediate_50xx_in_separate_list():
    extract = ChatDrawingStampExtractionService.extract(
        stamp_text="CÓDIGO DELPI 50232222\nREV. 01",
    )

    assert extract["productCode"] == "50232222"
    assert "50232222" in extract["intermediateCodes"]


def test_stamp_vs_message_conflict():
    extract = ChatDrawingStampExtractionService.extract(
        stamp_text="CÓDIGO DELPI 90264234",
        message_code="90261040",
    )

    assert extract["productCode"] == "90261040"
    assert extract["productCodeSource"] == "user_message"
    assert any(item["type"] == "stamp_vs_message" for item in extract["conflicts"])


def test_build_title_block_from_extract():
    extract = ChatDrawingStampExtractionService.extract(
        stamp_text="CÓDIGO DELPI 90260140\nREV. 03",
    )
    block = ChatDrawingStampExtractionService.build_title_block(
        extract,
        raw_text="CÓDIGO DELPI 90260140",
    )

    assert block is not None
    assert block["fields"]["code"] == "90260140"
    assert block["fields"]["rev"] == "03"
    assert block["bbox"][1] >= 0.5
