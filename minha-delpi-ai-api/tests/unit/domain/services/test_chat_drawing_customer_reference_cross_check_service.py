from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_drawing_customer_reference_cross_check_service import (
    ChatDrawingCustomerReferenceCrossCheckService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService
from app.domain.services.chat_drawing_stamp_extraction_service import (
    ChatDrawingStampExtractionService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)
from app.domain.services.chat_drawing_validation_rule_registry_service import (
    ChatDrawingValidationRuleRegistryService,
)

configure_domain_infrastructure_ports()

_STAMP_REF = (
    "CHICOTE DE LIGAÇÃO\n"
    "CLIENTE: WEG INDUSTRIAS S.A - MOTORES\n"
    "REF: 10432385\n"
    "90261823 REV: 00\n"
)


def test_stamp_extracts_ref_label_as_customer_code():
    extract = ChatDrawingStampExtractionService.extract(stamp_text=_STAMP_REF)

    assert extract.get("customerCode") == "10432385"


def test_customer_code_labeled_pattern_matches_ref():
    match = ChatDrawingPatternsService.customer_code_labeled().search(_STAMP_REF)

    assert match is not None
    assert match.group(1).strip() == "10432385"


def test_ocr_noise_after_ref_does_not_false_mismatch():
    """OCR cola 'CLIENTE'/'LIBERADO' na mesma linha do REF — não pode virar crítico."""
    noisy_cliente = "REF: 10432385 CLIENTE: WEG INDUSTRIAS"
    noisy_liberado = "COD. DESENHO 90261823 REF: 10432385 LIBERADO"

    for blob in (noisy_cliente, noisy_liberado):
        match = ChatDrawingPatternsService.customer_code_labeled().search(blob)
        assert match is not None, blob
        assert match.group(1).strip() == "10432385", blob

        extract = ChatDrawingStampExtractionService.extract(stamp_text=blob)
        assert extract.get("customerCode") == "10432385", blob

        item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
            pdf_reference=extract.get("customerCode") or match.group(1),
            api_reference="10432385",
        )
        assert item is not None
        assert item["templateKey"] == "customer_reference_ok", blob
        assert item["status"] == "ok"


def test_client_name_must_not_be_used_as_customer_reference():
    """Campo CLIENTE: (razão social) ≠ REF:/B1_REFEREN."""
    stamp = (
        "CHICOTE DE LIGAÇÃO\n"
        "CLIENTE: WEG INDUSTRIAS S.A - MOTORES\n"
        "REF: 10432385\n"
        "90261823 REV: 00\n"
    )
    confused = (
        "COD. CLIENTE: WEG INDUSTRIAS S.A - MOTORES\n"
        "REF: 10432385\n"
    )
    name_only = "CLIENTE: WEG INDUSTRIAS S.A - MOTORES\n90261823\n"

    for blob in (stamp, confused):
        extract = ChatDrawingStampExtractionService.extract(stamp_text=blob)
        assert extract.get("customerCode") == "10432385", blob

        item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
            pdf_reference=extract.get("customerCode") or "",
            api_reference="10432385",
        )
        assert item["templateKey"] == "customer_reference_ok", blob

    assert ChatDrawingStampExtractionService.extract(stamp_text=name_only).get(
        "customerCode"
    ) in (None, "")

    # Se o pipeline antigo gravasse o nome no PDF, não pode virar crítico.
    item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
        pdf_reference="WEG INDUSTRIAS S.A - MOTORES",
        api_reference="10432385",
    )
    assert item is not None
    assert item["templateKey"] == "customer_reference_pending_pdf"
    assert item["status"] == "pending"


def test_sanitize_raw_strips_trailing_stamp_words():
    assert (
        ChatDrawingCustomerReferenceCrossCheckService.sanitize_raw("10432385 CLIENTE")
        == "10432385"
    )
    assert (
        ChatDrawingCustomerReferenceCrossCheckService.sanitize_raw("10432385 LIBERADO")
        == "10432385"
    )
    assert (
        ChatDrawingCustomerReferenceCrossCheckService.normalize("10432385 CLIENTE")
        == "10432385"
    )


def test_spaced_customer_reference_still_normalizes():
    assert (
        ChatDrawingCustomerReferenceCrossCheckService.normalize("3E 4270 G02")
        == "3E4270G02"
    )
    item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
        pdf_reference="3E 4270 G02",
        api_reference="3E4270G02",
    )
    assert item is not None
    assert item["status"] == "ok"


def test_normalize_collapses_spaces_and_case():
    assert (
        ChatDrawingCustomerReferenceCrossCheckService.normalize("3E 4270 G02")
        == "3E4270G02"
    )


def test_customer_reference_ok_when_pdf_matches_api():
    item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
        pdf_reference="10432385",
        api_reference="10432385",
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_ok"
    assert item["status"] == "ok"


def test_customer_reference_mismatch_is_critical():
    item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
        pdf_reference="10432385",
        api_reference="99999999",
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_mismatch"
    assert item["status"] == "critical_error"


def test_customer_reference_pending_when_pdf_missing():
    item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
        pdf_reference="",
        api_reference="10432385",
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_pending_pdf"
    assert item["status"] == "pending"


def test_customer_reference_pending_when_api_missing():
    item = ChatDrawingCustomerReferenceCrossCheckService.build_check_item(
        pdf_reference="10432385",
        api_reference="",
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_pending_api"
    assert item["status"] == "pending"


def test_rule_registry_enables_customer_reference_cross_check():
    assert ChatDrawingValidationRuleRegistryService.is_enabled(
        "customer_reference_cross_check",
        "90261823",
        group_code="9026",
    )


def test_api_anchored_finds_ref_despite_client_name_noise():
    """Ancora em B1_REFEREN e acha o mesmo valor no PDF (REF:/COD:), ignorando CLIENTE:."""
    pdf_extract = {
        "customerReference": "WEG INDUSTRIAS S.A - MOTORES",
        "fullText": (
            "CLIENTE: WEG INDUSTRIAS S.A - MOTORES\n"
            "REF: 10432385\n"
            "90261823 REV: 00\n"
        ),
        "legible": True,
    }
    product = {"customer_reference": "10432385"}

    item = ChatDrawingCustomerReferenceCrossCheckService.build_from_sources(
        product=product,
        pdf_extract=pdf_extract,
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_ok"
    assert item["status"] == "ok"
    assert "10432385" in str(item.get("pdfEvidence") or item.get("pdf_evidence") or "")


def test_api_anchored_accepts_cod_label():
    pdf_extract = {
        "fullText": "COD: 10432385\nCLIENTE: WEG INDUSTRIAS S.A - MOTORES\n",
        "legible": True,
    }
    item = ChatDrawingCustomerReferenceCrossCheckService.build_from_sources(
        product={"customer_reference": "10432385"},
        pdf_extract=pdf_extract,
    )

    assert item is not None
    assert item["status"] == "ok"


def test_api_anchored_spaced_ocr_token():
    pdf_extract = {
        "fullText": "REF: 1 0 4 3 2 3 8 5\n90261823\n",
        "legible": True,
    }
    found = ChatDrawingCustomerReferenceCrossCheckService.find_reference_in_text(
        "10432385",
        pdf_extract["fullText"],
    )

    assert found == "10432385"

    item = ChatDrawingCustomerReferenceCrossCheckService.build_from_sources(
        product={"customer_reference": "10432385"},
        pdf_extract=pdf_extract,
    )
    assert item is not None
    assert item["status"] == "ok"


def test_description_noise_cabo_para_not_plausible_reference():
    """Ruído de descrição no carimbo (COD: CABO PARA 1002) ≠ REF do cliente."""
    assert not ChatDrawingCustomerReferenceCrossCheckService.is_plausible_reference(
        "CABO PARA 1002"
    )
    assert (
        ChatDrawingCustomerReferenceCrossCheckService.coerce_reference("CABO PARA 1002")
        == ""
    )


def test_cabo_para_noise_without_fulltext_is_pending_not_critical():
    """Sem haystack completo, extract sujo não pode reprovar por mismatch."""
    item = ChatDrawingCustomerReferenceCrossCheckService.build_from_sources(
        product={"customer_reference": "10432385"},
        pdf_extract={"customerReference": "CABO PARA 1002", "legible": True},
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_pending_pdf"
    assert item["status"] == "pending"


def test_cabo_para_noise_with_ref_in_fulltext_is_ok():
    pdf_extract = {
        "customerReference": "CABO PARA 1002",
        "fullText": (
            "CLIENTE: WEG INDUSTRIAS S.A - MOTORES\n"
            "REF: 10432385\n"
            "COD: CABO PARA 1002\n"
            "90261823 REV: 00\n"
        ),
        "legible": True,
    }
    item = ChatDrawingCustomerReferenceCrossCheckService.build_from_sources(
        product={"customer_reference": "10432385"},
        pdf_extract=pdf_extract,
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_ok"
    assert item["status"] == "ok"


def test_extract_from_text_skips_cabo_para_prefers_digit_ref():
    blob = "COD: CABO PARA 1002\nREF: 10432385\n"
    extracted = ChatDrawingCustomerReferenceCrossCheckService.extract_from_text(blob)

    assert extracted == "10432385"


def test_api_anchored_mismatch_when_pdf_has_other_ref():
    pdf_extract = {
        "customerReference": "99999999",
        "fullText": "REF: 99999999\nCLIENTE: WEG\n",
        "legible": True,
    }
    item = ChatDrawingCustomerReferenceCrossCheckService.build_from_sources(
        product={"customer_reference": "10432385"},
        pdf_extract=pdf_extract,
    )

    assert item is not None
    assert item["templateKey"] == "customer_reference_mismatch"
    assert item["status"] == "critical_error"


def test_orchestration_includes_customer_reference_item():
    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code="90261823",
        payload={
            "product": {
                "code": "90261823",
                "customer_reference": "10432385",
                "current_revision": "004",
            },
            "structure": {"items": []},
            "guide": {"items": []},
            "inspection": {"items": []},
        },
        has_pdf_attachment=True,
        api_ok=True,
        pdf_extract={
            "productCode": "90261823",
            "revision": "00",
            "customerReference": "WEG INDUSTRIAS S.A - MOTORES",
            "fullText": _STAMP_REF,
            "legible": True,
        },
    )
    items = [
        item
        for item in package["drawingAnalysis"]["items"]
        if str(item.get("templateKey") or "").startswith("customer_reference_")
    ]

    assert items
    assert items[0]["templateKey"] == "customer_reference_ok"
    assert package["drawingAnalysis"]["customerReferencePdf"] == "10432385"
    assert package["drawingAnalysis"]["customerReferenceApi"] == "10432385"
