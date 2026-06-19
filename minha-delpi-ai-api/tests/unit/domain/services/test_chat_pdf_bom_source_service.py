from app.domain.services.chat_pdf_bom_source_service import ChatPdfBomSourceService


def test_build_sources_uses_regional_bom_scope_only():
    sources = ChatPdfBomSourceService.build_sources(
        full_text="RESUMO DAS MODIFICACOES",
        metadata={
            "bomText": "10080627",
            "stampText": "90263489",
            "annotationText": "A",
            "regionTexts": {"bom": "10080627"},
        },
    )

    assert [name for name, _ in sources] == ["bom_region"]
    assert "stamp_region" not in [name for name, _ in sources]
