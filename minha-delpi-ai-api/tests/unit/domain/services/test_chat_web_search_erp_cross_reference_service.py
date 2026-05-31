from app.domain.services.chat_web_search_erp_cross_reference_service import (
    ChatWebSearchErpCrossReferenceService,
)


def test_should_cross_reference_internal_product_mode():
    assert ChatWebSearchErpCrossReferenceService.should_cross_reference(
        internal_data={"product": {"code": "10080001", "description": "Motor"}},
        web_payload={
            "searchStatus": "success",
            "integrationMode": "internal_product",
        },
    )


def test_enrich_and_format_cross_reference_block():
    payload = {
        "searchStatus": "success",
        "integrationMode": "internal_product",
        "results": [
            {
                "title": "Manual WEG",
                "url": "https://www.weg.net/manual",
                "isOfficial": True,
            },
        ],
    }
    internal = {"code": "10080001", "description": "Motor trifásico", "brand": "WEG"}

    enriched = ChatWebSearchErpCrossReferenceService.enrich_payload(payload, internal)

    assert enriched is not None
    assert enriched["erpCrossReference"]["productCode"] == "10080001"

    block = ChatWebSearchErpCrossReferenceService.format_cross_reference_block(enriched)

    assert block is not None
    assert "Cruzamento ERP" in block
    assert "10080001" in block
    assert "weg.net" in block


def test_append_to_direct_answer_merges_sections():
    answer, payload = ChatWebSearchErpCrossReferenceService.append_to_direct_answer(
        direct_answer="## Estoque\nSaldo 10 un.",
        internal_data={"product": {"code": "10080001", "description": "Motor"}},
        web_payload={
            "searchStatus": "success",
            "integrationMode": "internal_product",
            "results": [{"title": "Datasheet", "url": "https://example.com/ds.pdf"}],
        },
    )

    assert answer is not None
    assert "Estoque" in answer
    assert "Cruzamento ERP" in answer
    assert payload is not None
    assert "erpCrossReference" in payload
