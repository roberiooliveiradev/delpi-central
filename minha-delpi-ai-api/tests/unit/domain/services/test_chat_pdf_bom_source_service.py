from app.domain.services.chat_pdf_bom_source_service import ChatPdfBomSourceService


def test_build_sources_orders_structured_before_full_text():
    sources = ChatPdfBomSourceService.build_sources(
        full_text="RESUMO DAS MODIFICACOES",
        metadata={
            "bomText": "10080627",
            "stampText": "90263489",
            "annotationText": "A",
        },
    )

    assert [name for name, _ in sources] == [
        "bom_region",
        "pdf_annotations",
        "stamp_region",
        "full_text",
    ]
