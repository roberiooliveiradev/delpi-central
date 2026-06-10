from app.domain.services.chat_presentation_story_service import (
    ChatPresentationStoryService,
)


def test_build_story_from_data_answer_metadata():
    metadata = {
        "path": "/products/90269001/stock",
        "dataAnswer": {
            "profileKey": "stock",
            "summary": {
                "answer": "Saldo confortável em duas filiais.",
                "meaning": "não há ruptura aparente",
                "riskLevel": "ok",
                "nextAction": "Conferir posição com disponível negativo.",
                "attention": ["Uma posição com empenho acima do físico."],
            },
            "facts": [{"text": "Total disponível: **150** un."}],
            "analysis": ["Concentração em Fil.01."],
            "recommendations": [
                {
                    "label": "Ver concentração por filial",
                    "query": "Mostrar concentração de estoque por filial",
                    "reason": "Priorizar onde o saldo está",
                }
            ],
            "limitations": ["Esta análise considera apenas os registros desta página."],
        },
        "textPresentation": {
            "markdown": "### Estoque do produto — 90269001\n\nResumo.",
        },
    }

    assert ChatPresentationStoryService.enrich_metadata(metadata) is True

    story = metadata.get("storyPresentation")

    assert isinstance(story, dict)
    assert story["type"] == "story"
    assert story["title"] == "Estoque do produto — 90269001"
    assert story["blocks"][0]["kind"] == "verdict"
    assert story["blocks"][0]["status"] == "ok"
    assert any(block.get("kind") == "recommendation" and block.get("query") for block in story["blocks"])
    assert not any(block.get("kind") == "limitation" for block in story["blocks"])


def test_analysis_blocks_extract_text_from_dict_items():
    metadata = {
        "dataAnswer": {
            "profileKey": "production_status",
            "summary": {
                "answer": "Produção **em andamento** na OP principal.",
                "riskLevel": "attention",
            },
            "analysis": [
                {"text": "Produção **em andamento** com apontamento parcial."},
                "Linha já em texto.",
            ],
        },
    }

    story = ChatPresentationStoryService.build_from_metadata(metadata)

    assert isinstance(story, dict)

    analysis_blocks = [
        block
        for block in story["blocks"]
        if block.get("kind") == "analysis"
    ]

    assert analysis_blocks
    assert all("{'text':" not in block.get("text", "") for block in analysis_blocks)
    assert analysis_blocks[0]["text"] == "Produção **em andamento** com apontamento parcial."


def test_story_skips_duplicate_facts_already_in_verdict():
    metadata = {
        "dataAnswer": {
            "profileKey": "factory_status",
            "summary": {
                "answer": "Status fabril: OP aberta.",
                "meaning": "ainda sem apontamento",
                "riskLevel": "attention",
            },
            "facts": [
                {"text": "Status fabril: OP aberta."},
                {"text": "305 OPs abertas no período."},
            ],
        },
    }

    story = ChatPresentationStoryService.build_from_metadata(metadata)
    fact_texts = [
        block.get("text")
        for block in story["blocks"]
        if block.get("kind") == "fact"
    ]

    assert "Status fabril: OP aberta." not in fact_texts
    assert "305 OPs abertas no período." in fact_texts


def test_story_skips_recommendation_duplicated_as_next_action():
    metadata = {
        "dataAnswer": {
            "profileKey": "factory_status",
            "summary": {
                "answer": "Situação fabril estável.",
                "riskLevel": "ok",
                "nextAction": "Ver saldo detalhado das MPs com cobertura baixa",
            },
            "recommendations": [
                {
                    "label": "Ver saldo detalhado das MPs com cobertura baixa",
                    "query": "Ver saldo detalhado das MPs com cobertura baixa",
                },
                {
                    "label": "Listar OPs abertas sem apontamento",
                    "query": "Listar OPs abertas sem apontamento",
                },
            ],
        },
    }

    story = ChatPresentationStoryService.build_from_metadata(metadata)
    recommendation_texts = [
        block.get("text")
        for block in story["blocks"]
        if block.get("kind") == "recommendation"
    ]

    assert recommendation_texts.count("Ver saldo detalhado das MPs com cobertura baixa") == 1


def test_enrich_metadata_strips_destaques_from_text_presentation():
    metadata = {
        "dataAnswer": {
            "profileKey": "factory_status",
            "summary": {
                "answer": "Situação fabril consolidada.",
                "riskLevel": "ok",
            },
        },
        "textPresentation": {
            "markdown": (
                "### Status fabril\n\n"
                "Produção: PA **Sim**.\n\n"
                "**Destaques**\n\n"
                "- Situação fabril consolidada.\n"
            ),
        },
    }

    assert ChatPresentationStoryService.enrich_metadata(metadata) is True

    markdown = metadata["textPresentation"]["markdown"]

    assert "**Destaques**" not in markdown
    assert "Produção: PA **Sim**." in markdown


def test_skips_story_when_data_answer_missing():
    metadata = {"path": "/products/90269001/stock"}

    assert ChatPresentationStoryService.enrich_metadata(metadata) is False
    assert "storyPresentation" not in metadata
