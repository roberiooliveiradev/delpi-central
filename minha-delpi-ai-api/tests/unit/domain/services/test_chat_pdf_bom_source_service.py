from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_pdf_bom_source_service import ChatPdfBomSourceService

configure_domain_infrastructure_ports()


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


def test_build_sources_supplements_full_text_when_bom_region_is_partial():
    partial_bom = "QTD. | CÓDIGO | DESCRIÇÃO\nA | 01 | 10250032 | TERMISTOR"
    full_text = (
        "QTD. | CÓDIGO | DESCRIÇÃO\n"
        "A | 01 | 10250032 | TERMISTOR\n"
        "B | 01 | 10080591 | TERM. PINO\n"
        "C | 01 | 10090481 | CONECTOR"
    )

    sources = ChatPdfBomSourceService.build_sources(
        full_text=full_text,
        metadata={
            "validationScopes": {
                "bom": {
                    "sourceKey": "bom_region",
                    "text": partial_bom,
                    "available": True,
                }
            },
            "regionTexts": {"bom": partial_bom},
        },
        product_code="90262019",
    )

    assert sources[0][0] == "bom_region"
    assert any(name == "full_text_section" for name, _ in sources)
