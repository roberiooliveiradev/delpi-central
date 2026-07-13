from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_technical_description_intent_service import (
    ChatTechnicalDescriptionIntentService,
)
from app.domain.services.chat_technical_description_vocabulary_service import (
    ChatTechnicalDescriptionVocabularyService,
)

configure_domain_infrastructure_ports()


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
    query = ChatTechnicalDescriptionIntentService.build_rag_query(
        "como descrever um terminal?"
    )
    assert "1008" in query
    assert "terminais" in query
    assert "Normas_Tecnicas_DELPI" in query


def test_product_intent_not_description_for_normas_guidance():
    assert (
        ChatProductQueryIntentService.detect("como descrever um terminal?")
        != ChatProductQueryIntent.DESCRIPTION
    )


def test_resolve_material_group_terminal():
    group = ChatTechnicalDescriptionIntentService.resolve_material_group(
        "terminal pino 4mm"
    )
    assert group is not None
    assert group[0] == "1008"


def test_resolve_material_group_cabo_pp():
    group = ChatTechnicalDescriptionIntentService.resolve_material_group(
        "como descrever cabo pp circular"
    )
    assert group is not None
    assert group[0] == "1007"
    assert "pp" in group[1].lower()


def test_resolve_material_group_bandeira():
    group = ChatTechnicalDescriptionIntentService.resolve_material_group(
        "terminal bandeira 90 graus"
    )
    assert group is not None
    assert group[0] == "1008"


def test_resolve_material_group_anilha():
    group = ChatTechnicalDescriptionIntentService.resolve_material_group("anilha pvc ye")
    assert group is not None
    assert group[0] == "1011"


def test_requires_normas_for_color_abbreviation_meaning():
    assert ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "o que significa VDAR"
    )


def test_requires_normas_for_analyze_description():
    assert ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "analise esta descricao: TERM. FASTON 6,30X0,80 ESTANHADO"
    )


def test_requires_normas_for_create_description():
    assert ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "monte a descricao de um cabo pvc 0,75mm2 preto"
    )


def test_resolve_color_abbreviation_vdar():
    assert (
        ChatTechnicalDescriptionIntentService.resolve_color_abbreviation("VDAR")
        == "Verde-Amarelo"
    )
    assert (
        ChatTechnicalDescriptionVocabularyService.resolve_color_abbreviation("pt")
        == "Preto"
    )


def test_build_rag_query_includes_color_abbreviation():
    query = ChatTechnicalDescriptionIntentService.build_rag_query(
        "o que significa VDAR na descrição técnica?"
    )
    assert "VDAR" in query.upper()
    assert "Verde-Amarelo" in query


def test_vocabulary_material_groups_and_colors_loaded():
    groups = ChatTechnicalDescriptionVocabularyService.material_groups()
    colors = ChatTechnicalDescriptionVocabularyService.color_abbreviations()

    assert groups
    assert any(group["groupCode"] == "1008" for group in groups)
    assert any(group["groupCode"] == "50xx" for group in groups)
    assert "VDAR" in colors
    assert "PT" in colors
    assert "PRET" in colors
    assert "VERD" in colors
    assert ChatTechnicalDescriptionVocabularyService.rag_query_seeds()
    assert ChatTechnicalDescriptionVocabularyService.intermediate_rag_query_seeds()
    assert (
        ChatTechnicalDescriptionVocabularyService.resolve_insulation_code("CB") == "EPR"
    )


def test_requires_normas_for_intermediate_code_explanation():
    assert ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "explique o código intermediário 50232222 CB1,50VERD-00255/06/06–6314–0111"
    )


def test_requires_normas_for_intermediate_how_to_build():
    assert ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "como montar um código intermediário família 5023"
    )


def test_does_not_require_normas_for_intermediate_product_lookup():
    assert not ChatTechnicalDescriptionIntentService.requires_normas_knowledge(
        "qual a descrição do produto 50232222"
    )


def test_resolve_material_group_intermediate():
    group = ChatTechnicalDescriptionIntentService.resolve_material_group(
        "codigo intermediario 5023"
    )
    assert group is not None
    assert group[0] in {"50xx", "5023"}
    assert "intermedi" in group[1].lower()


def test_resolve_color_abbreviation_intermediate_four_letters():
    assert (
        ChatTechnicalDescriptionIntentService.resolve_color_abbreviation("PRET")
        == "Preto"
    )
    assert (
        ChatTechnicalDescriptionIntentService.resolve_color_abbreviation("VERD")
        == "Verde"
    )


def test_build_rag_query_includes_intermediate_seeds():
    query = ChatTechnicalDescriptionIntentService.build_rag_query(
        "explique o código intermediário CB1,50VERD"
    )
    assert "50xx" in query or "intermediário" in query.lower() or "Intermediate" in query
    assert "CB" in query.upper()
