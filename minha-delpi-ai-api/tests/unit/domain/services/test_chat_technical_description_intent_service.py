from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_technical_description_intent_service import (
    ChatTechnicalDescriptionIntentService,
)


def test_requires_normas_for_terminal_guidance():
    assert ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "como descrever um terminal?"
    )


def test_requires_normas_for_field_meaning():
    assert ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "o que significa o campo material na descrição técnica?"
    )


def test_requires_normas_for_normas_marker():
    assert ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "normas técnicas DELPI para cabos"
    )


def test_does_not_require_normas_for_product_lookup():
    assert not ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "qual a descrição do produto 10080047"
    )


def test_does_not_require_normas_for_catalog_search():
    assert not ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "busque parafuso m8"
    )


def test_build_rag_query_includes_terminal_group():
    query = ChatTechnicalDescriptionIntentService.build_rag_query("como descrever um terminal?")
    assert "1008" in query
    assert "terminais" in query
    assert "Normas_Tecnicas_DELPI" in query


def test_product_intent_not_description_for_normas_guidance():
    assert (
        ChatProductQueryIntentService.detect("como descrever um terminal?")
        != ChatProductQueryIntent.DESCRIPTION
    )


def test_resolve_material_group_terminal():
    group = ChatTechnicalDescriptionIntentService.resolve_material_group("terminal pino 4mm")
    assert group is not None
    assert group[0] == "1008"
